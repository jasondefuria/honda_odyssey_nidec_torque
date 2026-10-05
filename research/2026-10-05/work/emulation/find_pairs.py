import sys,json,hashlib
from pathlib import Path
import sh2a_pcode as e
root=Path(__file__).resolve().parents[2]
lookup=bytes(json.loads((root/'work/tla-decrypt-lookup.json').read_text()))
def image(name):
 b=(root/'outputs'/name).read_bytes();i=3
 for _ in range(6):
  n=b[i];i+=1
  for _ in range(n):l=b[i];i+=1+l
 a=int.from_bytes(b[i:i+4],'big');n=int.from_bytes(b[i+4:i+8],'big');i+=8
 assert a==0xc000 and n==0x74000
 rom=bytearray((root/'work/firmware/user.bin').read_bytes());rom[a:a+n]=b[i:i+n].translate(lookup)
 return bytes(rom),hashlib.sha256(b).hexdigest()
images={k:image(v) for k,v in [('stock','39990-THR-A020_STOCK_DUAL_ID.rwd'),('r2','39990-THR,A020_R2_DUAL_ID_EXPERIMENTAL.rwd')]}
targets=[0,256,512,1024,1536,2048,2560,3072,3584,4096];rows=[]
for bank in [1,2,3,7]:
 caches={}
 def setup(name):
  e.load_rom(images[name][0]);c=e.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc);return c
 def run(initial,cmd):
  c=e.CPU();c.ram[:]=initial.ram;c.stack[:]=initial.stack
  for a,v in [(0xfff82f60,16384),(0xfff82f62,0),(0xfff82f64,16384),(0xfff8500c,cmd),(0xfff8500a,60),(0xfff80016,0)]:c.writemem(a,2,v)
  vals=[]
  for _ in range(5):
   c.run(0x7276a,(0xfff8500c,0));ret,_=c.run(0x74c9c,(0,0));vals.append(e.signed(ret,4))
   for fn,arg in [(0x6a700,0xfff8a454),(0x6acc4,0xfff8a484),(0x6b010,0xfff8a498),(0x6be98,0xfff8a50c)]:c.run(fn,(arg,))
   c.run(0x4d358,(0,0,0xfff8e000));assert c.readmem(0xfff8e000,1)==0 and c.readmem(0xfff8a5cc,24)==0
  assert vals[-1]==vals[-2] and not c.hooks
  return vals
 initial=setup('stock');stock={cmd:run(initial,cmd) for cmd in targets}
 initial=setup('r2')
 def get(cmd):
  if cmd not in caches:caches[cmd]=run(initial,cmd)
  return caches[cmd]
 samples=[get(c)[-1] for c in range(0,4097,128)];assert samples==sorted(samples)
 for cmd in targets:
  target=stock[cmd][-1];lo,hi=0,4096
  while lo<hi:
   mid=(lo+hi)//2
   if get(mid)[-1]<target:lo=mid+1
   else:hi=mid
  best=min({max(0,lo-1),lo},key=lambda c:(abs(get(c)[-1]-target),c))
  neg=run(initial,-best)
  row=dict(bank=bank,stock_command=cmd,r2_command=best,stock_ticks=stock[cmd],r2_ticks=get(best),residual=get(best)[-1]-target,negative_r2_ticks=neg)
  rows.append(row)
 print('bank',bank,[(r['stock_command'],r['r2_command'],r['stock_ticks'][-1],r['residual']) for r in rows if r['bank']==bank],flush=True)
report=dict(scope='Offline synthetic state: full weights, zero driver input and feedback/base assist, speed 60 internal counts, fresh initialized state per command, five calls. Commands injected at FFF8500C; not verified CAN-to-input conversion or physical torque. Bisection with coarse monotonicity check; not exhaustive global nearest-pair proof.',rwd_sha256={k:v[1] for k,v in images.items()},pairs=rows)
(root/'outputs/R2_stock_equivalent_internal_pairs.json').write_text(json.dumps(report,indent=2))
