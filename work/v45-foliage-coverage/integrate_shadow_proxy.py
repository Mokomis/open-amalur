from pathlib import Path
import json,hashlib
P=Path(r'C:\Users\rwill\Documents\Opem Amalur')
V=P/'work/v45-foliage-coverage';B=V/'before-shadow-proxy-integration';B.mkdir(exist_ok=True)

def replace(s,a,b):
    if not s.count(a) and a.startswith(" "):a=a.lstrip()
    assert s.count(a)==1,(a[:90],s.count(a))
    return s.replace(a,b)

files={n:(P/'work/v19-host'/n).read_text() for n in ['oa_stream.c','oa_stream.h','android_scene.c','oa_post.c']}
for n,s in files.items():
    if (B/n).exists():assert (B/n).read_text()==s,n
    else:(B/n).write_text(s)
s=files['oa_stream.c']
s=replace(s,'LODS=6,GRASS=3,TREE_LEAF=4,REGION=5,','LODS=7,GRASS=3,TREE_LEAF=4,REGION=5,SHADOW_LEAF=6,')
s=replace(s,'typedef struct cell{','typedef struct shadow_replacement{uint32_t source,cell_index;}shadow_replacement;\ntypedef struct shadow_dependency{uint32_t cell_index,anchor_index;}shadow_dependency;\ntypedef struct cell{')
s=replace(s,'int shown;}cell;','int shown,shadow_present;}cell;')
s=replace(s,'unsigned char *leaf_materials;','shadow_replacement *shadow_replacements;shadow_dependency *shadow_dependencies;unsigned shadow_replacement_count,shadow_dependency_count,shadow_index_cells,shadow_proxy_draws,shadow_observed;float shadow_distance_scale;\n unsigned char *leaf_materials;')
s=replace(s,'else if(j.kind==0&&j.lod==REGION)snprintf','else if(j.kind==0&&j.lod==SHADOW_LEAF)snprintf(name,sizeof(name),"world/s%d_%d.bin",s->cells[j.index].ix,s->cells[j.index].iy);else if(j.kind==0&&j.lod==REGION)snprintf')
s=replace(s,'&&family!=8&&family!=9)continue;','&&family!=8&&family!=9&&family!=10)continue;')
s=replace(s,'(slot>=676&&slot<=700)?1.0f:4.0f','(slot>=676&&slot<=700)||slot==703?1.0f:4.0f')
# The existing validated auxiliary index reader also supplies source shadow cells.
a=s.index('/* Optional authored Region/actor visuals');e=s.index('s->started=1;',a)
block=s[a:e]
shadow=block.replace('Optional authored Region/actor visuals','Optional source-owned tree shadow visuals').replace('world/region-index.bin','world/shadow-index.bin').replace('region_distance_scale','shadow_distance_scale').replace('region_index_cells','shadow_index_cells').replace('lod[REGION]','lod[SHADOW_LEAF]').replace('Authored region index','Authored shadow index')
shadow=replace(shadow,'c->lod[SHADOW_LEAF].triangles=tris;','c->lod[SHADOW_LEAF].triangles=tris;c->shadow_present=1;')
loader=r'''  /* Replacement lookups are resolved after every optional cell has been registered.
   * Missing or invalid dependency tables disable replacement admission, retaining old casters. */
  {size_t z=0;uint8_t *q=asset_read(m,"world/shadow-replacements.bin",&z);uint32_t n=0,k;int valid=1;
   if(q&&z>=12&&!memcmp(q,"OASHR01",8)){memcpy(&n,q+8,4);if(n>65536||z!=12+(size_t)n*12)valid=0;
    if(valid){shadow_replacement *map=(shadow_replacement*)calloc(n?n:1,sizeof(*map));if(!map)valid=0;
     for(k=0;valid&&k<n;k++){uint32_t source,j;int32_t x,y;memcpy(&source,q+12+k*12,4);memcpy(&x,q+16+k*12,4);memcpy(&y,q+20+k*12,4);if(k&&source<=map[k-1].source){valid=0;break;}for(j=0;j<cells;j++)if(s->cells[j].ix==x&&s->cells[j].iy==y)break;if(j==cells||!s->cells[j].shadow_present){valid=0;break;}map[k].source=source;map[k].cell_index=j;}
     if(valid){s->shadow_replacements=map;s->shadow_replacement_count=n;}else free(map);}}
   if(q&&!valid)LOGE("Shadow replacement map invalid; keep original Region casters");free(q);}
  {size_t z=0;uint8_t *q=asset_read(m,"world/shadow-cell-deps.bin",&z);uint32_t n=0,k;int valid=1;
   if(q&&z>=12&&!memcmp(q,"OASHD01",8)){memcpy(&n,q+8,4);if(n>65536||z!=12+(size_t)n*16)valid=0;
    if(valid){shadow_dependency *map=(shadow_dependency*)calloc(n?n:1,sizeof(*map));if(!map)valid=0;
     for(k=0;valid&&k<n;k++){int32_t x[4];uint32_t j,t;memcpy(x,q+12+k*16,16);for(j=0;j<cells;j++)if(s->cells[j].ix==x[0]&&s->cells[j].iy==x[1])break;for(t=0;t<cells;t++)if(s->cells[t].ix==x[2]&&s->cells[t].iy==x[3])break;if(j==cells||t==cells||!s->cells[j].shadow_present||!s->cells[t].shadow_present){valid=0;break;}map[k].cell_index=j;map[k].anchor_index=t;}
     if(valid){s->shadow_dependencies=map;s->shadow_dependency_count=n;}else free(map);}}
   else valid=0;
   if(!valid){s->shadow_index_cells=0;LOGE("Shadow dependencies unavailable; keep original leaf casters");}free(q);}
  if(s->shadow_index_cells)LOGI("Native tree shadow registry cells=%u region_replacements=%u dependencies=%u",s->shadow_index_cells,s->shadow_replacement_count,s->shadow_dependency_count);
'''
s=s[:e]+shadow+loader+s[e:]
s=replace(s,'free(s->water);free(s->cells);','free(s->shadow_replacements);free(s->shadow_dependencies);free(s->water);free(s->cells);')
# Request caster geometry with expanded bounds, retaining ordinary body-LOD distances.
a=s.index('{lod_data *g=c->lod+REGION;');e=s.index('\n',a)
req=s[a:e].replace('lod+REGION','lod+SHADOW_LEAF').replace('oa_stream_region&&g->triangles','oa_stream_shadow_proxy&&s->shadow_index_cells&&c->shadow_present').replace('!oa_stream_region','!oa_stream_shadow_proxy').replace('(int)i,REGION','(int)i,SHADOW_LEAF')
s=s[:e]+'\n'+req+s[e:]
s=replace(s,'int oa_stream_region=1;','int oa_stream_region=1;int oa_stream_shadow_proxy=1;')
# Guard fallback suppression by the full readiness dependency closure (not just a file's existence).
a=s.index('/* Binds a material. In the shadow pass')
helpers=r'''static int shadow_cell_ready(const oa_stream *s,unsigned index){const lod_data *q;if(index>=s->cell_count)return 0;q=s->cells[index].lod+SHADOW_LEAF;return q->state==STATE_GPU&&lod_ready(s,q);}
static int shadow_fallback_ready(const oa_stream *s,unsigned index){unsigned k;if(!shadow_cell_ready(s,index))return 0;for(k=0;k<s->shadow_dependency_count;k++)if(s->shadow_dependencies[k].cell_index==index&&!shadow_cell_ready(s,s->shadow_dependencies[k].anchor_index))return 0;return 1;}
static int shadow_region_replaced(const oa_stream *s,uint32_t source){unsigned lo=0,hi=s->shadow_replacement_count;while(lo<hi){unsigned m=lo+(hi-lo)/2;if(s->shadow_replacements[m].source<source)lo=m+1;else hi=m;}return lo<s->shadow_replacement_count&&s->shadow_replacements[lo].source==source&&shadow_cell_ready(s,s->shadow_replacements[lo].cell_index);}
'''
s=s[:a]+helpers+s[a:]
s=replace(s,'int last_phase,int reset_stats){','int last_phase,int reset_stats,int caster_only){')
s=replace(s,'region_lod_culled=0,leaf_lod_culled=0;int j,k,phase','region_lod_culled=0,leaf_lod_culled=0,proxy_draws=0;int shadow_active=caster_only&&oa_stream_shadow_proxy&&oa_stream_leaf_native&&(features&128u)&&s->shadow_index_cells;int j,k,phase')
s=replace(s,'c->lod[REGION].state==STATE_GPU))&&cell_visible','c->lod[REGION].state==STATE_GPU)||(shadow_active&&c->lod[SHADOW_LEAF].state==STATE_GPU))&&cell_visible')
a=s.index('for(i=0;i<count;i++){const cell *c=');e=s.index('\n   for(d=0;',a)
s=s[:a]+r'''   for(i=0;i<count;i++){unsigned cell_index=vis[phase>=4?count-1-i:i].index;const cell *c=s->cells+cell_index;int leaf_pass,leaf_ready=phase==2&&oa_stream_leaf_native&&(features&128u)&&s->leaf_materials&&c->lod[TREE_LEAF].state==STATE_GPU&&lod_ready(s,c->lod+TREE_LEAF);int shadow_ready=phase==2&&shadow_active&&shadow_fallback_ready(s,cell_index);
    for(leaf_pass=0;leaf_pass<4;leaf_pass++){int region_pass=leaf_pass==2,proxy_pass=leaf_pass==3;const lod_data *q;unsigned d;int bound_array=0;
     if((leaf_pass==0&&c->shown<0)||(leaf_pass==1&&(!leaf_ready||shadow_ready))||(region_pass&&(phase==3||!oa_stream_region||!s->region_index_cells))||(proxy_pass&&!shadow_ready))continue;
     q=c->lod+(proxy_pass?SHADOW_LEAF:region_pass?REGION:leaf_pass==1?TREE_LEAF:phase==3?GRASS:c->shown);
     if(leaf_pass==1)native_leaf_cells++;else if(leaf_pass==0&&phase==2&&oa_stream_leaf_lod_override==0&&c->lod[0].state==STATE_GPU&&lod_ready(s,c->lod)){q=c->lod;forced_leaf_cells++;}
     if(q->state!=STATE_GPU||(!region_pass&&!proxy_pass&&phase==3&&c->distance>OA_STREAM_GRASS)||!lod_ready(s,q))continue;if(region_pass&&phase==0)region_cells++;
''' +s[e:]
s=replace(s,'if(leaf_pass==0&&leaf_ready&&s->leaf_materials[r->texture])continue;','if(leaf_pass==0&&(leaf_ready||shadow_ready)&&s->leaf_materials&&s->leaf_materials[r->texture])continue;')
s=replace(s,'const region_range *rr=q->ranges+d;float dx=','const region_range *rr=q->ranges+d;if(region_pass&&shadow_active&&(rr->flags&0x80000000u)&&shadow_region_replaced(s,rr->source))continue;float dx=')
s=replace(s,'rr->distance_scale:s->region_distance_scale','rr->distance_scale:(proxy_pass?s->shadow_distance_scale:s->region_distance_scale)')
s=replace(s,'draws++;tris+=r->count/3;if(region_pass)','draws++;tris+=r->count/3;if(proxy_pass&&s->materials[r->texture].native_family==10)proxy_draws++;if(region_pass)')
s=replace(s,'  glDisable(GL_BLEND);glDepthMask(GL_TRUE);glBindVertexArray(0);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,0);s->drawn_cells=count;', '  if(caster_only&&proxy_draws){s->shadow_proxy_draws+=proxy_draws;if(!s->shadow_observed){s->shadow_observed=1;LOGI("Native tree shadow proxies rendered draws=%u source_owned=1 exact_float_wind=1",proxy_draws);}}if(!oa_stream_shadow_proxy)s->shadow_observed=0;\n  glDisable(GL_BLEND);glDepthMask(GL_TRUE);glBindVertexArray(0);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,0);s->drawn_cells=count;')
s=replace(s,'s->reflection_attempted=0;if(s->terrain_paint)','s->reflection_attempted=0;s->shadow_observed=0;if(s->terrain_paint)')
s=replace(s,'o->leaf_lod_culled=s->leaf_lod_culled;','o->leaf_lod_culled=s->leaf_lod_culled;o->shadow_proxy_draws=s->shadow_proxy_draws;')
s=replace(s,'programs,f,0,6,1);','programs,f,0,6,1,0);')
files['oa_stream.c']=s
s=files['oa_stream.h'];s=replace(s,'region_lod_culled,leaf_lod_culled;float','region_lod_culled,leaf_lod_culled,shadow_proxy_draws;float');s=replace(s,'extern int oa_stream_region;','extern int oa_stream_region;\nextern int oa_stream_shadow_proxy;');s=replace(s,'int first,int last,int reset_stats);','int first,int last,int reset_stats,int caster_only);');files['oa_stream.h']=s
s=files['android_scene.c'];s=replace(s,'int last_phase,int depth_only){','int last_phase,int depth_only,int caster_only){');s=replace(s,'first_phase,last_phase,first_phase==0);','first_phase,last_phase,first_phase==0,caster_only);')
s=replace(s,'world_draw(g,matrix,eye,0,shadow_matrix,0,3,1);','world_draw(g,matrix,eye,0,shadow_matrix,0,3,1,0);')
s=replace(s,'world_draw(g,g->native_shadow.cascade[ci].vp,eye,0,shadow_matrix,0,3,1);','world_draw(g,g->native_shadow.cascade[ci].vp,eye,0,shadow_matrix,0,3,1,1);')
s=replace(s,'world_draw(g,matrix,eye,shadow_on,shadow_matrix,0,3,0);','world_draw(g,matrix,eye,shadow_on,shadow_matrix,0,3,0,0);')
s=replace(s,'world_draw(g,matrix,eye,shadow_on,shadow_matrix,4,6,0);','world_draw(g,matrix,eye,shadow_on,shadow_matrix,4,6,0,0);')
s=replace(s,'oa_fx_native_shape=prop_int("debug.opem.fxshape",1);','oa_stream_shadow_proxy=prop_int("debug.opem.shadowproxy",1);oa_fx_native_shape=prop_int("debug.opem.fxshape",1);')
s=replace(s,'leaf_lod_rejections=%u",st.cells_drawn','leaf_lod_rejections=%u shadow_proxy_draws=%u",st.cells_drawn');s=replace(s,'st.region_lod_culled,st.leaf_lod_culled);','st.region_lod_culled,st.leaf_lod_culled,st.shadow_proxy_draws);');files['android_scene.c']=s
s=files['oa_post.c']
s=replace(s,'vec3 normal=n.xyz;if(geometry_kind==2&&material_family==6','vec3 normal=n.xyz;if(geometry_kind==2&&material_family==10&&(features&128)!=0)pos+=n.xyz*(material_specular.y*leaf_palette[int(uv_second.x)]);if(geometry_kind==2&&material_family==6')
s=replace(s,'(material_family==5||material_family==6)?texture(t2,UV).g','(material_family==5||material_family==6||material_family==10)?texture(t2,UV).g')
files['oa_post.c']=s
for n,s in files.items():(P/'work/v19-host'/n).write_text(s)
(V/'shadow-proxy-source-integration.json').write_text(json.dumps({'sources':{n:hashlib.sha256(s.encode()).hexdigest()for n,s in files.items()},'mode':'CSM only; main z prepass and color retain visible leaf cards','readiness':'per-cell fallback dependencies and per-Region source anchor lookup','legacy':'no index/toggle0 retains original casters','wind':'family10 fullfloat object-normal-forward-world displacement','source_stage':'34 unit343974 source poses only; nonunit/otherfamilies remain exact old shadowfallback'},indent=2))
print('Source shadow proxy integration written; not yet built or deployed.')
