"""Native BHG material/reflection member name hash, recovered from00af09a0.
ASCII shader identifiers only; native_tolower's extended locale behavior is not modeled.
"""
import json,sys
TABLE=(127,811,1597,2131,2749,4759,5527,5953,8117,9539,10273,10753,11159,12301,13217,14207,15413,17681,18661,19013,21089,22051,25111,25801,27457,28057,29581,30809,32611,34469,36067,37511,38723,40093,41983,43321,45083,47431,49667,50767,53453,55469,57193,59369,61987,65071,73421,77849,84223,89009)
def hash_name(name,seed=0):
 b=name.encode('ascii').lower()
 return (seed+sum(TABLE[i%50]*c+TABLE[c%50]*(i+1) for i,c in enumerate(b)))&0xffffffff
KNOWN={'ConstantColor':10276250,'SpecularValues':11960536,'UTile':883724,'VTile':884831,'UTile2':1122436,'VTile2':1123543,'UseSphericalNormals':22257620,'CenterZOffset':8960387,'NormalDisable':10157840,'TranslucencyDisable':23106261,'SpecularDisable':13865487,'TreeLeafMovementScale':26820802,'AlphaCutoff':6936447,'AlphaReference':11015508}
if __name__=='__main__':
 for name,key in KNOWN.items():assert hash_name(name)==key and hash_name(name.lower())==key
 print(json.dumps({s:{'decimal':hash_name(s),'hex':f'0x{hash_name(s):08x}'} for s in (sys.argv[1:] or KNOWN)},indent=2))
