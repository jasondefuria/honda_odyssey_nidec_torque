from sh2a_pcode import CPU,signed,ROM
from pathlib import Path
import json,time,hashlib
from curve_oracle import calibration,evaluate
import sys
started=time.time();results=json.loads(Path("work/monitor_execution_progress.json").read_text()) if "--resume" in sys.argv else []
for bank in range(len(results),7):
 c=CPU();off=bank*0x300;c.writemem(0x1000f000,4,1)
 c.run(0x306ce,(0x67bc4+off,0x67bd6+off,0xfff8a574,9));c.writemem(0xfff82f04,4,off//2)
 xs,ys,limit,slopes=calibration(bank)
 for i,v in enumerate(slopes):assert c.readmem(0xfff8a574+i*4,4)==(v&0xffffffff)
 inst0=c.steps
 for raw in range(-32768,32768):
  cl,val,sv,ideal=evaluate(raw,xs,ys,limit,slopes)
  for i,v in enumerate((raw,cl,val,sv)):c.writemem(0xfff8a484+i*2,2,v)
  c.run(0x6acc4,(0xfff8a484,))
  assert c.readmem(0xfff8a5da,2)==0,(bank,raw,'fault')
  assert c.readmem(0xfff8a622,6)==0,(bank,raw,'disagreement')
  if (raw+32768)%8192==8191:print(json.dumps({'bank':bank+1,'inputs_completed':raw+32769,'elapsed_seconds':round(time.time()-started,1)}),flush=True)
 results.append({'bank':bank+1,'input_count':65536,'instructions_executed':c.steps-inst0,'mismatch_counters_nonzero':False,'monitor_fault_flags':0})
 Path('work/monitor_execution_progress.json').write_text(json.dumps(results,indent=2))
Path('outputs/odyssey_monitor_execution_verification.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'method':'Ghidra SH-2A SLEIGH p-code execution of monitor 6ACC4 with original slope initializer 306CE; snapshots generated from independently evaluated split fixed-point main calibration curve for every signed 16-bit input. No peripherals, interrupts, timing or physical plant modeled.','resumed_pass_elapsed_seconds':time.time()-started,'banks':results},indent=2)+'\n')
print('COMPLETE',time.time()-started,flush=True)
