from pathlib import Path
import sys,json,random,hashlib,types
R=Path(__file__).resolve().parents[1];O=R/'outputs/odyssey_feedforward_verification';O.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'work/emulation'),str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps')]
import sh2a_pcode as helperemu
from rwd_format.x5a import x5a
# Separate instrumented emulator, callback immediately before the named instruction.
# Does not patch firmware or alter the original emulator implementation.
src=(R/'work/emulation/sh2a_pcode.py').read_text().replace("end,ops=compile_block(self.pc);i=0;target=None;self.unique={}","\n   if hasattr(self, 'observer'): self.observer(self)\n   end,ops=compile_block(self.pc);i=0;target=None;self.unique={}")
em=types.ModuleType('instrumented');exec(compile(src,'offline_feedforward_instrumentation','exec'),em.__dict__)
raw=Path('/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd').read_bytes();f=x5a(raw);lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));rom=bytes(0xc000)+f.firmware_encrypted[0].translate(lut);em.load_rom(rom)
rows=[]
for gain in [0,8,16,32,45]:
 for bank in [1,3,7]:
  for command in [-1024,-400,0,400,1024]:
   for feedback in [-2000,0,2000]:
    c=em.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc)
    for a,v in [(0xfff82f60,16384),(0xfff82f62,0),(0xfff82f64,16384)]:c.writemem(a,2,v)
    c.writemem(0xfff82fec,2,command);c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484));target=em.signed(c.readmem(0xfff82ff6,2),2);observations=[]
    def inject(cpu):
     if cpu.pc==0x74aa2:
      before=em.signed(cpu.getreg('r2'),4);ff=(target*gain)>>10;after=max(-32767,min(32767,before+ff));cpu.setreg('r2',after);observations.append(dict(before=before,ff=ff,after=after))
    c.observer=inject;ticks=[]
    for tick in range(4):
     c.run(0x742c0,(feedback,0xfff82ff8,0xfff8a48c))
     for i,p in enumerate([0xfff82fc0,0xfff83004,0xfff8a498]):c.writemem(0x1000f000+4*i,4,p)
     c.run(0x7435c,(0,0xfff82fa0,0xfff82ff8,0xfff82ff0));out=em.signed(c.readmem(0xfff83074,2),2);scaled=em.signed(c.readmem(0xfff83076,2),2)
     c.run(0x6b010,(0xfff8a498,));ticks.append(dict(out=out,scaled=scaled,flags=c.readmem(0xfff8a5de,4)))
    assert len(observations)==4
    rows.append(dict(gain=gain,bank=bank,command=command,feedback=feedback,target=target,injections=observations,ticks=ticks))
 print('Completed injection gain',gain,flush=True)
# Broader original-instruction verification of the isolated signed product/shift helper.
helper=bytes.fromhex('254f001ae1f6401c000b0009');helperemu.load_rom(bytes(0x100)+helper)
rng=random.Random(530);targets=sorted(set([-32768,-32767,-12160,-1024,-1,0,1,1024,12160,32766,32767]+[rng.randint(-32768,32767) for _ in range(120)]));cases=[]
for t in targets:
 for g in [0,8,16,32,45]:
  c=helperemu.CPU();v,_=c.run(0x100,(t,g));got=helperemu.signed(v,4);assert got==(t*g)>>10;cases.append(dict(target=t,gain=g,actual=got))
result=dict(source_sha256=hashlib.sha256(raw).hexdigest(),method='Synthetic r2 addition at 0x74AA2, original downstream controller and monitor instructions; NOT a firmware trampoline',rows=rows,helper_cases=cases,helper_matches=True)
(O/'results.json').write_text(json.dumps(result,indent=2));print('Helper cases',len(cases))
