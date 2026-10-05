from pathlib import Path
import sys,json,hashlib,zipfile
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as em
root=Path(__file__).resolve().parents[2]
files=['user.bin','THR_A020_2p5_peak_BENCH_ONLY_UNVALIDATED.bin','THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin']
addresses=list(range(0x5fc00,0x5fdb4))+[0,0x1fff,0x2000,0xffff,0x10000,0x12345,0x1ffff,0x20000,0x3ffff,0x40000,0x5fbff,0x5fdb4,0xfff819c0]
results=[]
stock=(root/'work/firmware/user.bin').read_bytes()
for name in files:
 rom=(root/'work/firmware'/name).read_bytes();em.load_rom(rom);rows=[]
 for flag in (0,1):
  for addr in addresses:
   cpu=em.CPU();cpu.writemem(0xfff8429d,1,flag);cpu.run(0x37844,(0,addr))
   got=cpu.getreg('r0')
   expected=int.from_bytes(rom[addr&~3:(addr&~3)+4],'big') if 0x5fc00<=addr<0x5fdb4 else (0x50000|(addr&0xffff) if 0x10000<=addr<0x40000 and not flag else addr)
   assert got==expected,(name,flag,hex(addr),hex(got),hex(expected))
   rows.append({'flag':flag,'request':hex(addr),'resolved':hex(got)})
 results.append({'file':name,'sha256':hashlib.sha256(rom).hexdigest(),'passed':len(rows),'lookup_code_identical_to_stock':rom[0x37844:0x3787e]==stock[0x37844:0x3787e],'can_table_identical_to_stock':rom[0x3da90:0x3de90]==stock[0x3da90:0x3de90],'pointer_table_identical_to_stock':rom[0x5fc00:0x5fdb4]==stock[0x5fc00:0x5fdb4],'cases':rows})
can=[]
for idx in (1,33):
 a=0x3da90+16*idx;b=stock[a:a+16];can.append({'index':idx,'address':hex(a),'raw':b.hex(),'id':hex(int.from_bytes(b[4:6],'big')),'length':b[12],'direction':b[13]})
pointers=[{'entry':i,'address':hex(0x5fc00+4*i),'target':hex(int.from_bytes(stock[0x5fc00+4*i:0x5fc04+4*i],'big'))} for i in range(109)]
out={'scope':'Offline lookup routine only; no CAN, CCP handler, bootloader or physical torque validation','can_entries':can,'pointer_entries':pointers,'images':results}
(root/'outputs/THR_CCP_lookup_validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'can':can,'first':pointers[:2],'last':pointers[-1],'results':[{k:v for k,v in x.items() if k!='cases'} for x in results]},indent=2))
