from assemble_ff_inimage import *
import itertools
O=R/'outputs/odyssey_ff_operating_grid';O.mkdir(exist_ok=True)
rows=[]
for mode in ['baseline','ff8','combined8','mismatch']:
 b,h,m=build(0,0) if mode=='baseline' else build(16 if mode=='mismatch' else 8,8)
 if mode=='combined8':
  for bank in [1,2,3]:
   off=(bank-1)*0x300
   for main,ref,factor in [(0x57c82,0x67cac,.75),(0x57c5e,0x67c84,1.25)]:
    for i in range(9):
     value=round(int.from_bytes(b[main+off+2*i:main+off+2*i+2],'big',signed=True)*factor)
     for a in [main+off+2*i,ref+off+2*i]:b[a:a+2]=value.to_bytes(2,'big',signed=True)
   b[0x57bd2+off:0x57bd4+off]=(308).to_bytes(2,'big')
 em.load_rom(b)
 for bank,schedule,rate,weights in itertools.product([1,3,7],[-2176,0,512,2176],[-320,0,320],[(16384,0,16384),(0,16384,16384),(8192,8192,8192)]):
  c=em.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc)
  for a,v in zip([0xfff82f60,0xfff82f62,0xfff82f64],weights):c.writemem(a,2,v)
  c.writemem(0xfff82fb8,2,rate);ticks=[]
  for command,feedback in [(0,0),(400,2000),(1024,2000),(-1024,-2000),(-400,-2000),(0,0)]:
   c.writemem(0xfff82fec,2,command);c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484));c.run(0x742c0,(feedback,0xfff82ff8,0xfff8a48c))
   for i,p in enumerate([0xfff82fc0,0xfff83004,0xfff8a498]):c.writemem(0x1000f000+4*i,4,p)
   c.run(0x7435c,(schedule,0xfff82fa0,0xfff82ff8,0xfff82ff0));out=em.signed(c.readmem(0xfff83074,2),2)
   c.run(0x6b010,(0xfff8a498,));ticks.append(dict(command=command,feedback=feedback,out=out,flags=c.readmem(0xfff8a5de,4)))
  rows.append(dict(mode=mode,bank=bank,schedule=schedule,rate=rate,weights=weights,ticks=ticks))
 print(mode,'done',flush=True)
(O/'results.json').write_text(json.dumps(rows,indent=2))
