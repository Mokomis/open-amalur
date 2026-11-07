from pathlib import Path
p=Path.home()/"Documents/Opem Amalur/work/v20-char/build_zone.py";t=p.read_text(encoding="utf-8")
a='''        if r is not None and typed >> 28 == 15:
            instances.append((typed & 0xfffffff, r))'''
assert a in t
t=t.replace(a,'''        # The top four bits vary and are not understood; the model id is the low 28 bits for every value seen (2 to 7 and 15).
        if r is not None and str(typed & 0xfffffff) in syms["fab"]:
            instances.append((typed & 0xfffffff, r))''')
p.write_text(t,encoding="utf-8",newline="\n");print("ok")
