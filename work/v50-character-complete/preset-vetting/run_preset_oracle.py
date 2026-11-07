"""Execute recovered original preset dispatcher with explicit native option-table fixtures.
This does not run original engine bindings or prove live renderer parity."""
from pathlib import Path
import json,sys,hashlib
R=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/python-libs'))
from lupa.lua51 import LuaRuntime
A=R/'work/v49-character-create/analysis'
data=json.loads((A/'character-data-tables.json').read_text())
pal=json.loads((A/'resolved-cosmetic-palettes.json').read_text())['types']
cat=json.loads((A/'source-customization-options.json').read_text())
source=R/'outputs/initial-corpus-drafts-v05/scripts/d1963a864dd8246f799032b3b843a271a5d20b08fc8223ab54f3bd4d0f55ff32/functions/function_0_15.lua'
fntext=source.read_text()
lua=LuaRuntime(register_eval=False,register_builtins=False)
to=lambda x:lua.table_from(x,recursive=True)
make=lua.eval('function(f,env) setfenv(f,env);return f end')
observer=lua.eval('function(results,param) return function(value) results[param]=value end end')
noop=lua.eval('function(...) end')
out=[];alpha_errors=[]
for typ,ps in data['m_customization_presets'].items():
 race,sex=typ.split('_');rm=cat['race_bits_from_unique_default_head_records'][race];sm=cat['gender_bits_from_unique_default_head_records'][sex]
 for seed in ['default','last']:
  for pnum,preset in ps.items():
   env=lua.table()
   # Recovered guards require plain tables: copy Lua globals, do not add metatable.
   for k,v in lua.globals().items():env[k]=v
   opts=lua.table();effective=lua.table();initial={}
   for k,row in sorted(data['m_gen_options'].items(),key=lambda kv:int(kv[0])):
    opt=to({n:v for n,v in row.items() if n!='selection_change_callback'})
    param=row['param'];values=[]
    if row.get('color'):
     values=list(range(1,1+len(pal[typ].get(param,{}).get('records',[]))))
    elif row.get('alpha'):values=list(range(0,256,5))
    elif row.get('customization_hash'):
     values=[x['asset_id'] for x in cat['records'] if x['category_hash']==row['customization_hash'] and x['race_mask']&rm and x['gender_mask']&sm]
    opt['options']=to(values)
    # Model current original selection by exact source default or final admitted option.
    val=data['m_default_customization'][typ].get(param)
    if seed=='last' and values:val=values[-1]
    selected=values.index(val)+1 if val in values else 1
    opt['selected']=selected;opt['selection_change_callback']=observer(effective,param)
    if values:initial[param]=values[selected-1]
    if values:effective[param]=values[selected-1]
    opts[int(k)]=opt
   cd=lua.table();cd['m_gen_options']=opts
   cd['get_cur_preset_data']=lua.eval('function(presets) return function(n) return presets[n] end end')(to({int(k):v for k,v in ps.items()}))
   env['character_data']=cd
   player=lua.table();actor=lua.table()
   for n in ['get_equipped_object_from_equip_type_and_slot','unequip','unequip_from_portrait']:player[n]=noop
   actor['destroy_from_inventory']=noop
   env['PLAYER']=player;env['ACTOR']=actor;env['get_player']=lua.eval('function() return 1 end');env['m_portrait_win']=1
   fn=make(lua.execute(fntext),env);fn(int(pnum))
   eff={k:v for k,v in effective.items()}
   out.append(dict(type=typ,seed=seed,preset=int(pnum),initial=initial,effective=eff,
    retained_missing_or_invalid={k:{'source':v,'retained':eff.get(k)} for k,v in preset.items() if k in initial and (v not in ([*range(0,256,5)] if k.endswith('Alpha') else [*range(1,1+len(pal[typ][k]['records']))] if k in pal[typ] else [v]))}))
   for k,v in preset.items():
    if k.endswith('Alpha') and k in ['TattooAlpha','EyeLinerAlpha','LipstickAlpha'] and v%5:alpha_errors.append((typ,int(pnum),k,v))
receipt={'source':str(source.relative_to(R)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'scope':'Actual reconstructed Lua5.1 dispatcher executed with source-derived native-option fixtures; engine calls observed only, no original runtime execution.',
 'cases':out,'invalid_alpha_values':sorted(set(alpha_errors)),
 'rules':['Only parameters present in m_gen_options execute callbacks. EyebrowAlpha absent; Ears do_not_display skipped.',
 'Color selects by one-based position; alpha selects by exact value from0,5,...255; assets select by exactID.',
 'Missing/invalid source choices keep previous option.selected, then callback receives previous option value. No clamp/reject/skip whole preset.']}
(O/'preset-dispatch-oracle.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'cases':len(out),'invalid_alpha_values':receipt['invalid_alpha_values']}))
