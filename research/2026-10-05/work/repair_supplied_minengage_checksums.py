"""Repair only existing runtime CRC and dependent checksums; no calibration edits."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
source=Path('/Users/jasondefuria/Downloads/mod25xv3-39990-THR_A020-minengage0-banks1-3.rwd')
raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='2d63d6c8aedd543eb0f71473db8e7dbf148ff874bbf44054c37acb4a787f0ef2'
fw=x5a(raw);assert fw.firmware_blocks==[{'start':0xc000,'length':0x74000}]
lut=bytes(json.loads((ROOT/'work/tla-decrypt-lookup.json').read_text()));assert len(set(lut))==256
old=fw.firmware_encrypted[0].translate(lut);new=bytearray(old);base=0xc000
# The format holds one payload followed by the four-byte container checksum.
offset=len(raw)-4-len(old)
def crc(data):
 c=0xffffffff
 for byte in data:
  c^=byte<<24
  for _ in range(8):c=((c<<1)^(0x04c11db7 if c&0x80000000 else 0))&0xffffffff
 return c^0xffffffff
def word_sum(data):return sum(int.from_bytes(data[i:i+2],'big') for i in range(0,len(data),2))&0xffff
assert int.from_bytes(old[0x6ff7c-base:0x6ff80-base],'big')==0x6956dafd
value=crc(old[0x60000-base:0x6ff60-base]);assert value==0xda5b0744
new[0x6ff7c-base:0x6ff80-base]=value.to_bytes(4,'big')
new[0x7ff80-base:0x7ff82-base]=word_sum(new[:0x7ff80-base]).to_bytes(2,'big')
new[-2:]=((-word_sum(new[:-2]))&0xffff).to_bytes(2,'big')
inv=bytes(lut.index(i) for i in range(256));body=raw[:offset]+bytes(new).translate(inv)
result=body+(sum(body)&0xffffffff).to_bytes(4,'little')
parsed=x5a(result);decoded=parsed.firmware_encrypted[0].translate(lut)
assert decoded==new and parsed.firmware_blocks==fw.firmware_blocks
assert result[:offset]==raw[:offset]
changed=[base+i for i,(a,b) in enumerate(zip(old,decoded)) if a!=b]
allowed=set(range(0x6ff7c,0x6ff80))|set(range(0x7ff80,0x7ff82))|set(range(0x7fffe,0x80000))
assert set(changed)<=allowed
checks=[]
for a in [0x40000,0x60000]:
 stored=int.from_bytes(decoded[a+0xff7c-base:a+0xff80-base],'big');computed=crc(decoded[a-base:a+0xff60-base]);assert stored==computed
 checks.append({'slot':hex(a+0xff7c),'stored':f'{stored:08X}','computed':f'{computed:08X}','pass':True})
assert word_sum(decoded)==0
assert int.from_bytes(decoded[0x7ff80-base:0x7ff82-base],'big')==word_sum(decoded[:0x7ff80-base])
assert int.from_bytes(result[-4:],'little')==sum(result[:-4])&0xffffffff
out=ROOT/'outputs/minengage0_checksum_fixed';out.mkdir(exist_ok=True)
dest=out/'mod25xv3-39990-THR_A020-minengage0-banks1-3-checksums-fixed.rwd'
with dest.open('xb') as f:f.write(result)
assert dest.read_bytes()==result
report={'file':str(dest),'sha256':hashlib.sha256(result).hexdigest(),'source_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(result),'runtime_crc_algorithm':'CRC-32/BZIP2','runtime_crc_checks':checks,'checksum_A':decoded[0x7ff80-base:0x7ff82-base].hex(),'checksum_C':decoded[-2:].hex(),'container_checksum':hex(int.from_bytes(result[-4:],'little')),'payload_word_sum':word_sum(decoded),'changed_payload_addresses':[hex(a) for a in changed],'header_unchanged':True,'all_non_checksum_payload_bytes_unchanged':True,'source_unchanged':source.read_bytes()==raw,'scope':'Offline checksum repair and byte verification only; no ECU flash or runtime acceptance test.'}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
