"""Offline state dispatcher/ramp tests; no writable firmware artifacts."""
from pathlib import Path
import json,hashlib
import sh2a_pcode as e
R=Path(__file__).resolve().parents[2];original=(R/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes();results=[]
def state(c):return {'state':c.readmem(0xfff82f35,1),'path':c.readmem(0xfff82f37,1),'R':c.readmem(0xfff82f64,2),'W':c.readmem(0xfff82f60,2),'marker':c.readmem(0xfff82f32,1)}
def init(bank):
 c=e.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc);c.writemem(0xfff86e83,1,1);c.run(0x73458);c.writemem(0xfff8500e,1,1);return c

def tick(c,speed,reset=0):
 c.writemem(0x1000f000,4,reset);c.run(0x72a44,(0xfff8500c,speed,0,8868));c.run(0x73852);assert not c.hooks
for variant in ['baseline','bank1_zero_only']:
 im=bytearray(original)
 if variant=='bank1_zero_only':im[0x57b00:0x57b02]=b'\0\0'
 e.load_rom(im)
 for bank,speed in [(1,0),(1,10),(2,0),(2,10),(7,0),(7,70)]:
  c=init(bank);trans=[];prev=None
  for t in range(1030):
   tick(c,speed);s=state(c)
   key=(s['state'],s['path'])
   if key!=prev:trans.append({'tick':t,**s});prev=key
  end=state(c);c.writemem(0xfff8500e,1,0)
  for t in range(1030):tick(c,speed)
  results.append({'variant':variant,'test':'engage_release','bank':bank,'speed':speed,'transitions':trans,'engaged':end,'released':state(c)})
 fault_speed=0 if variant=='bank1_zero_only' else 10
 for fault,address,value in [('system',0xfff830ec,1),('monitor3',0xfff82f0f,3),('inhibit',0xfff85012,1),('config_off',0xfff86e83,0)]:
  c=init(1)
  for _ in range(1030):tick(c,fault_speed)
  before=state(c);c.writemem(address,1,value);seq=[]
  for _ in range(4):tick(c,fault_speed);seq.append(state(c))
  results.append({'variant':variant,'test':fault,'speed':fault_speed,'before':before,'after':seq})
 # Synthetic live change of bank selector: not proof of real bank-selection policy.
 for target in [2,7]:
  c=init(1)
  for _ in range(1030):tick(c,fault_speed)
  before=state(c);c.writemem(0xfff82f04,4,(target-1)*0x180)
  for _ in range(4):tick(c,fault_speed)
  results.append({'variant':variant,'test':'synthetic_bank_switch','target':target,'speed':fault_speed,'before':before,'after':state(c)})
 print(variant,'complete',flush=True)
O=R/'outputs/zero_speed_offline';(O/'extended.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(original).hexdigest(),'scope':'Real dispatcher 72A44 and ramp 73852 with synthetic RAM and call cadence; only bank1 minimum changed in memory. No full boot, peripherals, monitor production or physical plant. Bank changes directly inject selector, without running a bank selection policy.','results':results},indent=2));print(json.dumps(results,indent=2))
