from sh2a_pcode import CPU,ROM
from pathlib import Path
Path(__file__).resolve().parent.joinpath("results").mkdir(exist_ok=True)
import json,hashlib
ident=b'THRC0';record=bytearray(b'\x55\xaa'+ident+ident+bytes(v^255 for v in ident)+b'\xaa\x55'+b'\0'*5)
assert len(record)==24
rows=[]
for flipped in [None]+list(range(192)):
 c=CPU();r=record.copy()
 if flipped is not None:r[flipped//8]^=1<<(flipped%8)
 for i,v in enumerate(r):c.writemem(0xfff83f1c+i,1,v)
 result,steps=c.run(0x17704)
 loaded=bytes(c.ram[0x1f58:0x1f5d]);enable=c.readmem(0xfff86e83,1)
 good=flipped is None or flipped//8>=19
 assert loaded==(ident if good else bytes(5)),(flipped,loaded)
 assert enable==int(good),(flipped,enable)
 rows.append({'flipped_bit':flipped,'routine_return':result,'marker_flag':c.readmem(0xfff85349,1),'loaded_coding_hex':loaded.hex(),'can_assist_enable':enable,'coding_ram_after':bytes(c.ram[0x3f1c:0x3f34]).hex()})
Path(str(Path(__file__).resolve().parent / 'results') + '/odyssey_coding_record_execution.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'scope':'Original 17704 and full variant loader with synthetic valid THRC0 coding then all 192 individual bit flips of its 24-byte RAM record; auxiliary calibration RAM zero. No EEPROM access or real coding changes.','cases':rows,'passed':len(rows)},indent=2)+'\n')
from collections import Counter
print(Counter((x['routine_return'],x['marker_flag'],x['can_assist_enable']) for x in rows))
