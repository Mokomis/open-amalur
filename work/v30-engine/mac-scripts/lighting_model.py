"""Reference math recovered from koa.exe and its shipped D3D11 shaders. Evidence labels match lighting-provenance.json."""


def saturate(x):
    return max(0.0, min(1.0, x))


def lerp_key(values, key_a, key_b, t):
    """native_confirmed: FUN_00c8a160 and FUN_00c49860 blend two time keys linearly."""
    return values[key_a] * (1.0 - t) + values[key_b] * t


def point_light_constants(rgb, hdr_intensity, multiplier, start, end):
    """native_confirmed: FUN_00ccf660. Returns (color, attenuation scale, attenuation bias)."""
    if end <= start:
        start = 0.0
    inverse = 1.0 / (end - start)
    scale = hdr_intensity * multiplier
    return [c * scale for c in rgb], -inverse, inverse * end


def point_attenuation(distance, attenuation_scale, attenuation_bias):
    """shader_confirmed: forward loop and rspointlightsheet both use mad_sat(distance, scale, bias)."""
    return saturate(distance * attenuation_scale + attenuation_bias)


def fog_blend(color, fog_color, a, b, z):
    """shader_confirmed: factor is min(1, 2^-(a*z+b)). How a and b derive from fog_start/fog_density is unresolved."""
    factor = min(1.0, 2.0 ** -(a * z + b))
    return [f + factor * (c - f) for c, f in zip(color, fog_color)]


def region_blend_weight(distance, fade, base_weight=1.0):
    """native_confirmed: FUN_00df6150 weights each environment contributor by distance over its fade range."""
    if fade <= 0.0:
        ratio = 1.0 if distance > 0.0 else 0.0
    else:
        ratio = saturate(distance / fade)
    return (1.0 - ratio) * base_weight
