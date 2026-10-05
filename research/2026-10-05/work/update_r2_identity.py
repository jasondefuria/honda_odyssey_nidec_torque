from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[1];out=root/'outputs'
src=out/'39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd';raw=src.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='dbfe61804b35c6ff8855c0c02115c72c5fdd26d6f82e5e2209cf72bbae120311'
sys.path.insert(0,str(out));from build_thr_r2_rwd import parse
h,start,size,offset,enc=parse(raw);lut=json.loads((root/'work/tla-decrypt-lookup.json').read_text());old=enc.translate(bytes(lut));new=bytearray(old)
positions=[0x5eb37+0x46*i for i in range(14)]
for a in positions:
 i=a-start;assert new[i:i+14]==b'39990-THR-A020';new[i:i+14]=b'39990-THR,A020'
def total(end):return sum(int.from_bytes(new[i:i+2],'big') for i in range(0,end-start,2))&65535
new[0x7ff80-start:0x7ff82-start]=total(0x7ff80).to_bytes(2,'big')
new[0x7fffe-start:0x80000-start]=((-total(0x7fffe))&65535).to_bytes(2,'big')
assert total(0x80000)==0
inv=[0]*256
for c,p in enumerate(lut):inv[p]=c
body=raw[:offset]+bytes(new).translate(bytes(inv));result=body+(sum(body)&0xffffffff).to_bytes(4,'little')
p=parse(result);assert p[:4]==(h,start,size,offset) and p[4].translate(bytes(lut))==new
changed=[start+i for i,(a,b) in enumerate(zip(old,new)) if a!=b];assert set(changed)<=set(a+9 for a in positions)|{0x7ff80,0x7ff81,0x7fffe,0x7ffff}
# Actual repository parser compatibility, without importing flasher.
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/nrdr-reference/openpilot/nrdr/tools/eps')
from rwd_format.x5a import x5a
fw=x5a(result);assert fw.keys==bytes.fromhex('010203')
dest=out/'39990-THR,A020_R2_IDENTITY_EXPERIMENTAL.rwd'
with dest.open('xb') as f:f.write(result)
report={'file':dest.name,'sha256':hashlib.sha256(result).hexdigest(),'bytes':len(result),'source_sha256':hashlib.sha256(raw).hexdigest(),'embedded_identity':'39990-THR,A020','identity_addresses':[hex(a) for a in positions],'header_preserved':True,'calibration_and_code_preserved':True,'changed_payload_addresses':[hex(a) for a in changed],'checksum_A':new[0x7ff80-start:0x7ff82-start].hex(),'checksum_C':new[-2:].hex(),'payload_sum':total(0x80000),'roundtrip_and_repository_parser':'PASS','status':'EXPERIMENTAL; identity edit and offline integrity verified; not flashed; prior emulator results apply to original R2 image hash, not a fresh full execution of this revision'}
(out/'THR_R2_identity_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
