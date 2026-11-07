from pathlib import Path
import struct,hashlib,json,re
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v33-native-camera');exe=r.parent/'v30-engine/koa.exe';b=exe.read_bytes();pe=struct.unpack_from('<I',b,60)[0];ns=struct.unpack_from('<H',b,pe+6)[0];oh=struct.unpack_from('<H',b,pe+20)[0];base=struct.unpack_from('<I',b,pe+24+28)[0];addr=0xabc070;n=1618
for i in range(ns):
 p=pe+24+oh+40*i;vs,va,rs,rp=struct.unpack_from('<IIII',b,p+8)
 if base+va<=addr and addr+n<=base+va+rs:code=b[rp+addr-base-va:rp+addr-base-va+n];break
else:raise RuntimeError('Function not wholly file-backed')
assert code[:8]==bytes.fromhex('8b4424048b542408') and code[-3:]==bytes.fromhex('c20800')
assembly=(r/'abc070-assembly.txt').read_text(encoding='utf-16');assert not re.search(r'\b(?:call|jmp|j[a-z]{1,3})\s',assembly)
# Original code uses only input/output pointer and stack memory operands; no absolute globals.
for line in assembly.splitlines():
 for operand in re.findall(r'\[([^]]+)\]',line):assert re.fullmatch(r'(eax|ecx|edx|esp)( \+ 0x[0-9a-f]+)?',operand),operand
(r/'abc070-original-code.bin').write_bytes(code)
info={'source':'koa.exe cs:15032','source_sha256':hashlib.sha256(b).hexdigest(),'address':'0x00abc070','bytes':n,'function_sha256':hashlib.sha256(code).hexdigest(),'no_external_calls_or_absolute_data_operands':True,'precision':'SSE double arithmetic; final float conversion','output':'left * right; destination in ECX, right/left on stack; ret 8'}
(r/'matrix-native-identity.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
