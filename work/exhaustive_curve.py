from sh2a_pcode import CPU,signed,ROM
from pathlib import Path
import json,hashlib,time
from curve_oracle import calibration,evaluate
import sys
started=time.time();results=json.loads(Path("work/curve_execution_progress.json").read_text()) if "--resume" in sys.argv else []
for bank in range(len(results),7):
 c=CPU();off=bank*0x300
 c.writemem(0x1000f000,4,1)
 c.run(0x306ce,(0x57bae+off,0x57bc0+off,0xfff83168,9))
 c.writemem(0xfff82f04,4,off//2)
 xs,ys,limit,slopes=calibration(bank)
 quantization_differences=0;max_difference=0
 for i,v in enumerate(slopes):assert c.readmem(0xfff83168+i*4,4)==(v&0xffffffff)
 digest=hashlib.sha256();inst0=c.steps
 for raw in range(-32768,32768):
  c.writemem(0xfff82fec,2,raw)
  c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484))
  out=signed(c.readmem(0xfff82ff6,2),2)
  cl,mag,want,ideal=evaluate(raw,xs,ys,limit,slopes)
  quantization_differences+=want!=ideal;max_difference=max(max_difference,abs(want-ideal))
  assert out==want,(bank,raw,out,want)
  assert c.readmem(0xfff82ff0,8)==c.readmem(0xfff8a484,8),(bank,raw,'mirror')
  digest.update((out&65535).to_bytes(2,'big'))
  if (raw+32768)%8192==8191: print(json.dumps({'bank':bank+1,'inputs_completed':raw+32769,'elapsed_seconds':round(time.time()-started,1)}),flush=True)
 results.append({'bank':bank+1,'input_count':65536,'output_sha256':digest.hexdigest(),'instructions_executed':c.steps-inst0,'axis':xs,'ordinates':ys,'limit':limit,'different_from_ideal_linear_count':quantization_differences,'max_difference_from_ideal_linear':max_difference,'fixed_point_slopes':slopes})
 Path('work/curve_execution_progress.json').write_text(json.dumps(results,indent=2))
Path('outputs/odyssey_curve_execution_verification.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'method':'Ghidra SH-2A SLEIGH p-code execution via a local interpreter, compared against independently evaluated split fixed-point interpolation at every signed 16-bit input. ROM is immutable. No timing, interrupts, peripherals or physical plant modeled.','resumed_pass_elapsed_seconds':time.time()-started,'banks':results},indent=2)+'\n')
print('COMPLETE',time.time()-started,flush=True)
