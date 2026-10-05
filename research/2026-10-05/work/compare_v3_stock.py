from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
paths=[R/'work/eps_rwd_publish/eps_tools/stock_39990-THR-A020.rwd',R/'outputs/mod25xv2_crc_fixed/mod25xv3-39990-THR,A020.rwd']
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));inv=bytes(lut.index(i) for i in range(256))
def crc(d):
 c=0xffffffff
 for b in d:
  c^=b<<24
  for _ in range(8):c=((c<<1)^(0x04c11db7 if c&0x80000000 else 0))&0xffffffff
 return c^0xffffffff
def sum16(d):return sum(int.from_bytes(d[i:i+2],'big') for i in range(0,len(d),2))&65535
def word(d,a):return int.from_bytes(d[a:a+2],'big')
records=[];roms=[];prefix=[]
for path in paths:
 raw=path.read_bytes();f=x5a(raw);assert f.firmware_blocks==[{'start':0xc000,'length':0x74000}]
 data=f.firmware_encrypted[0].translate(lut);d=bytes(0xc000)+data;roms.append(d);prefix.append(raw[:-len(data)-4])
 checks=[]
 for a in [0x40000,0x60000]:
  stored=int.from_bytes(d[a+0xff7c:a+0xff80],'big');computed=crc(d[a:a+0xff60]);checks.append({'check':f'CRC at {a+0xff7c:05X}','stored':f'{stored:08X}','computed':f'{computed:08X}','pass':stored==computed})
 for label,stored,computed in [('A',word(d,0x7ff80),sum16(d[0xc000:0x7ff80])),('C',word(d,0x7fffe),(-sum16(d[0xc000:0x7fffe]))&65535),('container',int.from_bytes(raw[-4:],'little'),sum(raw[:-4])&0xffffffff)]:checks.append({'check':label,'stored':hex(stored),'computed':hex(computed),'pass':stored==computed})
 assert all(c['pass'] for c in checks) and sum16(data)==0
 assert word(d,0xc000)==0x4837 and word(d,0x7fffa)==0xb7c8
 assert data.translate(inv)==f.firmware_encrypted[0]
 headers=[[v.value.hex() for v in h.values] for h in f.file_headers]
 records.append(dict(file=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),blocks=f.firmware_blocks,headers_hex=headers,checks=checks,payload_sum=sum16(data),marker_pair=['4837','B7C8'],cipher_roundtrip=True,identities={s:data.count(s.encode()) for s in ['39990-THR-A010','39990-THR-A020','39990-THR,A020']}))
s,m=roms;expected=bytearray(s)
patches=[x for x in json.loads((R/'outputs/THR_R2_patch_manifest.json').read_text())['patch_words'] if x['bank'] is not None]
for p in patches:
 a=int(p['address'],16);assert word(s,a)==p['old'] and word(m,a)==p['new'];expected[a:a+2]=p['new'].to_bytes(2,'big')
positions=[];start=0
while True:
 a=s.find(b'39990-THR-A020',start)
 if a<0:break
 positions.append(a);expected[a:a+14]=b'39990-THR,A020';start=a+14
for a,n in [(0x6ff7c,4),(0x7ff80,2),(0x7fffe,2)]:expected[a:a+n]=m[a:a+n]
assert bytes(expected)==m,'Unaccounted payload changes'
banks=[]
for b in range(1,8):
 delta=(b-1)*0x300
 banks.append({'bank':b,'main_different_bytes':sum(x!=y for x,y in zip(s[0x57b00+delta:0x57e00+delta],m[0x57b00+delta:0x57e00+delta])),'reference_different_bytes':sum(x!=y for x,y in zip(s[0x67b00+delta:0x67e00+delta],m[0x67b00+delta:0x67e00+delta])),'minimum_speed':[word(d,0x57b00+delta) for d in roms]})
r={'files':records,'header_bytes_identical':prefix[0]==prefix[1],'changed_payload_bytes':sum(a!=b for a,b in zip(s,m)),'all_changes_accounted_for':True,'identity_addresses':[hex(a) for a in positions],'calibration_patch_words':len(patches),'banks':banks,'scope':'Offline verification of both identified runtime CRCs, A/C, word sum, markers, container, format, roundtrip and complete byte diff; not full ECU runtime or physical steering validation.'}
o=R/'outputs/mod25xv3_stock_comparison';o.mkdir(exist_ok=True);(o/'comparison.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
