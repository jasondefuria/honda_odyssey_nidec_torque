from pathlib import Path
import json
import sh2a_pcode as e
R=Path(__file__).resolve().parents[2];rom=(R/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes();rows=[]
for variant in ['baseline','bank1_zero_only']:
 im=bytearray(rom)
 if variant=='bank1_zero_only':im[0x57b00:0x57b02]=b'\0\0'
 e.load_rom(im)
 for permit in [0,1]:
  for speed in [0,1,10,401]:
   c=e.CPU();c.writemem(0xfff82f04,4,0);c.run(0x720dc);ptr=0xfff8500c;c.writemem(0xfff82f35,1,1);c.writemem(ptr+2,1,1);c.writemem(ptr+7,1,permit)
   c.run(0x72ddc,(ptr,0,0,8868));initial=c.readmem(0xfff82f35,1)
   if initial==2:c.run(0x73060,(ptr,speed,0,8868))
   rows.append(dict(variant=variant,permit=permit,next_speed=speed,initial_state=initial,state=c.readmem(0xfff82f35,1),substate=c.readmem(0xfff82f34,1),marker=c.readmem(0xfff82f32,1),visited_ramp_out=0x7346c in c.visited))
(R/'outputs/zero_speed_offline/release.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
