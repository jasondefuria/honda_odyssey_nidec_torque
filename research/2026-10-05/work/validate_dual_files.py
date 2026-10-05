from pathlib import Path
import hashlib,json,sys,ast
root=Path(__file__).resolve().parents[1];out=root/'outputs'
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/nrdr-reference/openpilot/nrdr/tools/eps')
from rwd_format.x5a import x5a
lut=bytes(json.loads((root/'work/tla-decrypt-lookup.json').read_text()))
def parse(b):
 assert b[:3]==b'Z\r\n';i=3;headers=[]
 for _ in range(6):
  count=b[i];i+=1;vs=[]
  for _ in range(count):
   length=b[i];i+=1;assert i+length<=len(b);vs.append(b[i:i+length]);i+=length
  headers.append(vs)
 a=int.from_bytes(b[i:i+4],'big');n=int.from_bytes(b[i+4:i+8],'big');i+=8
 assert i+n+4==len(b);assert int.from_bytes(b[-4:],'little')==sum(b[:-4])&0xffffffff
 return headers,a,n,i,b[i:i+n]
ns={};tree=ast.parse((root/'work/uds_review/eps-update.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('get_seed_secret','_normalize_app_id')],type_ignores=[]),'pure_matching','exec'),ns)
reports=[]
for name,parent,digest in [('39990-THR-A020_STOCK_DUAL_ID.rwd',root/'work/imported/39990-THR-A020_stock_pure.rwd','90cb1d23d8a27f4c45d52fcbc0a6f08813fb2ae87a0c2f9069f552edd7715edb'),('39990-THR,A020_R2_DUAL_ID_EXPERIMENTAL.rwd',out/'39990-THR,A020_R2_IDENTITY_EXPERIMENTAL.rwd','7086b01cf9c78b4a094662d8f9f0c9fb915d1ea497d90d56f21c0224c986b9b8')]:
 b=(out/name).read_bytes();assert hashlib.sha256(b).hexdigest()==digest;h,a,n,i,p=parse(b);ph,pa,pn,pi,pp=parse(parent.read_bytes())
 assert (a,n)==(pa,pn)==(0xc000,0x74000) and p==pp
 assert h[:3]==ph[:3] and h[5]==ph[5]==[bytes.fromhex('010203')]
 assert h[3]==[b'39990-THR-A020\0\0',b'39990-THR,A020\0\0'] and h[4]==[bytes.fromhex('011101121120')]*2
 fw=x5a(b);assert fw.firmware_encrypted[0]==p
 for identity in h[3]:assert ns['get_seed_secret'](fw,identity)==h[4][0]
 try:ns['get_seed_secret'](fw,b'39990-TG7-A060')
 except RuntimeError:pass
 else:raise AssertionError('unrelated match')
 d=p.translate(lut);w=lambda end:sum(int.from_bytes(d[j:j+2],'big') for j in range(0,end,2))&65535
 assert w(0x73f80)==int.from_bytes(d[0x73f80:0x73f82],'big') and w(len(d))==0
 assert d[:2]==bytes.fromhex('4837') and d[0x73ffa:0x73ffc]==bytes.fromhex('b7c8')
 inv=bytes(lut.index(v) for v in range(256));assert d.translate(inv)==p
 # Verify decoded candidate against independently stored stock plus explicit manifest.
 expected=bytearray((root/'work/firmware/user.bin').read_bytes())
 if 'R2_' in name:
  for patch in json.loads((out/'THR_R2_patch_manifest.json').read_text())['patch_words']:
   adr=int(patch['address'],16);assert int.from_bytes(expected[adr:adr+2],'big')==patch['old'];expected[adr:adr+2]=patch['new'].to_bytes(2,'big')
  for k in range(14):
   adr=0x5eb37+k*0x46;assert expected[adr:adr+14]==b'39990-THR-A020';expected[adr:adr+14]=b'39990-THR,A020'
  total=lambda end:sum(int.from_bytes(expected[j:j+2],'big') for j in range(0xc000,end,2))&65535
  expected[0x7ff80:0x7ff82]=total(0x7ff80).to_bytes(2,'big');expected[-2:]=((-total(0x7fffe))&65535).to_bytes(2,'big')
 assert d==expected[a:a+n]
 rejected=[]
 for label,damaged in [('truncated',b[:-1]),('extra_byte',b+b'\0'),('payload_bitflip',b[:i]+bytes([b[i]^1])+b[i+1:])]:
  try:parse(damaged)
  except AssertionError:rejected.append(label)
  else:raise AssertionError('accepted '+label)
 reports.append({'file':name,'sha256':digest,'size':len(b),'status':'PASS_OFFLINE_VALIDATION','payload_byte_identical_to_parent':True,'independent_payload_reconstruction':True,'both_identities_match':True,'unrelated_identity_rejected':True,'encryption_key_values':1,'checksum_A':d[0x73f80:0x73f82].hex(),'checksum_C':d[-2:].hex(),'word_sum':w(len(d)),'negative_tests_rejected':rejected})
(out/'THR_dual_files_independent_validation.json').write_text(json.dumps({'files':reports,'scope':'Offline parsing, exact byte reconstruction and integrity only. No new boot emulation or live ECU activity.'},indent=2)+'\n');print(json.dumps(reports,indent=2))
