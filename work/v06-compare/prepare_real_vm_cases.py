"""Select bounded real game functions for isolated native VM replay on Windows.

Only acyclic primitive functions with no closures, globals, calls, strings,
custom types, varargs, or division/modulo are selected. This corpus selection is
an execution-domain restriction; excluded functions are not called equivalent.
"""
import argparse,hashlib,json,platform,sys
from pathlib import Path
assert platform.system()=='Windows'
ROOT=Path.home()/'Documents'/'Opem Amalur';sys.path.insert(0,str(ROOT/'src'))
from amalur_script import parse_file
from amalur_reconstruct import lift_function
ALLOWED={1,4,5,7,9,13,25,26,28,34,35,36,37,38,39,44,45,47,48,50,51,52,53,65,66}

def visit(fn,path='0'):
 yield path,fn
 for i,c in enumerate(fn['children']):yield from visit(c,path+'/'+str(i))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=64);ap.add_argument('--output',type=Path,default=ROOT/'outputs/engine-bindings-v06/real-vm-fixtures.json');args=ap.parse_args()
 profile=json.loads((ROOT/'outputs/native-script-profile.json').read_text());records=[];seen=set();inspected=0
 for path in sorted((ROOT/'work/initial-script-corpus-v04').glob('*.lua_bxml')):
  if path.name.startswith('batch'):continue
  parsed=parse_file(path)
  for function_path,fn in visit(parsed['chunk']['root_function']):
   inspected+=1;code=fn['instructions']
   if fn['children'] or fn['upvalue_count'] or fn['vararg_flags'] or fn['parameter_count']>3 or not 2<=len(code)<=40:continue
   if any(i['opcode'] not in ALLOWED for i in code):continue
   if any(i['opcode']==28 and i['sBx_provisional']<0 for i in code):continue
   if any(c['type'] not in {'nil','boolean','number'} for c in fn['constants']):continue
   ir=lift_function(fn,function_path,profile)
   if not ir['body_emittable']:continue
   # A return-only constant body is useful but cap duplicate code+constants.
   constants=[None if c['type']=='nil' else c['value'] if c['type']=='boolean' else int.from_bytes(bytes.fromhex(c['raw_hex']),'big',signed=True) for c in fn['constants']]
   words=[int(i['word_hex'],16) for i in code]
   identity=hashlib.sha256(json.dumps([words,constants,fn['parameter_count'],fn['maximum_stack_size']],separators=(',',':')).encode()).hexdigest()
   if identity in seen:continue
   seen.add(identity)
   records.append({'file':path.name,'input_sha256':parsed['input_sha256'],'function_path':function_path,'function_signature':identity,
                   'parameter_count':fn['parameter_count'],'stack':fn['maximum_stack_size'],'code':words,'constants':constants,
                   'instruction_offsets':[i['file_offset'] for i in code]})
   if len(records)>=args.limit:break
  if len(records)>=args.limit:break
 report={'scope':'Real standalone functions selected by acyclic primitive execution domain; source order bounded selection, not representative/full corpus equivalence.',
         'functions_selected':len(records),'functions_inspected':inspected,'selection_opcodes':sorted(ALLOWED),'records':records}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
if __name__=='__main__':main()
