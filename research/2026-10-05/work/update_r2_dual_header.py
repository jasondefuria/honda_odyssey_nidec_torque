from pathlib import Path
import sys,json,hashlib,ast
root=Path(__file__).resolve().parents[1];out=root/'outputs';sys.path.insert(0,str(out))
from build_thr_r2_rwd import parse
src=out/'39990-THR,A020_R2_IDENTITY_EXPERIMENTAL.rwd';raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()=='645a3fab1db8212430911bf369fccae80efd8fc1b2859654c6c134768cfa20d2'
h,start,size,offset,payload=parse(raw)
h[3]=[b'39990-THR-A020\0\0',b'39990-THR,A020\0\0'];h[4]=[bytes.fromhex('011101121120')]*2
body=b'Z\r\n'+b''.join(bytes([len(values)])+b''.join(bytes([len(v)])+v for v in values) for values in h)+start.to_bytes(4,'big')+size.to_bytes(4,'big')+payload
result=body+(sum(body)&0xffffffff).to_bytes(4,'little');h2,a,n,off,p=parse(result);assert h2==h and (a,n)==(start,size) and p==payload
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/nrdr-reference/openpilot/nrdr/tools/eps')
from rwd_format.x5a import x5a
fw=x5a(result);assert fw.keys==bytes.fromhex('010203')
# Load only pure ID-matching functions, not any transport/flashing code.
tree=ast.parse((root/'work/uds_review/eps-update.py').read_text());nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('_normalize_app_id','get_seed_secret')];ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'identity_matching','exec'),ns)
for identity in h[3]:assert ns['get_seed_secret'](fw,identity)==h[4][0]
try:ns['get_seed_secret'](fw,b'39990-TG7-A060')
except RuntimeError:pass
else:raise AssertionError('unrelated identity accepted')
lut=bytes(json.loads((root/'work/tla-decrypt-lookup.json').read_text()));decoded=p.translate(lut)
assert sum(int.from_bytes(decoded[i:i+2],'big') for i in range(0,len(decoded),2))&65535==0
name='39990-THR,A020_R2_DUAL_ID_EXPERIMENTAL.rwd';dest=out/name
with dest.open('xb') as f:f.write(result)
r={'file':name,'sha256':hashlib.sha256(result).hexdigest(),'size':len(result),'source':src.name,'supported_identities':[x.rstrip(b'\0').decode() for x in h[3]],'security_entry_count':len(h[4]),'encryption_key_count':len(h[5]),'encrypted_payload_unchanged':p==payload,'download_start':hex(a),'download_length':hex(n),'payload_offset':off,'checksum_A':decoded[0x7ff80-start:0x7ff82-start].hex(),'checksum_C':decoded[-2:].hex(),'parser_and_identity_matching':'PASS; unrelated TG7 identity rejected','note':'Existing flasher normalizes comma and hyphen already. Explicit dual entries do not prove ECU acceptance. Not flashed.'}
(out/'THR_R2_dual_header_validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
