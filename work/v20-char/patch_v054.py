from pathlib import Path
p=Path.home()/"Documents/Opem Amalur/work/v19-host/oa_character_test.c";t=p.read_text(encoding="utf-8")
a="fabsf(c.weight[0]+c.weight[1]+c.weight[2]-1)<.001f"
assert a in t
t=t.replace("CHECK("+a+");","{float all=0;uint32_t w;for(w=0;w<c.clip_count;w++)all+=c.weight[w];CHECK(fabsf(all-1)<.001f);}")
assert a not in t
p.write_text(t,encoding="utf-8",newline="\n");print("ok")
