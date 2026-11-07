"""Narrow opt-in admission of host-registered Lua5.1 seeall module tables.

This transforms the v0.5 emitter's table-field guards, function/nil and canonical type11/nil equality,
canonical realm type11 table keys, and one approved table-valued read fallback. It does not change
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
READ_HELPER='''
-- v0.8: READ only; host checks actual metadata, not a protected public marker.
-- Exactly one __index table hop to a plain or host-approved seeall target.
local __host_read_table_allowed = __getfenv(0).__amalur_read_table_allowed
local function __read_table_allowed(value)
  if __field_table_allowed(value) then return true end
  return __type(__host_read_table_allowed) == "function" and __host_read_table_allowed(value) == true
end
'''
FIELD=re.compile(r'if __type\((__r\[\d+\]\.value)\) ~= "table" or __getmetatable\(\1\) ~= nil then __unresolved\("Unmodeled Amalur field domain"\) end')
TABLE='if __type(__table) ~= "table" or __getmetatable(__table) ~= nil then __unresolved("Unmodeled Amalur table domain") end'
READ_FIELD_OPS={'GETFIELD','GETFIELD_R1'}
READ_TABLE_OPS={'GETTABLE','GETTABLE_S','GETTABLE_N'}
WRITE_TABLE_OPS={'SETFIELD','SETFIELD_R1','SETTABLE','SETTABLE_BK','SETTABLE_S','SETTABLE_S_BK','SETTABLE_N','SETTABLE_N_BK'}
OPCODE_COMMENT=re.compile(r'\s*-- file 0x[0-9a-fA-F]+: ([A-Z0-9_]+)\s*')
def adapt_table_guards(source):
    lines=source.splitlines(keepends=True);opcode=None
    counts={'field_guards_adapted':0,'table_guards_adapted':0,
            'proxy_read_field_guards_adapted':0,'proxy_read_table_guards_adapted':0,
            'write_table_guards_preserved':0,'self_table_guards_preserved':0}
    for index,line in enumerate(lines):
        comment=OPCODE_COMMENT.fullmatch(line)
        if comment:opcode=comment[1];continue
        field=FIELD.fullmatch(line.strip())
        if field:
            if opcode not in READ_FIELD_OPS:raise ValueError('Field guard is not under an expected GETFIELD opcode: '+str(opcode))
            replacement='if __type('+field[1]+') ~= "table" or not __read_table_allowed('+field[1]+') then __unresolved("Unmodeled Amalur field domain") end'
            lines[index]=line.replace(field[0],replacement)
            counts['field_guards_adapted']+=1;counts['proxy_read_field_guards_adapted']+=1
        elif line.strip()==TABLE:
            if opcode in READ_TABLE_OPS:
                helper='__read_table_allowed';counts['proxy_read_table_guards_adapted']+=1
            elif opcode in WRITE_TABLE_OPS:
                helper='__field_table_allowed';counts['write_table_guards_preserved']+=1
            elif opcode=='SELF':
                helper='__field_table_allowed';counts['self_table_guards_preserved']+=1
            else:raise ValueError('Table guard is not under an expected read/write/SELF opcode: '+str(opcode))
            lines[index]=line.replace(TABLE,'if __type(__table) ~= "table" or not '+helper+'(__table) then __unresolved("Unmodeled Amalur table domain") end')
            counts['table_guards_adapted']+=1
    return ''.join(lines),counts
def primitive(value,kind):
    return f'({kind} == "nil" or {kind} == "boolean" or {kind} == "string" or ({kind} == "number" and {value} >= -2147483648 and {value} <= 2147483647 and {value} % 1 == 0))'
EQ_PRIMITIVES=primitive('__left','__lt')+' and '+primitive('__right','__rt')
EQ_GUARD='if not ('+EQ_PRIMITIVES+') then __unresolved("Unmodeled Amalur comparison domain") end'
EQ_NIL_FUNCTION='((__lt == "function" and __rt == "nil") or (__lt == "nil" and __rt == "function"))'
# Native EQ rejects unequal low-nibble tags before any same-tag/metamethod path.
# Admit only the host's exact canonical realm carrier, not arbitrary userdata.
EQ_NIL_TYPE11='((__rt == "nil" and __type11_key_allowed(__left)) or (__lt == "nil" and __type11_key_allowed(__right)))'

def adapt_equality_guards(source):
    lines=source.splitlines(keepends=True);count=0
    for index,line in enumerate(lines):
        if line.strip()!=EQ_GUARD:continue
        # Fail closed if the emitter shape changes. Ordered comparisons have
        # additional same-type restrictions and never match EQ_GUARD.
        if index+1>=len(lines) or lines[index+1].strip() not in {
            'if (__left == __right) == true then','if (__left == __right) == false then'}:
            raise ValueError('Primitive equality guard is not followed by the expected EQ branch')
        lines[index]=line.replace(EQ_GUARD,'if not (('+EQ_PRIMITIVES+') or '+EQ_NIL_FUNCTION+' or '+EQ_NIL_TYPE11+') then __unresolved("Unmodeled Amalur comparison domain") end')
        count+=1
    return ''.join(lines),count

KEY_GUARD='if not (__kt == "string" or (__kt == "number" and __key >= -2147483648 and __key <= 2147483647 and __key % 1 == 0)) then __unresolved("Unmodeled Amalur table-key domain") end'
KEY_HELPER='\n-- v0.8: host captures the original realm carrier membership predicate at init.\n-- Never admit arbitrary userdata by its public metatable marker.\nlocal __host_type11_key_allowed = __getfenv(0).__amalur_type11_key_allowed\nlocal function __type11_key_allowed(value)\n  return __type(value) == "userdata" and __type(__host_type11_key_allowed) == "function"\n      and __host_type11_key_allowed(value) == true\nend\n'
def adapt_key_guards(source):
    lines=source.splitlines(keepends=True);count=0;self_guards=0
    for index,line in enumerate(lines):
        if line.strip()!=KEY_GUARD:continue
        if index==0 or lines[index-1].strip()!='local __kt = __type(__key)':
            raise ValueError('Table key guard is not preceded by expected key type binding')
        next_line=lines[index+1].strip() if index+1<len(lines) else ''
        if next_line=='if __kt ~= "string" then __unresolved("Unmodeled Amalur method key") end':
            self_guards+=1
            continue # Preserve SELF's string-only key domain unchanged.
        if not (re.fullmatch(r'__r\[\d+\]\.value = __table\[__key\]',next_line) or next_line.startswith('__table[__key] = ')):
            raise ValueError('Table key guard is not followed by expected read/write')
        replacement=KEY_GUARD.replace('if not (','if not (__type11_key_allowed(__key) or (',1).replace(')) then', '))) then',1)
        lines[index]=line.replace(KEY_GUARD,replacement);count+=1
    return ''.join(lines),count,self_guards

def adapt_source(source):
    if source.count(HEADER)!=1 or '__field_table_allowed' in source:
        raise ValueError('Expected one untouched v0.5 generated-source header')
    source,guards=adapt_table_guards(source)
    source,equality=adapt_equality_guards(source)
    source,keys,self_guards=adapt_key_guards(source)
    source=source.replace(HEADER,HEADER+HELPER+READ_HELPER+KEY_HELPER)
    return source,{**guards,
                   'function_nil_equality_guards_adapted':equality,
                   'canonical_type11_nil_equality_guards_adapted':equality,
                   'canonical_type11_key_guards_adapted':keys,
                   'self_key_guards_preserved':self_guards,
                   'scope':'One host-checked table-valued __index hop for GETFIELD/GETTABLE reads; writes/SELF retain prior table guards. Canonical realm type11 versus nil EQ admitted; table/arbitrary userdata equality unchanged. Existing seeall/function-nil EQ/canonical type11 key extensions preserved.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    if args.input.resolve()==args.output.resolve():raise ValueError('Preserve the original generated source')
    data=args.input.read_bytes();adapted,report=adapt_source(data.decode('utf-8-sig'))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(adapted,encoding='utf-8')
    report.update(input_sha256=hashlib.sha256(data).hexdigest(),output_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest())
    args.output.with_suffix(args.output.suffix+'.adapter.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
