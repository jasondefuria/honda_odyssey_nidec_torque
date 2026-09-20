from sh2a_pcode import CPU,signed,ROM
from pathlib import Path
import json,time,hashlib
started=time.time();c=CPU();payload=b'';results=[];sentinel=0x1234

def rx(cpu):
 assert cpu.getreg('r4')==22
 dest=cpu.getreg('r5')
 for i,v in enumerate(payload):cpu.writemem(dest+i,1,v)
 cpu.setreg('r0',1)
def stop(cpu):cpu.setreg('pr',0xfffffffe)
c.hooks={0x323b2:rx,0x146ca:stop,0x111e0:stop}
for condition in range(4):
 for request in range(2):
  for counter in range(4):
   digest=hashlib.sha256();count0=c.steps
   repeat=bool(condition&1);bad_crc=bool(condition&2)
   for raw in range(65536):
    arr=[raw>>8,raw&255,request<<7,0,counter<<4,0,0,0]
    nibble=(-26-sum((v>>4)+(v&15) for v in arr[:5]))&15
    arr[4]|=(nibble+int(bad_crc))&15;payload=bytes(arr)
    c.writemem(0xfff8519f,1,counter if repeat else ((counter+3)&3))
    c.writemem(0xfff850da,2,0)
    c.run(0x14618)
    assert c.readmem(0xfff85198,2)==raw
    assert c.readmem(0xfff8519a,1)==request
    assert c.readmem(0xfff8519f,1)==counter
    flags=c.readmem(0xfff850da,2)
    expected=(0x4042 if repeat else 0)|(0x2021 if bad_crc else 0)
    assert flags==expected,(condition,request,counter,raw,flags,expected)
    # Entry to accepted-command segment: preceding function fields supplied explicitly.
    c.writemem(0xfff850dd,1,0);c.writemem(0xfff8500c,2,sentinel)
    for p in range(0xfff8500e,0xfff85014):c.writemem(p,1,0)
    c.setreg('r9',0xfff850b0);c.setreg('r14',0xfff8500c);c.setreg('r0',0)
    c.run(0x1113e)
    accepted=c.readmem(0xfff8500c,2);req=c.readmem(0xfff8500e,1)
    assert accepted==(sentinel if condition else raw),(condition,raw,accepted)
    assert req==(0 if condition else request),(condition,raw,req)
    digest.update(accepted.to_bytes(2,'big')+bytes([req]))
   row={'condition':condition,'repeated_counter':repeat,'bad_checksum':bad_crc,'request_bit':request,'counter':counter,'raw_word_inputs':65536,'output_sha256':digest.hexdigest(),'instructions_executed':c.steps-count0}
   results.append(row)
   Path('work/can_execution_progress.json').write_text(json.dumps(results,indent=2))
   print(json.dumps({'completed_groups':len(results),'total_groups':32,'elapsed_seconds':round(time.time()-started,1)}),flush=True)
Path('outputs/odyssey_can_execution_verification.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'elapsed_seconds':time.time()-started,'total_cases':sum(x['raw_word_inputs'] for x in results),'method':'Offline SH-2A SLEIGH p-code. Execute original 14618 through 146CA (exclusive), substituting hardware receive 323B2 with a slot-22 payload provider. Execute original acceptance segment 1113E through 111E0 (exclusive), supplying r9, r14 and prior fields. Status postprocessing at 153C4 and timeout debounce are deliberately outside this experiment. No actual bus, peripheral, scheduler, interrupt or vehicle execution.','groups':results,'visited_pc_count':len(c.visited)},indent=2)+'\n')
print('COMPLETE',time.time()-started,flush=True)
