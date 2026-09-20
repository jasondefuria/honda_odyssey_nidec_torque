from sh2a_pcode import CPU,ROM
from pathlib import Path
Path(__file__).resolve().parent.joinpath("results").mkdir(exist_ok=True)
import json,hashlib
rows=[]
for gate in range(256):
 c=CPU();c.writemem(0xfff89362,2,0x8000);c.writemem(0xfff861ed,1,gate);c.setreg('r1',0xfff89350)
 c.hooks[0x4b8c6]=lambda cpu:cpu.setreg('pr',0xfffffffe)
 c.run(0x4b658)
 processed=c.readmem(0xfff89378,2)
 assert processed==(0 if gate&0xc0 else 0x8000),(gate,processed)
 c.run(0x7541e);fault=c.readmem(0xfff830ec,1)
 assert fault==int(not gate&0xc0),(gate,fault)
 rows.append({'gate_byte':gate,'processed_fault_word':processed,'can_fault':fault})
Path(str(Path(__file__).resolve().parent / 'results') + '/odyssey_fault_publication_execution.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'scope':'Original segment 4B658..4B8C6 exclusive, supplying r1=FFF89350 and a fresh synthetic stack; original EF flag only; original 2DE7A and 7541E run without substitutions. Exhaustive over the gate byte, not all diagnostic RAM states or timing.','cases':rows,'passed':len(rows)},indent=2)+'\n')
print('Passed',len(rows),'gate-byte cases')
