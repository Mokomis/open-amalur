"""Narrow opt-in admission of host-registered Lua5.1 seeall module tables.

This transforms the v0.5 emitter's table-field guards and admits function/nil
tag-mismatch equality only. It does not change
getmetatable globally, other metatable domains, opcodes, or branch structure.
The portable host supplies a private-registry-backed predicate. Absent that
predicate, the previous plain-table-only restriction remains in effect.
"""
import argparse, hashlib, json, re
from pathlib import Path

HEADER='local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable'
HELPER='''
-- v0.7: only the host's exact registered seeall module-table shape is admitted.
local __host_module_table_allowed = __getfenv(0).__amalur_module_table_allowed
local function __field_table_allowed(value)
  if __getmetatable(value) == nil then return true end
  return __type(__host_module_table_allowed) == "function" and __host_module_table_allowed(value) == true
end
'''
FIELD=re.compile(r'if __type\((__r\[\d+\]\.value)\) ~= "table" or __getmetatable\(\1\) ~= nil then __unresolved\("Unmodeled Amalur field domain"\) end')
TABLE='if __type(__table) ~= "table" or __getmetatable(__table) ~= nil then __unresolved("Unmodeled Amalur table domain") end'
def primitive(value,kind):
    return f'({kind} == "nil" or {kind} == "boolean" or {kind} == "string" or ({kind} == "number" and {value} >= -2147483648 and {value} <= 2147483647 and {value} % 1 == 0))'
EQ_PRIMITIVES=primitive('__left','__lt')+' and '+primitive('__right','__rt')
EQ_GUARD='if not ('+EQ_PRIMITIVES+') then __unresolved("Unmodeled Amalur comparison domain") end'
EQ_NIL_FUNCTION='((__lt == "function" and __rt == "nil") or (__lt == "nil" and __rt == "function"))'

def adapt_equality_guards(source):
    lines=source.splitlines(keepends=True);count=0
    for index,line in enumerate(lines):
        if line.strip()!=EQ_GUARD:continue
        # Fail closed if the emitter shape changes. Ordered comparisons have
        # additional same-type restrictions and never match EQ_GUARD.
        if index+1>=len(lines) or lines[index+1].strip() not in {
            'if (__left == __right) == true then','if (__left == __right) == false then'}:
            raise ValueError('Primitive equality guard is not followed by the expected EQ branch')
        lines[index]=line.replace(EQ_GUARD,'if not (('+EQ_PRIMITIVES+') or '+EQ_NIL_FUNCTION+') then __unresolved("Unmodeled Amalur comparison domain") end')
        count+=1
    return ''.join(lines),count

def adapt_source(source):
    if source.count(HEADER)!=1 or '__field_table_allowed' in source:
        raise ValueError('Expected one untouched v0.5 generated-source header')
    source,fields=FIELD.subn(lambda m:'if __type('+m[1]+') ~= "table" or not __field_table_allowed('+m[1]+') then __unresolved("Unmodeled Amalur field domain") end',source)
    tables=source.count(TABLE)
    source=source.replace(TABLE,'if __type(__table) ~= "table" or not __field_table_allowed(__table) then __unresolved("Unmodeled Amalur table domain") end')
    source,equality=adapt_equality_guards(source)
    source=source.replace(HEADER,HEADER+HELPER)
    return source,{'field_guards_adapted':fields,'table_guards_adapted':tables,
                   'function_nil_equality_guards_adapted':equality,
                   'scope':'Host-marked stock seeall field access and function/nil EQ tag mismatch only; same-tag/custom equality, ordered comparisons, length/list domains unchanged.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    if args.input.resolve()==args.output.resolve():raise ValueError('Preserve the original generated source')
    data=args.input.read_bytes();adapted,report=adapt_source(data.decode('utf-8-sig'))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(adapted,encoding='utf-8')
    report.update(input_sha256=hashlib.sha256(data).hexdigest(),output_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest())
    args.output.with_suffix(args.output.suffix+'.adapter.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
