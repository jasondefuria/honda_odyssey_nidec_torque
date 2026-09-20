from sh2a_pcode import CPU,ROM
from pathlib import Path
import json,hashlib
rows=[]
for request in [0,1]:
 c=CPU();c.hooks[0xa7b2]=lambda cpu:None;c.hooks[0xa79c]=lambda cpu:None
 c.hooks[0xabbc]=lambda cpu:cpu.setreg('r0',request)
 reached=[]
 def stop(cpu):reached.append(hex(cpu.pc));cpu.setreg('pr',0xfffffffe)
 c.hooks[0x8898]=stop;c.hooks[0x884c]=stop
 c.run(0x8814)
 assert reached==['0x8898']
 rows.append({'synthetic_flash_request_result':request,'header_word':hex(int.from_bytes(ROM[0xc000:0xc002],'big')),'tail_word_read':hex(int.from_bytes(ROM[0x7fff8:0x7fffa],'big')),'sum':hex(c.getreg('r13')),'branch_destination':reached[0]})
out={'rom_sha256':hashlib.sha256(ROM).hexdigest(),'scope':'Original segment starting8814, hardware initialization helpers A7B2/A79C replaced with register-preserving returns, ABBC flash-request check supplied 0/1. Stops at8898 or884C. This is a conditional boot-path experiment, not execution of an actual reset or all boot hardware.','vector_at_8000':hex(int.from_bytes(ROM[0x8000:0x8004],'big')),'tail_8_bytes':ROM[0x7fff8:].hex(),'header_complement':hex(int.from_bytes(ROM[0xc000:0xc002],'big')^65535),'complement_location_in_this_dump':'0x7FFFA','cases':rows}
Path('outputs/odyssey_boot_marker_execution.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
