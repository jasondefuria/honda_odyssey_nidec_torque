from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a

def split(b):
 assert b[:3]==b'Z\r\n'
 assert int.from_bytes(b[-4:],'little')==sum(b[:-4])&0xffffffff
 i=3;h=[]
 for _ in range(6):
  count=b[i];i+=1;v=[]
  for _ in range(count):
   n=b[i];i+=1;v.append(b[i:i+n]);i+=n
  h.append(v)
 return h,i
ref=Path('/Users/jasondefuria/Downloads/39990-THR-A020_pure_stock_A010-A020.rwd').read_bytes();rh,ri=split(ref)
assert rh[3]==[b'39990-THR-A020\0\0',b'39990-THR-A010\0\0']
out=ROOT/'outputs/corrected_A010_A020_headers';out.mkdir(exist_ok=True);reports=[]
for name in ['stock_39990-THR-A020.rwd','mod25xv1-39990-THR,A020.rwd']:
 src=Path('/Users/jasondefuria/Downloads/firmware_mod')/name;b=src.read_bytes();h,i=split(b)
 body=ref[:ri]+b[i:-4];new=body+(sum(body)&0xffffffff).to_bytes(4,'little')
 dest=out/name;dest.write_bytes(new);nh,ni=split(new);a=x5a(b);c=x5a(new)
 assert nh==rh and new[ni:-4]==b[i:-4]
 assert a.firmware_encrypted==c.firmware_encrypted and a.firmware_blocks==c.firmware_blocks and a.keys==c.keys
 lut=bytes(json.loads((ROOT/'work/tla-decrypt-lookup.json').read_text()));d=c.firmware_encrypted[0].translate(lut)
 assert sum(int.from_bytes(d[k:k+2],'big') for k in range(0,len(d),2))&65535==0
 reports.append({'file':str(dest),'sha256':hashlib.sha256(new).hexdigest(),'header_matches_reference':True,'payload_unchanged':True,'outer_checksum_valid':True,'payload_word_sum':0,'payload_identity_counts':{s:d.count(s.encode()) for s in ['39990-THR-A010','39990-THR-A020','39990-THR,A020']}})
(out/'validation.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))
