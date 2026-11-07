"""Build work/v21-ui/oa_ui.bin: game UI sprites, baked Cinzel and Alegreya distance fields, title art."""
import struct, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt as edt
root = Path.home() / "Documents/Opem Amalur"
png = root / "work/v21-ui/png"
fonts = root / "work/v21-ui/fonts"; fonts.mkdir(parents=True, exist_ok=True)
SOURCES = {"Cinzel.ttf": "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf", "Alegreya.ttf": "https://github.com/google/fonts/raw/main/ofl/alegreya/Alegreya%5Bwght%5D.ttf",
           "Cinzel-OFL.txt": "https://github.com/google/fonts/raw/main/ofl/cinzel/OFL.txt", "Alegreya-OFL.txt": "https://github.com/google/fonts/raw/main/ofl/alegreya/OFL.txt"}
for name, url in SOURCES.items():
    if not (fonts / name).exists():
        urllib.request.urlretrieve(url, fonts / name)

# Order is oa_ui.h's OA_SPR_ enum: sheet, x, y, w, h.
hud, pause, radial = "ui_hud", "ui_pause_menu", "ui_conversation_radial"
SPRITES = [(hud, 583, 391, 200, 14), (hud, 632, 493, 200, 15), (hud, 583, 405, 236, 14), (pause, 128, 333, 34, 30), (pause, 772, 480, 32, 32), (hud, 905, 65, 46, 50),
           (radial, 257, 0, 62, 63), (radial, 320, 0, 62, 63), (radial, 383, 0, 62, 63), (radial, 446, 0, 62, 63), (radial, 257, 64, 62, 63), (radial, 320, 64, 62, 63)]
wa, a1, a2, it = "ui_icons_inv_weapons_armor", "ui_icons_inv_armor_01", "ui_icons_inv_armor_02", "ui_icons_inv_items"
# Item icons in OA_SPR_I_ order, column and row on each game sheet's 64 pixel grid.
for sheet, col, row in ((wa, 4, 2), (wa, 3, 2), (wa, 7, 0), (wa, 1, 1), (wa, 0, 1), (a1, 1, 3), (a2, 3, 2), (a1, 6, 0), (a1, 3, 4), (a1, 5, 5), (a1, 0, 5), (a1, 7, 1), (a2, 1, 2), (a1, 2, 7), (a2, 4, 0), (it, 2, 3), (it, 0, 3), (it, 1, 3)):
    SPRITES.append((sheet, col * 64, row * 64, 64, 64))
ATLAS = 1024
atlas = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 0))
table, x, y, row = [], 2, 2, 0
for sheet, sx, sy, w, h in SPRITES:
    part = Image.open(png / f"{sheet}.png").convert("RGBA").crop((sx, sy, sx + w, sy + h))
    if x + w + 2 > ATLAS:
        x, y, row = 2, y + row + 2, 0
    atlas.paste(part, (x, y)); table.append((x, y, w, h))
    x += w + 2; row = max(row, h)
blob = bytearray(b"OAUI0002") + struct.pack("<II", ATLAS, ATLAS) + atlas.tobytes() + struct.pack("<I", len(table))
for t in table:
    blob += struct.pack("<4H", *t)

PX, PAD, OVER, FIRST, LAST, SHEET = 44, 8, 4, 32, 126, 1024
field = np.zeros((SHEET, SHEET), np.uint8)
cx, cy, line, glyph_blobs = 1, 1, 0, []
for path, weight in (("Cinzel.ttf", 600), ("Alegreya.ttf", 500)):
    big = ImageFont.truetype(str(fonts / path), PX * OVER)
    big.set_variation_by_axes([weight])
    ascent, descent = big.getmetrics()
    head = struct.pack("<fff", PX, ascent / OVER, (ascent + descent) / OVER)
    records = bytearray()
    for code in range(FIRST, LAST + 1):
        ch = chr(code); left, top, right, bottom = big.getbbox(ch)
        advance = big.getlength(ch) / OVER
        w, h = max(right - left, 1), max(bottom - top, 1)
        m = Image.new("L", (w + 2 * PAD * OVER, h + 2 * PAD * OVER), 0)
        ImageDraw.Draw(m).text((PAD * OVER - left, PAD * OVER - top), ch, font=big, fill=255)
        a = np.asarray(m) > 127
        signed = (edt(a) - edt(~a)) / (PAD * OVER)
        small = np.clip(signed[OVER // 2::OVER, OVER // 2::OVER] * .5 + .5, 0, 1)
        gh, gw = small.shape
        if cx + gw + 1 > SHEET:
            cx, cy, line = 1, cy + line + 1, 0
        if cy + gh + 1 > SHEET:
            raise SystemExit("font sheet full")
        field[cy:cy + gh, cx:cx + gw] = (small * 255).astype(np.uint8)
        records += struct.pack("<4H2hf", cx, cy, gw, gh, round(left / OVER) - PAD, round(top / OVER) - PAD, advance)
        cx += gw + 1; line = max(line, gh)
    glyph_blobs.append(head + bytes(records))
blob += struct.pack("<II", SHEET, SHEET) + field.tobytes()
for g in glyph_blobs:
    blob += g
title = Image.open(png / "ui_main_menu_1.png").convert("RGB")
blob += struct.pack("<II", *title.size) + title.tobytes()
(root / "work/v21-ui/oa_ui.bin").write_bytes(blob)
Image.fromarray(field).save(root / "work/v21-ui/field-preview.png")
print("oa_ui.bin", len(blob), "font sheet rows used", cy + line, "sprites", len(table))
