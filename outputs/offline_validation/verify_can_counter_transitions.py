from sh2a_pcode import CPU,ROM
from pathlib import Path
Path(__file__).resolve().parent.joinpath("results").mkdir(exist_ok=True)
import json,hashlib
c=CPU();payload=b'';rows=[]
def rx(cpu):
 assert cpu.getreg('r4')==22
 for i,v in enumerate(payload):cpu.writemem(cpu.getreg('r5')+i,1,v)
 cpu.setreg('r0',1)
c.hooks={0x323b2:rx,0x146ca:lambda cpu:cpu.setreg('pr',0xfffffffe)}
for old in range(4):
 for new in range(4):
  cases=0
  for raw in [0,1,1024,4096,32767,32768,65534,65535]:
   for request in range(2):
    arr=[raw>>8,raw&255,(request<<7)|0x55,0xa7,new<<4,0,0,0]
    correct=(-26-sum((v>>4)+(v&15) for v in arr[:5]))&15
    for check in range(16):
     arr[4]=(new<<4)|check;payload=bytes(arr)
     c.writemem(0xfff8519f,1,old);c.writemem(0xfff850da,2,0);c.run(0x14618)
     flags=c.readmem(0xfff850da,2);want=(0x4042 if old==new else 0)|(0x2021 if check!=correct else 0)
     assert flags==want,(old,new,raw,request,check,flags,want)
     assert c.readmem(0xfff85198,2)==raw and c.readmem(0xfff8519a,1)==request
     cases+=1
  rows.append({'previous_counter':old,'new_counter':new,'repeated_counter_flag':old==new,'cases':cases})
Path(str(Path(__file__).resolve().parent / 'results') + '/odyssey_can_counter_transition_execution.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'scope':'Original parser segment with slot-22 payload provider, all 16 old/new counter pairs, 8 raw values, both request values, every checksum nibble; byte 2 low bits=55 and byte 3=A7. No status postprocessing or scheduler.','cases':rows,'total_cases':sum(x['cases'] for x in rows)},indent=2)+'\n')
print('Passed',sum(x['cases'] for x in rows),'cases; only equal counter values set repeat flags')
