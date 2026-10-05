from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()))
paths={'stock':R/'work/eps_rwd_publish/eps_tools/stock_39990-THR-A020.rwd','v4':Path('/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd')}
roms={};out={'files':{}}
for n,p in paths.items():
 raw=p.read_bytes();f=x5a(raw);roms[n]=bytes(f.firmware_blocks[0]['start'])+f.firmware_encrypted[0].translate(lut);out['files'][n]={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()}
d=roms['v4'];u=lambda a:int.from_bytes(d[a:a+4],'big');w=lambda b,a:int.from_bytes(b[a:a+2],'big',signed=True)
out['literals']={hex(a):hex(u(a)) for a in [0x742a8,0x742ac,0x742b0,0x742b4,0x74348,0x7434c,0x74350,0x74354,0x74358,0x748bc,0x748c0,0x74b48,0x74b4c,0x74b50,0x74b5c,0x74b60,0x74b64,0x74f30,0x74f38,0x74f3c,0x74f40]}
out['banks']=[]
for bank in range(1,8):
 off=(bank-1)*0x300
 out['banks'].append({'bank':bank,**{n:{'curve':[w(b,0x57bc0+off+2*i) for i in range(9)],'minimum_field':w(b,0x57b00+off),'D_limit':w(b,u(0x74b48)+off),'P_limit':w(b,u(0x74b5c)+off),'combined_limit':w(b,u(0x74b60)+off),'D_curve':[w(b,u(0x748c0)+off+2*i) for i in range(9)],'P_curve':[w(b,u(0x74b50)+off+2*i) for i in range(9)]} for n,b in roms.items()}})
out['controller_code_equal']=roms['stock'][0x7415c:0x74c9c]==d[0x7415c:0x74c9c]
p=R/'outputs/dual_ecu_reconstruction/odyssey_evidence.json';p.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
