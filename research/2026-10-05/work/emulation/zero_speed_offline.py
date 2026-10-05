"""In-memory threshold experiment only; emits no ROM or RWD."""
from pathlib import Path
import json,itertools
import sh2a_pcode as e
R=Path(__file__).resolve().parents[2];rom=(R/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes();rows=[]
for variant in ['baseline','bank1_zero_only']:
 image=bytearray(rom)
 if variant=='bank1_zero_only':image[0x57b00:0x57b02]=b'\0\0'
 e.load_rom(image)
 for bank,speed,permit,request,inhibit in itertools.product([1,2,7],[0,1,9,10,69,70,400,401],[0,1],[0,1],[0,1]):
  c=e.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc)
  # Exercise the isolated idle transition with clean synthetic monitors.
  c.writemem(0xfff82f35,1,1);ptr=0xfff8500c
  for off,val in [(0,0),(2,request),(4,0),(5,0),(6,inhibit),(7,permit)]:c.writemem(ptr+off,2 if off==0 else 1,val)
  c.run(0x72ddc,(ptr,speed,0,8868))
  state=c.readmem(0xfff82f35,1);marker=c.readmem(0xfff82f32,1)
  expected=request and not inhibit and (0<=speed<=400 if variant=='bank1_zero_only' and bank==1 else ((70 if bank==7 else 10)<=speed<=400))
  expected=bool(expected or (request and not inhibit and speed==0 and permit))
  assert (state==2)==expected,(variant,bank,speed,permit,request,inhibit,state,marker)
  assert not c.hooks
  rows.append(dict(variant=variant,bank=bank,speed_counts=speed,standstill_permit=permit,request=request,inhibit=inhibit,state=state,standstill_marker=marker))
O=R/'outputs/zero_speed_offline';O.mkdir(exist_ok=True);(O/'results.json').write_text(json.dumps({'scope':'Isolated 0x72DDC idle-to-ramp transition, synthetic clean RAM, R2 base ROM. Bank1 threshold changed only in host memory. No ROM/RWD written; no vehicle access.','case_count':len(rows),'cases':rows},indent=2));print('PASS',len(rows));print([r for r in rows if r['bank']==1 and r['speed_counts']==0 and r['request']==1 and r['inhibit']==0])
