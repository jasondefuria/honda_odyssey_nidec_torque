"""Offline integrated-function tests, no RWD/BIN output or hardware access."""
from pathlib import Path
import json,hashlib,time
import sh2a_pcode as e
R=Path(__file__).resolve().parents[2];rom=(R/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes();O=R/'outputs/zero_speed_offline';rows=[]
def tick(c):
 c.writemem(0x1000f000,4,0);c.run(0x72a44,(0xfff8500c,0,0,8868));c.run(0x73852)
 c.run(0x7276a,(0xfff8500c,0));ret,_=c.run(0x74c9c,(0,0))
 for fn,arg in [(0x6a700,0xfff8a454),(0x6acc4,0xfff8a484),(0x6b010,0xfff8a498),(0x6be98,0xfff8a50c)]:c.run(fn,(arg,))
 c.run(0x4d358,(0,0,0xfff8e000));assert not c.hooks
 return {'state':c.readmem(0xfff82f35,1),'path':c.readmem(0xfff82f37,1),'authority':c.readmem(0xfff82f64,2),'fade':e.signed(c.readmem(0xfff82fec,2),2),'controller':e.signed(c.readmem(0xfff83074,2),2),'mixer':e.signed(ret,4),'diagnostic':c.readmem(0xfff8e000,1),'monitor_bytes':c.readmem(0xfff8a5cc,24)}
def clone(c):
 n=e.CPU();n.ram[:]=c.ram;n.stack[:]=c.stack;return n
for variant in ['baseline','bank1_zero_only']:
 b=bytearray(rom)
 if variant=='bank1_zero_only':b[0x57b00:0x57b02]=b'\0\0'
 e.load_rom(b);c=e.CPU();c.writemem(0xfff82f04,4,0);c.run(0x720dc);c.writemem(0xfff86e83,1,1);c.run(0x73458);c.writemem(0xfff8500e,1,1);c.writemem(0xfff8500c,2,4096)
 samples=[];monitor_nonzero=0
 for t in range(1030):
  z=tick(c);monitor_nonzero+=int(bool(z['diagnostic'] or z['monitor_bytes']))
  if t in [0,1,2,100,512,1023,1024,1029]:samples.append({'tick':t,**z})
 rows.append({'variant':variant,'case':'engagement','ticks':1030,'monitor_nonzero_ticks':monitor_nonzero,'samples':samples});print(variant,'engagement',z,flush=True)
 tests=[('inhibit',0xfff85012,1,1,8),('driver767',0xfff80016,2,767,8),('driver768',0xfff80016,2,768,8),('driver_negative768',0xfff80016,2,-768,8),('system_fault',0xfff830ec,1,1,8),('monitor3',0xfff82f0f,1,3,8),('config_off',0xfff86e83,1,0,8),('request_off',0xfff8500e,1,0,1030),('bank2',0xfff82f04,4,0x180,1030),('bank7',0xfff82f04,4,6*0x180,1030),('reverse_command',0xfff8500c,2,-4096,8),('zero_command',0xfff8500c,2,0,8)]
 for name,addr,size,value,n in tests:
  c2=clone(c);c2.writemem(addr,size,value);samples=[];bad=0;peak=0
  for t in range(n):
   z=tick(c2);bad+=int(bool(z['diagnostic'] or z['monitor_bytes']));peak=max(peak,abs(z['mixer']))
   if t<8 or t==n-1:samples.append({'tick':t,**z})
  rows.append({'variant':variant,'case':name,'ticks':n,'peak_abs_mixer':peak,'monitor_nonzero_ticks':bad,'samples':samples})
  print(variant,name,'last',z,'monitor_ticks',bad,flush=True)
(O/'combined.json').write_text(json.dumps({'scope':'Synthetic speed=0, bank1 baseline versus in-memory minimum zero. Dispatcher/ramp + preprocessing/fade/PD/mixer + four consistency monitors and aggregation. Zero feedback/base assist. No full boot, CAN parsing, hardware, actual bank-selection policy or motor plant. Injected flags do not test fault detection generation.','base_rom_sha256':hashlib.sha256(rom).hexdigest(),'cases':rows},indent=2))
