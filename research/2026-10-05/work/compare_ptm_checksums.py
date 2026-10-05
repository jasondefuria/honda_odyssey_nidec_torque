from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()))
def crc(data):
 c=0xffffffff
 for v in data:
  c^=v<<24
  for _ in range(8):c=((c<<1)^(0x04c11db7 if c&0x80000000 else 0))&0xffffffff
 return c^0xffffffff
def ws(data):return sum(int.from_bytes(data[i:i+2],'big') for i in range(0,len(data),2))&65535
rows=[]
for name,path in [('v4',Path('/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd')),('PTM',R/'outputs/odyssey_ptm_candidate/PTM-39990-THR,A020-EXPERIMENTAL.rwd')]:
 raw=path.read_bytes();f=x5a(raw);assert f.firmware_blocks==[{'start':0xc000,'length':0x74000}];d=bytes(0xc000)+f.firmware_encrypted[0].translate(lut);checks=[]
 for start in [0x40000,0x60000]:
  a=start+0xff7c;stored=int.from_bytes(d[a:a+4],'big');computed=crc(d[start:start+0xff60]);checks.append(dict(name=f'CRC {start:05X}–{start+0xff5f:05X}',address=hex(a),stored=f'{stored:08X}',computed=f'{computed:08X}',passed=stored==computed))
 for label,a,computed in [('Application A',0x7ff80,ws(d[0xc000:0x7ff80])),('Application C',0x7fffe,(-ws(d[0xc000:0x7fffe]))&65535)]:
  stored=int.from_bytes(d[a:a+2],'big');checks.append(dict(name=label,address=hex(a),stored=f'{stored:04X}',computed=f'{computed:04X}',passed=stored==computed))
 stored=int.from_bytes(raw[-4:],'little');computed=sum(raw[:-4])&0xffffffff;checks.append(dict(name='RWD container',stored=f'{stored:08X}',computed=f'{computed:08X}',passed=stored==computed))
 rows.append(dict(name=name,file=str(path),sha256=hashlib.sha256(raw).hexdigest(),checks=checks,payload_word_sum=f'{ws(d[0xc000:]):04X}',all_pass=all(c['passed'] for c in checks) and ws(d[0xc000:])==0))
(R/'outputs/odyssey_ptm_candidate/checksum_comparison.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
