from pathlib import Path
import sys,json,hashlib,re
R=Path(__file__).resolve().parents[1];O=R/'outputs/odyssey_ptm_no_bank7';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
source=Path('/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd');raw=source.read_bytes();manifest=json.loads((R/'outputs/odyssey_ff_no_bank7/review_patch_manifest.json').read_text());assert hashlib.sha256(raw).hexdigest()==manifest['source_sha256']
f=x5a(raw);assert f.firmware_blocks==[{'start':0xc000,'length':0x74000}]
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));assert len(set(lut))==256
old=bytes(0xc000)+f.firmware_encrypted[0].translate(lut);new=bytearray(old);allowed=set()
for ch in manifest['changes']:
 a=int(ch['address'],16);before=bytes.fromhex(ch['original']);after=bytes.fromhex(ch['replacement']);assert len(before)==len(after);assert new[a:a+len(before)]==before
 new[a:a+len(after)]=after;allowed.update(range(a,a+len(after)))
def crc(data):
 table=[]
 for v in range(256):
  c=v<<24
  for _ in range(8):c=((c<<1)^(0x04c11db7 if c&0x80000000 else 0))&0xffffffff
  table.append(c)
 c=0xffffffff
 for v in data:c=((c<<8)&0xffffffff)^table[((c>>24)^v)&255]
 return c^0xffffffff
assert crc(b'123456789')==0xfc891918
def ws(data):return sum(int.from_bytes(data[i:i+2],'big') for i in range(0,len(data),2))&65535
for a in [0x40000,0x60000]:new[a+0xff7c:a+0xff80]=crc(new[a:a+0xff60]).to_bytes(4,'big');allowed.update(range(a+0xff7c,a+0xff80))
new[0x7ff80:0x7ff82]=ws(new[0xc000:0x7ff80]).to_bytes(2,'big');new[-2:]=((-ws(new[0xc000:-2]))&65535).to_bytes(2,'big');allowed.update([0x7ff80,0x7ff81,0x7fffe,0x7ffff])
assert len(new)==0x80000;assert all(i in allowed for i in range(0xc000,0x80000) if new[i]!=old[i])
inv=bytes(lut.index(i) for i in range(256));offset=len(raw)-4-0x74000;body=raw[:offset]+bytes(new[0xc000:]).translate(inv);result=body+(sum(body)&0xffffffff).to_bytes(4,'little')
parsed=x5a(result);decoded=parsed.firmware_encrypted[0].translate(lut);assert decoded==new[0xc000:];assert result[:offset]==raw[:offset];assert parsed.firmware_blocks==f.firmware_blocks;assert ws(decoded)==0
checks=[]
for a in [0x40000,0x60000]:
 stored=int.from_bytes(decoded[a+0xff7c-0xc000:a+0xff80-0xc000],'big');computed=crc(decoded[a-0xc000:a+0xff60-0xc000]);assert stored==computed;checks.append(dict(address=hex(a+0xff7c),stored=hex(stored),computed=hex(computed),passed=True))
assert int.from_bytes(decoded[0x7ff80-0xc000:0x7ff82-0xc000],'big')==ws(decoded[:0x7ff80-0xc000])
assert int.from_bytes(result[-4:],'little')==(sum(result[:-4])&0xffffffff)
ids=sorted(set(m.group().decode() for m in re.finditer(rb'39990[-,]THR[-,]A0[0-9][0-9]',decoded)))
assert ids==sorted(set(m.group().decode() for m in re.finditer(rb'39990[-,]THR[-,]A0[0-9][0-9]',old)))
dest=O/'PTM-39990-THR,A020-NO-FF-BANK7-EXPERIMENTAL.rwd'
with dest.open('xb') as fp:fp.write(result)
assert dest.read_bytes()==result and source.read_bytes()==raw
sha=hashlib.sha256(result).hexdigest();(O/'SHA256SUMS').write_text(sha+'  '+dest.name+'\n')
report=dict(file=str(dest),sha256=sha,size=len(result),source_sha256=manifest['source_sha256'],profile='P75% D125% alpha308 Dlimit512 Plimit2048 combinedlimit2048 banks1-3; matched independent references; FF8/ref8 except bank7; inherited v4 curve and minimum-speed fields',embedded_identities=ids,header_unchanged=True,roundtrip_pass=True,patch_manifest_match=True,runtime_crc_checks=checks,checksum_A=new[0x7ff80:0x7ff82].hex(),checksum_C=new[-2:].hex(),container_checksum=hex(int.from_bytes(result[-4:],'little')),word_sum=ws(decoded),limitations=['Experimental candidate; not verified for ECU installation or vehicle use','Candidate code placement at0x75800/0x75900 has not been proven unused at runtime','No physical torque/stability calibration or hardware timing/stack validation','Feedforward disabled for bank7 in controller and independent monitor','Existing v4 low-speed settings retained'])
(O/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
