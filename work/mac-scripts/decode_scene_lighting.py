"""Decode authored scene lighting from Amalur region_bxml and space_bxml files.

Works from asset bytes alone: no save, game launch or loaded scene is needed.
Every field carries its source offset and an evidence status from STATUS below.
Unknown bytes stay reported as unmapped; nothing is filled with a guessed value.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct
import sys

SCHEMA = "open-amalur.scene-lighting.v1"
KEYS = ("Midnight", "Dawn", "Noon", "Dusk")
STATUS = {
    "asset_verified": "Offset and meaning verified byte-for-byte against shipped authored XML across the corpus",
    "native_confirmed": "Read by decompiled native code with the stated meaning",
    "shader_confirmed": "Consumed in disassembled shipped shader code",
    "hypothesis": "Consistent with evidence but not proven; do not treat as native-equivalent",
    "unmapped": "Bytes preserved; meaning unknown",
}

ROOT_REGION_KEY = 0x00
ROOT_SKY_ID = 0x08
ROOT_CUBES = 0xE8
ROOT_ENV = 0xF0
ROOT_DAY_DIVISION = 0xF8
ENV_RECORD_BYTES = 0x570
CUBE_ENTRY_BYTES = 0x30
CUBE_FACE_TEXELS = 64
SPACE_REGION_KEY = 0x48
SPACE_LIGHTS = 0x90
LIGHT_BYTES = 108

# (name, record offset, kind). "f": float per key at +4. "c": float4 per key at +16.
# "v3": float3 per key at +12. "id": uint per key at +4.
ENV_FIELDS = (
    ("fog_color", 0x240, "c"),
    ("fog_start", 0x280, "f"),
    ("fog_density", 0x290, "f"),
    ("post_bloom_scale", 0x2A0, "f"),
    ("post_bloom_cutoff", 0x2B0, "f"),
    ("post_brightness", 0x2C0, "f"),
    ("post_contrast", 0x2D0, "v3"),
    ("post_focal_distance", 0x300, "f"),
    ("post_focal_radius", 0x310, "f"),
    ("post_motion_blur", 0x320, "f"),
    ("bloom_exposure_level", 0x330, "f"),
    ("bloom_min_luminance", 0x340, "f"),
    ("bloom_max_luminance", 0x350, "f"),
    ("bloom_strength", 0x360, "f"),
    ("dof_near_fuzzy", 0x370, "f"),
    ("dof_near_sharp", 0x380, "f"),
    ("dof_far_fuzzy", 0x390, "f"),
    ("dof_far_sharp", 0x3A0, "f"),
    ("dof_max_fuzzy", 0x3B0, "f"),
    ("edge_motion_blur", 0x3C0, "f"),
    ("color_correction_texture_id", 0x3D0, "id"),
    ("directional_light_color", 0x3E0, "c"),
    ("directional_light_intensity", 0x420, "f"),
    ("shadow_color", 0x440, "c"),
    ("sky_light_color", 0x480, "c"),
    ("shadow_opacity", 0x4C0, "f"),
    ("particle_tint", 0x4D0, "c"),
    ("environment_tint", 0x510, "c"),
    ("ambient_cube_index", 0x550, "id"),
    ("character_ambient_cube_index", 0x560, "id"),
)
# Field names map to the renderer stage that consumes them; see lighting-provenance.json.
ENV_UNMAPPED = ((0x000, 0x240), (0x43C, 0x440))


class DecodeError(ValueError):
    pass


class Blob:
    """Amalur container: u32 payload bytes, u32 fixup bytes, payload, fixup slots."""

    def __init__(self, data):
        if len(data) < 8:
            raise DecodeError("truncated container header")
        self.payload_bytes, fixup_bytes = struct.unpack_from("<II", data, 0)
        if 8 + self.payload_bytes + fixup_bytes != len(data) or fixup_bytes % 4:
            raise DecodeError("container size does not match declared sections")
        self.payload = data[8:8 + self.payload_bytes]
        self.fixups = set(struct.unpack_from("<%dI" % (fixup_bytes // 4), data, 8 + self.payload_bytes))
        self.sha256 = hashlib.sha256(data).hexdigest()

    def u32(self, offset):
        if offset + 4 > self.payload_bytes:
            raise DecodeError("read beyond payload at 0x%x" % offset)
        return struct.unpack_from("<I", self.payload, offset)[0]

    def floats(self, offset, count):
        if offset + 4 * count > self.payload_bytes:
            raise DecodeError("read beyond payload at 0x%x" % offset)
        return struct.unpack_from("<%df" % count, self.payload, offset)

    def array(self, slot):
        """Return (payload offset, count) for a fixed-up pointer/count pair."""
        if slot not in self.fixups:
            raise DecodeError("slot 0x%x is not a registered pointer" % slot)
        stored, count = struct.unpack_from("<II", self.payload, slot)
        if stored < 8 or stored - 8 > self.payload_bytes:
            raise DecodeError("pointer at 0x%x leaves payload" % slot)
        return stored - 8, count


def field(value, offset, status, **extra):
    row = {"value": value, "source_offset": offset, "status": status}
    row.update(extra)
    return row


def clean(value):
    return value if math.isfinite(value) else None


def decode_env(blob, base):
    if base + ENV_RECORD_BYTES > blob.payload_bytes:
        raise DecodeError("environment record leaves payload")
    keyed = {}
    for name, offset, kind in ENV_FIELDS:
        at = base + offset
        rows = {}
        for index, key in enumerate(KEYS):
            if kind == "f":
                rows[key] = field(clean(blob.floats(at + 4 * index, 1)[0]), at + 4 * index, "asset_verified")
            elif kind == "c":
                r, g, b, hdr = blob.floats(at + 16 * index, 4)
                rows[key] = field({"rgb": [clean(r), clean(g), clean(b)], "intensity": clean(hdr)}, at + 16 * index, "asset_verified")
            elif kind == "v3":
                rows[key] = field([clean(x) for x in blob.floats(at + 12 * index, 3)], at + 12 * index, "asset_verified")
            else:
                status = "native_confirmed" if name.endswith("_cube_index") else "hypothesis"
                rows[key] = field(blob.u32(at + 4 * index), at + 4 * index, status)
        keyed[name] = rows
    direction = field([clean(x) for x in blob.floats(base + 0x430, 3)], base + 0x430, "asset_verified")
    unmapped = []
    for start, end in ENV_UNMAPPED:
        raw = blob.payload[base + start:base + end]
        unmapped.append({"source_offset": base + start, "bytes": end - start, "sha256": hashlib.sha256(raw).hexdigest(), "status": "unmapped"})
    return {"source_offset": base, "record_bytes": ENV_RECORD_BYTES, "keys": list(KEYS), "time_keyed": keyed, "directional_light_direction": direction, "unmapped_spans": unmapped}


def decode_cubes(blob):
    base, count = blob.array(ROOT_CUBES)
    cubes = []
    for index in range(count):
        at = base + index * CUBE_ENTRY_BYTES
        faces = []
        digest = hashlib.sha256()
        for face in range(6):
            slot = at + face * 8
            texels, texel_count = blob.array(slot)
            if texel_count != CUBE_FACE_TEXELS or texels + texel_count * 4 > blob.payload_bytes:
                raise DecodeError("unexpected ambient cube face layout")
            digest.update(blob.payload[texels:texels + texel_count * 4])
            faces.append(texels)
        cubes.append({"index": index, "face_texel_offsets": faces, "face_size": [8, 8], "texel_bytes": 4, "pixels_sha256": digest.hexdigest(), "channel_order_status": "hypothesis"})
    return cubes


def decode_region(data):
    blob = Blob(data)
    base, count = blob.array(ROOT_ENV)
    if count != 1:
        raise DecodeError("expected one environment record, found %d" % count)
    hours = blob.floats(ROOT_DAY_DIVISION, 8)
    return {
        "schema": SCHEMA,
        "kind": "region",
        "source_sha256": blob.sha256,
        "region_key": field(blob.payload[ROOT_REGION_KEY:ROOT_REGION_KEY + 8].hex(), ROOT_REGION_KEY, "asset_verified"),
        "sky_asset_id": field(blob.u32(ROOT_SKY_ID), ROOT_SKY_ID, "hypothesis"),
        "day_division_hours": field({key: {"start": hours[i], "end": hours[i + 4]} for i, key in enumerate(KEYS)}, ROOT_DAY_DIVISION, "asset_verified"),
        "environment": decode_env(blob, base),
        "ambient_cubes": decode_cubes(blob),
    }


def decode_space_lights(data):
    blob = Blob(data)
    base, count = blob.array(SPACE_LIGHTS)
    lights = []
    for index in range(count):
        at = base + index * LIGHT_BYTES
        v = blob.floats(at, 27)
        lights.append({
            "index": index,
            "source_offset": at,
            "position": [clean(x) for x in v[:3]],
            "time_keyed": {key: {
                "color": [clean(x) for x in v[3 + 3 * i:6 + 3 * i]],
                "multiplier": clean(v[15 + i]),
                "attenuation_start": clean(v[19 + i]),
                "attenuation_end": clean(v[23 + i]),
            } for i, key in enumerate(KEYS)},
            "field_status": "hypothesis",
        })
    return {
        "schema": SCHEMA,
        "kind": "space_lights",
        "source_sha256": blob.sha256,
        "region_key": field(blob.payload[SPACE_REGION_KEY:SPACE_REGION_KEY + 8].hex(), SPACE_REGION_KEY, "asset_verified"),
        "lights": lights,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = args.path.read_bytes()
    result = decode_space_lights(data) if args.path.name.endswith(".space_bxml") else decode_region(data)
    text = json.dumps(result, indent=1)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
