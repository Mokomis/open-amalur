"""Read native placement records; does not instantiate gameplay or infer visual parts.

Native evidence (koa.exe cs:15032, existing private Ghidra export):
00fdc910: Space asset data +0x210/+0x214 is begin/count with 0x68 stride.
00fe4970 -> 00f92480: consume the array, advancing by 0x68.
00f92080: record[0xe] (+0x38) is the resolved simtype; values <2 do not instantiate.
00f873a0 -> 00f72340: pass the placement transform at record+8.
A standalone GOR contains the same record layout at file+16. The validator
checks bounds and independent transform validity; no overlapping instance keys
were available for a paired-record comparison. Quaternions are returned as stored;
heading_xy separately exposes the validated native planar heading convention.
"""
from __future__ import annotations
import struct,math,hashlib
RECORD_BYTES=104
class PlacementError(ValueError):pass

def _extent(data:bytes)->int:
 if len(data)<8:raise PlacementError('Missing container header')
 n=struct.unpack_from('<I',data)[0]+8
 if not 8<=n<=len(data):raise PlacementError('Declared payload is out of bounds')
 return n

def _record(data:bytes,offset:int,end:int)->dict:
 if offset<8 or offset+RECORD_BYTES>end:raise PlacementError('Placement record is out of bounds')
 raw=data[offset:offset+RECORD_BYTES]
 nameptr,instance=struct.unpack_from('<II',raw)
 name=None
 if 8<=nameptr<end:
  terminator=data.find(b'\0',nameptr,min(end,nameptr+1024))
  if terminator>=0:
   try:name=data[nameptr:terminator].decode('utf-8')
   except UnicodeDecodeError:pass
 xyz=struct.unpack_from('<3f',raw,8);q=struct.unpack_from('<4f',raw,24);scale=struct.unpack_from('<3f',raw,40)
 if not all(math.isfinite(v) for v in xyz+q+scale):raise PlacementError('Non-finite placement transform')
 return {'offset':offset,'name':name,'instance_id':instance,'position':xyz,'quaternion':q,'scale':scale,
         'flags':struct.unpack_from('<I',raw,52)[0],'type_id':struct.unpack_from('<I',raw,56)[0],
         'opaque_tail_u32':list(struct.unpack_from('<11I',raw,60)),
         'record_sha256':hashlib.sha256(raw).hexdigest()}

def parse_space(data:bytes)->dict:
 end=_extent(data)
 if end<8+0x218:raise PlacementError('Space header is too short')
 begin,count=struct.unpack_from('<II',data,8+0x210)
 if count>1_000_000 or (count and (begin<8 or begin+count*RECORD_BYTES>end)):
  raise PlacementError('Placement array is out of bounds')
 return {'space_id':struct.unpack_from('<I',data,8)[0],'array_offset':begin,'count':count,
         'records':[_record(data,begin+i*RECORD_BYTES,end) for i in range(count)]}

def parse_gor(data:bytes)->dict:
 end=_extent(data)
 if end<120:raise PlacementError('Standalone object record is too short')
 return {'space_id':struct.unpack_from('<I',data,8)[0],'header_word_12':struct.unpack_from('<I',data,12)[0],
         'record':_record(data,16,end)}

def heading_xy(quaternion):
 """Heading of native local +X after its conjugated world rotation.

 Matches the native row-vector world matrix convention independently checked at
 0x00ac3a70 in outputs/scene-v17/native-prop-matrix-verification.json.
 Projects tilted placements into the existing host's planar heading; AI and
 motion-tree policies remain authored and are not recovered by this conversion.
 """
 x,y,z,w=quaternion
 return math.atan2(2*(x*y-z*w),1-2*(y*y+z*z))
