from pathlib import Path
import sys,json,hashlib,ast
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
lut=ast.literal_eval(next(n.value for n in ast.parse((R/'work/eps_tool_pinned.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='default_decrypt_lookup_table' for t in n.targets)))
trans=bytes(lut[i] for i in range(256));rom=[];records=[]
for name in ['39990-TRW-A020 (stock).rwd','ClarityMax-PTM.rwd']:
 raw=(Path('/Users/jasondefuria/Downloads')/name).read_bytes();f=x5a(raw);base=f.firmware_blocks[0]['start'];data=f.firmware_encrypted[0].translate(trans);d=bytes(base)+data;rom.append(d)
 records.append({'name':name,'sha256':hashlib.sha256(raw).hexdigest(),'blocks':f.firmware_blocks,'headers':[[repr(v.value) for v in h.values] for h in f.file_headers],'container_pass':True,'decoded_start':data[:16].hex(),'identities':{v:d.count(v.encode()) for v in ['39990-TRW-A020','39990-TRW,A020']},'BE16_payload_sum':hex(sum(int.from_bytes(data[i:i+2],'big') for i in range(0,len(data),2))&65535)})
a,b=rom;assert len(a)==len(b)
runs=[]
for i,(x,y) in enumerate(zip(a,b)):
 if x!=y:
  if runs and runs[-1][1]==i:runs[-1][1]+=1
  else:runs.append([i,i+1])

r={'files':records,'changed_bytes':sum(x!=y for x,y in zip(a,b)),'diff_runs':[{'address':hex(x),'stock':a[x:y].hex(),'ptm':b[x:y].hex()} for x,y in runs]}
(R/'outputs/clarity_ptm_comparison/comparison.json').write_text(json.dumps(r,indent=2));

def words(d,addr,n):return [int.from_bytes(d[i:i+2],'big') for i in range(addr,addr+n*2,2)]
def sum16(d):return sum(int.from_bytes(d[i:i+2],'big') for i in range(0,len(d),2))&65535
r['tables']=[{'row':i+1,'address':hex(0x1388e+i*18),'stock':words(a,0x1388e+i*18,9),'ptm':words(b,0x1388e+i*18,9)} for i in range(7)]
r['checks']=[{'A_stored':hex(words(d,0x4ff80,1)[0]),'A_computed':hex(sum16(d[0x4000:0x4ff80])),'C_stored':hex(words(d,0x4fffe,1)[0]),'C_computed':hex((-sum16(d[0x4000:0x4fffe]))&65535)} for d in rom]
r['other_words']=[{'address':hex(addr),'stock':words(a,addr,n),'ptm':words(b,addr,n)} for addr,n in [(0x13638,1),(0x1380a,1),(0x1390c,3),(0x13918,3),(0x139c0,3),(0x13ae0,9),(0x13af2,9),(0x13b04,9)]]
(R/'outputs/clarity_ptm_comparison/comparison.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:r[k] for k in ['tables','checks','other_words']},indent=2))
