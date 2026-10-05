import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as e
root=Path(__file__).resolve().parents[2];out=root/'outputs';boot=(out/'ccp_capture/THR_boot_0000_1FFF.bin').read_bytes();r=(root/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes();rom=boot+r[8192:];e.load_rom(rom)
lut=json.loads((root/'work/tla-decrypt-lookup.json').read_text());report={'method':'Captured boot prefix plus existing R2 image; synthetic RAM; SH-2A research interpreter. No hardware or CAN.'}
# Actual byte transform, with the three key operations separately reconstructed from disassembly.
vals=[]
for c in range(256):
 cpu=e.CPU();cpu.writemem(0xfff88000,1,((c^1^2)+3)&255);cpu.run(0xa00,(0xfff88000,));vals.append(cpu.readmem(0xfff88000,1))
assert vals==lut;report['actual_0a00_with_reconstructed_key_stage_matches_all_256']=True
cpu=e.CPU();cpu.run(0x11be,(0xdeadbeef,));assert cpu.getreg('r0')==0;report['11be_return']=0
report['range_tests']=[]
for start,length in [(0xc000,0x74000),(0xc000,16),(0xbfff,16),(0x80000,16),(0xc000,0x74001)]:
 cpu=e.CPU();cpu.run(0x1f1c,(start,length,0xc000,0x74000));report['range_tests'].append({'start':hex(start),'length':hex(length),'return':cpu.getreg('r0')})
# Exercise entry points until completion or explicit unsupported hardware boundary.
for name,addr in [('decrypt',0x14ce),('checksum',0x1306),('ff01',0x11c2)]:
 cpu=e.CPU();p=0xfff88000;buf=0xfff88100
 cpu.writemem(0xfff80c58,2,4)
 for j,v in enumerate([1,2,3]):cpu.writemem(0xfff80c51+j,1,v)
 if name=='decrypt':
  cpu.writemem(p,4,buf);cpu.writemem(p+4,2,256)
  for c in range(256):cpu.writemem(buf+c,1,c)
 elif name=='checksum':cpu.writemem(p+4,4,0xc000);cpu.writemem(p+8,4,0x74000)
 else:
  cpu.writemem(0xfff80c98,4,0xc000);cpu.writemem(0xfff80c9c,4,0x74000);cpu.writemem(0xfff80ca0,1,2)
 try:
  cpu.run(addr,(p,0),limit=20000000);res={'status':'completed','return':cpu.getreg('r0'),'steps':cpu.steps}
  if name=='decrypt':res['all_256_match']=all(cpu.readmem(buf+i,1)==lut[i] for i in range(256))
 except Exception as ex:res={'status':'blocked','error':str(ex),'pc':hex(cpu.pc),'steps':cpu.steps}
 report[name]=res
(out/'THR_boot_execution.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
