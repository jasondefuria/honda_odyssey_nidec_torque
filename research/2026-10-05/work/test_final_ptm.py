from pathlib import Path
import sys,json,hashlib,itertools,math
R=Path(__file__).resolve().parents[1];O=R/'outputs/ptm_final_emulator';O.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'work/emulation'),str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps')]
import sh2a_pcode as em
from rwd_format.x5a import x5a
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()))
paths={'stock':R/'work/eps_rwd_publish/eps_tools/stock_39990-THR-A020.rwd','v4':Path('/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd'),'PTM':R/'outputs/odyssey_ptm_candidate/PTM-39990-THR,A020-EXPERIMENTAL.rwd'}
roms={};hashes={}
for k,p in paths.items():
 raw=p.read_bytes();f=x5a(raw);roms[k]=bytes(f.firmware_blocks[0]['start'])+f.firmware_encrypted[0].translate(lut);hashes[k]=hashlib.sha256(raw).hexdigest()
assert hashes['PTM']=='1c45356e7dffd85a416d79ae262641756f2bdc37e99fe9f0422981f1a4e033f1'
def init(bank):
 c=em.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc);return c
def tick(c,bank,cmd,fb,schedule=0,rate=0,weights=(16384,0,16384),corrupt=None):
 for a,v in zip([0xfff82f60,0xfff82f62,0xfff82f64],weights):c.writemem(a,2,v)
 c.writemem(0xfff82fb8,2,rate);c.writemem(0xfff82fec,2,cmd);c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484));c.run(0x742c0,(fb,0xfff82ff8,0xfff8a48c))
 for i,p in enumerate([0xfff82fc0,0xfff83004,0xfff8a498]):c.writemem(0x1000f000+4*i,4,p)
 c.run(0x7435c,(schedule,0xfff82fa0,0xfff82ff8,0xfff82ff0))
 out=em.signed(c.readmem(0xfff83074,2),2);target=em.signed(c.readmem(0xfff82ff6,2),2)
 if corrupt:
  offset,width,delta=corrupt;addr=0xfff8a498+offset;c.writemem(addr,width,c.readmem(addr,width)+delta)
 c.run(0x6b010,(0xfff8a498,));c.run(0x6acc4,(0xfff8a484,))
 lim=int.from_bytes(em.ROM[0x57bda+(bank-1)*0x300:0x57bdc+(bank-1)*0x300],'big')
 return dict(out=out,target=target,pd_flags=c.readmem(0xfff8a5de,4),curve_flags=c.readmem(0xfff8a5da,2),within_limit=abs(out)<=lim,steps=c.steps)
results={};errors=[]
for name,rom in roms.items():
 em.load_rom(rom);rows=[]
 for bank,schedule,rate,weights in itertools.product(range(1,8),[-2176,0,2176],[-320,320],[(16384,0,16384),(8192,8192,8192)]):
  c=init(bank);ts=[]
  try:
   for cmd,fb in [(0,0),(55,1),(400,2000),(1774,32767),(-1774,-32768),(-400,-2000),(-1,-1),(0,0)]:ts.append(tick(c,bank,cmd,fb,schedule,rate,weights))
  except Exception as ex:errors.append(dict(stage='grid',image=name,bank=bank,error=repr(ex)))
  rows.append(dict(bank=bank,schedule=schedule,rate=rate,weights=weights,ticks=ts))
 results[name]=rows;print('Grid completed',name,flush=True)
(O/'grid.json').write_text(json.dumps(dict(hashes=hashes,results=results,errors=errors),indent=2))
trans=[]
for name,rom in roms.items():
 em.load_rom(rom)
 for a,b in itertools.permutations(range(1,8),2):
  c=init(a);ts=[]
  try:
   for _ in range(3):ts.append(tick(c,a,400,1000))
   # Deliberate retained-state selector change: not a claim about real mode-switch sequencing.
   c.writemem(0xfff82f04,4,(b-1)*0x180)
   for _ in range(3):ts.append(tick(c,b,400,1000))
  except Exception as ex:errors.append(dict(stage='transition',image=name,banks=[a,b],error=repr(ex)))
  trans.append(dict(image=name,from_bank=a,to_bank=b,ticks=ts))
 print('Transitions completed',name,flush=True)
(O/'transitions.json').write_text(json.dumps(trans,indent=2))
em.load_rom(roms['PTM']);faults=[]
for bank,kind,corrupt in itertools.product(range(1,8),['sum','P','target','output'],[None]):
 off={'sum':(0x60,4,1),'P':(0x5c,2,100),'target':(0x6,2,1024),'output':(0x70,2,100)}[kind];c=init(bank);ts=[]
 for _ in range(8):ts.append(tick(c,bank,400,0,corrupt=off))
 faults.append(dict(bank=bank,kind=kind,ticks=ts,detected=any(t['pd_flags'] for t in ts)))
(O/'faults.json').write_text(json.dumps(faults,indent=2));print('Faults completed',flush=True)
# Assumed first-order dimensionless plant: y follows gain*u with delay. No time/torque units.
plant=[]
for image,plantgain,alpha,delay in itertools.product(['v4','PTM'],[2.,6.],[.05,.2],[0,3]):
 em.load_rom(roms[image]);c=init(1);y=0.;q=[0.]*delay;trace=[]
 for n in range(100):
  cmd=400 if 10<=n<65 else 0;r=tick(c,1,cmd,round(max(-32768,min(32767,y))));drive=r['out']
  if delay:q.append(drive);drive=q.pop(0)
  y+=alpha*(plantgain*drive-y);trace.append(dict(sample=n,feedback=y,**r))
 plant.append(dict(image=image,assumed_gain=plantgain,assumed_alpha=alpha,delay_updates=delay,trace=trace))
 print('Assumed plant',image,plantgain,alpha,delay,flush=True)
(O/'assumed_plant.json').write_text(json.dumps(plant,indent=2));(O/'errors.json').write_text(json.dumps(errors,indent=2));print('All suites completed',flush=True)
