import sys;sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import shutil,hashlib,json
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=P/'work/v46-canopy';B=Q/'before-selector';B.mkdir(exist_ok=True)
files=['work/v19-host/oa_stream.c','work/v19-host/oa_stream.h','work/v19-host/android_scene.c','work/v19-host/CMakeLists.txt','work/v40-windows-host/CMakeLists.txt'];sources={}
for name in files:
 p=P/name;backup=B/name.replace('/','__')
 if not backup.exists():shutil.copy2(p,backup)
 assert backup.read_bytes()==p.read_bytes(),(name,'changed since backup')
 sources[name]=p.read_text(encoding='utf-8')
def change(name,a,b,count=1):
 s=sources[name];assert s.count(a)==count,(name,a,s.count(a));sources[name]=s.replace(a,b)
f=files[0]
change(f,'#include "oa_cart_probe.h"','#include "oa_cart_probe.h"\n#include "oa_canopy.h"')
change(f,' unsigned char *leaf_materials;unsigned leaf_index_cells,native_leaf_cells;',' oa_canopy *canopy;unsigned canopy_override,canopy_culled,canopy_seen_space;int canopy_enabled,canopy_observed,canopy_seen_mode;\n unsigned char *leaf_materials;unsigned leaf_index_cells,native_leaf_cells;')
change(f,'s->started=1;LOGI("Stream opened','{size_t z=0;uint8_t *q=asset_read(m,"world/canopy-visibility.bin",&z);s->canopy=oa_canopy_open(q,z);s->canopy_override=0xffffffffu;free(q);if(s->canopy)LOGI("Canopy source graph ready initial_space=%u admitted=%u native_default_hops=1",oa_canopy_space(s->canopy),oa_canopy_admitted(s->canopy));}\ns->started=1;LOGI("Stream opened')
change(f,'free(s->leaf_materials);free(s->materials);free(s);','free(s->leaf_materials);free(s->materials);oa_canopy_close(s->canopy);free(s);',2)
change(f,'void oa_stream_set_far(oa_stream *s,float range){s->far_range=range;}','''void oa_stream_set_far(oa_stream *s,float range){s->far_range=range;}
void oa_stream_canopy_update(oa_stream *s,const float feet[3],unsigned override_space){unsigned previous;if(!s||!s->canopy)return;
 if(s->canopy_override!=override_space){s->canopy_override=override_space;s->canopy_enabled=oa_canopy_set_space(s->canopy,override_space);s->canopy_observed=0;if(!s->canopy_enabled)LOGE("Canopy unknown scene identity=%u; retain dense fallback",override_space);}
 previous=oa_canopy_space(s->canopy);if(s->canopy_enabled)oa_canopy_move(s->canopy,feet);if(previous!=oa_canopy_space(s->canopy))LOGI("Canopy portal crossed space=%u admitted=%u",oa_canopy_space(s->canopy),oa_canopy_admitted(s->canopy));}
''')
change(f,'int oa_stream_shadow_proxy=1;','int oa_stream_shadow_proxy=1;int oa_stream_canopy_dense=0;')
change(f,'leaf_lod_culled=0,proxy_draws=0;','leaf_lod_culled=0,canopy_culled=0,proxy_draws=0;')
change(f,'if(q->ranges){const region_range *rr=q->ranges+d;','''if(q->ranges){const region_range *rr=q->ranges+d;
 /* Source collection admission applies to visible leaves and MAIN early depth.
  * Caster passes retain the independently verified R3 shadow/proxy stream. */
 if(!caster_only&&leaf_pass==1&&(rr->flags&0x40000000u)&&!oa_stream_canopy_dense&&s->canopy_enabled&&!oa_canopy_admits(s->canopy,rr->source)){canopy_culled++;continue;}
''')
change(f,'if(!oa_stream_shadow_proxy)s->shadow_observed=0;','''if(!oa_stream_shadow_proxy)s->shadow_observed=0;
 if(!caster_only&&native_leaf_cells&&s->canopy_enabled&&(!s->canopy_observed||s->canopy_seen_mode!=oa_stream_canopy_dense||s->canopy_seen_space!=oa_canopy_space(s->canopy))){s->canopy_observed=1;s->canopy_seen_mode=oa_stream_canopy_dense;s->canopy_seen_space=oa_canopy_space(s->canopy);LOGI("Canopy rendered mode=%s space=%u admitted=%u rejected_runs=%u source_portal_graph=1",oa_stream_canopy_dense?"Dense":"Corrected",s->canopy_seen_space,oa_canopy_admitted(s->canopy),canopy_culled);}
''')
change(f,'s->leaf_lod_culled=leaf_lod_culled+(reset_stats?0:s->leaf_lod_culled);','s->leaf_lod_culled=leaf_lod_culled+(reset_stats?0:s->leaf_lod_culled);s->canopy_culled=canopy_culled+(reset_stats?0:s->canopy_culled);')
change(f,'s->reflection_attempted=0;s->shadow_observed=0;','s->reflection_attempted=0;s->shadow_observed=0;s->canopy_observed=0;')
change(f,'o->shadow_proxy_draws=s->shadow_proxy_draws;','o->shadow_proxy_draws=s->shadow_proxy_draws;o->canopy_space=oa_canopy_space(s->canopy);o->canopy_admitted=oa_canopy_admitted(s->canopy);o->canopy_culled=s->canopy_culled;o->canopy_dense=oa_stream_canopy_dense;')
f=files[1]
change(f,'shadow_proxy_draws;float gpu_mb','shadow_proxy_draws,canopy_space,canopy_admitted,canopy_culled,canopy_dense;float gpu_mb')
change(f,'extern int oa_stream_shadow_proxy;','extern int oa_stream_shadow_proxy;\nextern int oa_stream_canopy_dense;\n/* Explicit native scene identity override (0 uses source scene); portal tracking follows feet. */\nvoid oa_stream_canopy_update(oa_stream *s,const float feet[3],unsigned override_space);')
f=files[2]
change(f,'if(active_stream)oa_stream_update(active_stream,eye);','''{int dense=prop_int("debug.opem.canopy",-1),space=prop_int("debug.opem.space",0);oa_stream_canopy_dense=dense<0?oa_menu_canopy_dense(menu):!!dense;if(active_stream){oa_stream_canopy_update(active_stream,c->body.feet,space>0?(unsigned)space:0);oa_stream_update(active_stream,eye);}}''')
change(f,'shadow_proxy_draws_total=%u",st.cells_drawn','shadow_proxy_draws_total=%u canopy_mode=%u canopy_space=%u canopy_admitted=%u canopy_rejected_runs=%u",st.cells_drawn')
change(f,'st.leaf_lod_culled,st.shadow_proxy_draws);','st.leaf_lod_culled,st.shadow_proxy_draws,st.canopy_dense,st.canopy_space,st.canopy_admitted,st.canopy_culled);')
for f in files[3:]:change(f,'oa_native_water.c oa_cart_probe.c oa_native_filter.c','oa_native_water.c oa_cart_probe.c oa_canopy.c oa_native_filter.c')
report=[]
for name,s in sources.items():
 p=P/name;tmp=p.with_suffix(p.suffix+'.v46tmp');tmp.write_bytes(s.replace('\n','\r\n').encode('utf-8'));tmp.replace(p);report.append(dict(file=name,before_sha256=hashlib.sha256((B/name.replace('/','__')).read_bytes()).hexdigest(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(Q/'selector-source-changes.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
