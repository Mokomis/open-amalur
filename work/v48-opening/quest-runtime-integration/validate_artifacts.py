from pathlib import Path
import struct,json,hashlib,re
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
results=json.loads((O/'test-results.json').read_text());assert results['result']=='PASS' and results['checks']==241
source=(O/'oa_mq01_cursor.c').read_text();table=[int(x.strip()) for x in re.search(r'static const int32_t ids\[\]=\{([^}]+)\}',source).group(1).split(',')]
defs=json.loads((P/'work/v48-opening/quest-start-audit/quest-definition-provenance.json').read_text());provenance=[]
for d in defs:
 raw=(P/d['source']).read_bytes();assert H(raw)==d['sha256']
 ptr,count=struct.unpack_from('<II',raw,8+0x1c);ids=[struct.unpack_from('<I',raw,ptr+56*i)[0] for i in range(count)]
 assert table==[0]+ids and 25 not in ids
 provenance.append(dict(path=d['source'],sha256=d['sha256'],stage_ids=ids))
elf=(O/'test_mq01_cursor_arm64').read_bytes();assert elf[:7]==b'\x7fELF\x02\x01\x01';assert struct.unpack_from('<H',elf,18)[0]==183
pe=(O/'test_mq01_cursor.exe').read_bytes();assert pe[:2]==b'MZ';po=struct.unpack_from('<I',pe,0x3c)[0];assert pe[po:po+4]==b'PE\0\0' and struct.unpack_from('<H',pe,po+4)[0]==0x8664
receipt=dict(result='PASS',windows_checks=results['checks'],windows_execution=True,arm_compile_link=True,arm_execution=False,
 arm_header=dict(class_bits=64,endianness='little',machine='AArch64',machine_id=183,elf_type=struct.unpack_from('<H',elf,16)[0]),
 source_table=table,source_definitions=provenance,host_backend='Recorded atomic acknowledgement fixture; no native QuestMgr/startup effects implemented.',
 no_live_core_UI_save_binding_changes=True,
 hashes={n:H((O/n).read_bytes()) for n in ['oa_mq01_cursor.c','oa_mq01_cursor.h','test_mq01_cursor.c','test_mq01_cursor.exe','test_mq01_cursor_arm64','build-test.cmd','build-test.log']})
(O/'validation-receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
