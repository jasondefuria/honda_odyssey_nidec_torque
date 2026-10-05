from pathlib import Path
import sys,json,hashlib,ast
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
lut=ast.literal_eval(next(n.value for n in ast.parse((R/'work/eps_tool_pinned.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='default_decrypt_lookup_table' for t in n.targets)))
trans=bytes(lut[i] for i in range(256));rom=[];records=[]
for name in ['stock-39990-TBA-A030.rwd','39990-TBA,A030-PTM.rwd']:
 raw=(Path('/Users/jasondefuria/Downloads')/name).read_bytes();f=x5a(raw);base=f.firmware_blocks[0]['start'];data=f.firmware_encrypted[0].translate(trans);d=bytes(base)+data;rom.append(d)
 records.append({'name':name,'sha256':hashlib.sha256(raw).hexdigest(),'blocks':f.firmware_blocks,'headers':[[repr(v.value) for v in h.values] for h in f.file_headers],'container_pass':True,'decoded_start':data[:16].hex(),'identities':{v:d.count(v.encode()) for v in ['39990-TBA-A030','39990-TBA,A030']},'BE16_payload_sum':hex(sum(int.from_bytes(data[i:i+2],'big') for i in range(0,len(data),2))&65535)})
a,b=rom;assert len(a)==len(b)
runs=[]
for i,(x,y) in enumerate(zip(a,b)):
 if x!=y:
  if runs and runs[-1][1]==i:runs[-1][1]+=1
  else:runs.append([i,i+1])
rows=[]
for kind,addr in [('torque',0x1379a),('filter',0x139ec)]:
 for row in range(7):
  off=addr+row*18
  rows.append({'kind':kind,'row':row+1,'address':hex(off),'stock':[int.from_bytes(a[i:i+2],'big') for i in range(off,off+18,2)],'ptm':[int.from_bytes(b[i:i+2],'big') for i in range(off,off+18,2)]})
r={'files':records,'changed_bytes':sum(x!=y for x,y in zip(a,b)),'diff_runs':[{'address':hex(x),'stock':a[x:y].hex(),'ptm':b[x:y].hex()} for x,y in runs],'candidate_tables':rows,'speed_word_13544':[int.from_bytes(d[0x13544:0x13546],'big') for d in rom]}
(R/'outputs/civic_ptm_comparison/comparison.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
extra=[]
for addr in [0x13716,0x13818,0x1381a,0x1381c]:
 extra.append({'address':hex(addr),'stock':int.from_bytes(a[addr:addr+2],'big'),'ptm':int.from_bytes(b[addr:addr+2],'big')})
checks=[]
for d in rom:
 def sum16(z):return sum(int.from_bytes(z[i:i+2],'big') for i in range(0,len(z),2))&65535
 checks.append({'A_stored':hex(int.from_bytes(d[0x4ff80:0x4ff82],'big')),'A_computed':hex(sum16(d[0x4000:0x4ff80])),'C_stored':hex(int.from_bytes(d[0x4fffe:0x50000],'big')),'C_computed':hex((-sum16(d[0x4000:0x4fffe]))&65535)})
r['additional_words']=extra;r['application_checks']=checks
r['additional_table']=[{'row':j+1,'address':hex(0x13ae8+j*18),'stock':[int.from_bytes(a[i:i+2],'big') for i in range(0x13ae8+j*18,0x13ae8+j*18+18,2)],'ptm':[int.from_bytes(b[i:i+2],'big') for i in range(0x13ae8+j*18,0x13ae8+j*18+18,2)]} for j in range(7)]
(R/'outputs/civic_ptm_comparison/comparison.json').write_text(json.dumps(r,indent=2))
print(json.dumps({'checks':checks,'additional_words':extra,'additional_table_example':r['additional_table'][0]},indent=2))
