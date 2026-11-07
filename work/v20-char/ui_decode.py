import json, re, struct, subprocess, sys, zlib, tarfile
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v09-textures")]
import keen_texture
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
raw = root / "work/v21-ui/raw"; out = root / "work/v21-ui/png"; out.mkdir(parents=True, exist_ok=True)
sym = json.loads((root / "work/v20-inputs/symbols.json").read_text())["texture"]
ids = {str(n): k for k, n in sym.items()}
def png(path, w, h, rgba):
    c = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    rows = b"".join(b"\0" + bytes(rgba[y*w*4:(y+1)*w*4]) for y in range(h))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + c(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + c(b"IDAT", zlib.compress(rows, 6)) + c(b"IEND", b""))
def bc3(d, w, h):
    o = bytearray(w*h*4)
    bw, bh, at = (w+3)//4, (h+3)//4, 0
    for by in range(bh):
        for bx in range(bw):
            a0, a1 = d[at], d[at+1]
            bits = int.from_bytes(d[at+2:at+8], "little")
            pal = [a0, a1] + ([((7-i)*a0+i*a1)//7 for i in range(1,7)] if a0 > a1 else [((5-i)*a0+i*a1)//5 for i in range(1,5)]+[0,255])
            c0, c1, idx = *struct.unpack_from("<HH", d, at+8), struct.unpack_from("<I", d, at+12)[0]
            r0,g0,b0 = (c0>>11)*255//31,((c0>>5)&63)*255//63,(c0&31)*255//31
            r1,g1,b1 = (c1>>11)*255//31,((c1>>5)&63)*255//63,(c1&31)*255//31
            col = [(r0,g0,b0),(r1,g1,b1),((2*r0+r1)//3,(2*g0+g1)//3,(2*b0+b1)//3),((r0+2*r1)//3,(g0+2*g1)//3,(b0+2*b1)//3)]
            for py in range(4):
                for px in range(4):
                    x,y = bx*4+px, by*4+py
                    if x>=w or y>=h: continue
                    p = (y*w+x)*4
                    o[p:p+3] = bytes(col[(idx>>(2*(py*4+px)))&3])
                    o[p+3] = pal[(bits>>(3*(py*4+px)))&7]
            at += 16
    return o
for n in ("ui_hud","ui_pause_menu","minimap_icons","help_icons_large","dialog_types","inventory_checkmark","ui_menu_numbers","ui_moves_menu","savapro_mediumsavapro_medium_p00_00","byngve_boldbyngve_bold_p00_00"):
    f = raw / f"{n}.ntx"
    if not f.exists():
        subprocess.run([str(g/"modding/pakfileunpacker.exe"), str(g/"data/initial_0.pak"), "unpack", str(raw), f.name], cwd=g/"modding", capture_output=True, timeout=120)
    if not f.exists(): print("missing", n); continue
    b = f.read_bytes()
    t = b.rfind(b"TXTR")
    w, h = struct.unpack_from("<HH", b, t+24)
    size = struct.unpack_from(">I", b, 24)[0]
    bpp = size/(w*h)
    print(n, w, h, size, bpp, "fmt", b[t+28:t+40].hex())
    d = b[80:80+size]
    if abs(bpp-1) < .01:
        png(out/f"{n}.png", w, h, bc3(d, w, h))
    elif abs(bpp-4) < .01:
        png(out/f"{n}.png", w, h, d)
    else:
        print("  unhandled bpp", bpp)
want = ["ui_menu_buttons","ui_menu_list_cursor","ui_button_list","ui_expander_skulls","ui_expander_thin","ui_expander_special","ui_expander_popup","ui_expander_gradient_edge","ui_hud_boss_bar","minimap_frame","minimap_frame_no_notch","ui_merchant","ui_merchant_background","ledger_skills","ledger_quest_log","ledger_quest_tabs","loot_entry","ui_paper_note","ui_abilities_menu","ui_main_menu_1","ui_main_menu_2","ui_main_menu_3","ui_icons_inv_weapons_common","ui_icons_inv_armor_01","ui_icons_inv_items","ui_icons_abilities_active","ui_icons_abilities_passive","ui_icons_buffs","ui_icons_reagents","ui_ls_out_dalentarth","ui_ls_small","ui_icons_destiny_cards","ui_icon_fate","ui_conversation_radial"]
D = root/"work/v21-ui/dds"; D.mkdir(parents=True, exist_ok=True)
names = [f"{ids[n]}.dds" for n in want if n in ids]
for i in range(0, len(names), 40):
    subprocess.run([str(g/"modding/pakfileunpacker.exe"), str(g/"data/initial_0.pak"), "unpack", str(D), *names[i:i+40]], cwd=g/"modding", capture_output=True, timeout=300)
for n in want:
    q = D/f"{ids[n]}.dds"
    if not q.exists(): print("nofile", n); continue
    data = q.read_bytes()
    w,h,fmt,mips = *struct.unpack_from("<HH", data, 20), data[29], struct.unpack_from("<H", data, 35)[0]
    magic = data[:4]
    o, block = 38, 8 if fmt == 1 else 16
    done = False
    for _ in range(max(mips,1)):
        size = ((w+3)//4)*((h+3)//4)*block
        if max(w,h) <= 2048 and o+size <= len(data):
            try:
                rgba = bytes(keen_texture.decode_blocks(data[o:o+size], w, h, fmt))
                png(out/f"{n}.png", w, h, rgba); print(n, w, h, fmt, mips); done = True
            except Exception as e:
                print("ERR", n, magic, w, h, fmt, mips, e)
            break
        o += size; w,h = max(1,w//2),max(1,h//2)
    if not done: print("skip", n, magic, len(data), data[:40].hex())
for n in ("savapro_mediumsavapro_medium_p00_00","byngve_boldbyngve_bold_p00_00"):
    b = (raw/f"{n}.ntx").read_bytes()
    a = b[80:80+262144]
    png(out/f"{n}.png", 512, 512, b"".join(bytes((255,255,255,x)) for x in a))
with tarfile.open(root/"work/v21-ui/png.tar","w") as t: t.add(out, arcname="png")
