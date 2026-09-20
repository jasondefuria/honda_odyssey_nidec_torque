from sh2a_pcode import CPU,ROM
from pathlib import Path
import zlib,json,hashlib,time
started=time.time();c=CPU();ctx=0xfff8e000;lst=ctx+0x100;expected_ptr=ctx+0x200;start=0xc000;length=0x74000
crc=zlib.crc32(ROM[start:start+length]);fields=[1<<24,lst,start,length,expected_ptr,0,0x4ed0,0xffff0000]
for i,v in enumerate(fields):c.writemem(ctx+4*i,4,v)
c.writemem(lst+4,4,start);c.writemem(lst+8,4,length);c.writemem(expected_ptr,4,crc)
reads=0;bytes_read=0
last=start

def read(cpu):
 global reads,bytes_read,last
 src,dst,n=[cpu.getreg('r'+str(i)) for i in (4,5,6)]
 assert src==last and 0<n<=64
 for i in range(n):cpu.writemem(dst+i,1,cpu.readmem(src+i,1))
 cpu.setreg('r0',n);reads+=1;bytes_read+=n;last=src+n
c.hooks[0xffff0000]=read
result,steps=c.run(0x4fe8,(ctx,),limit=40000000)
assert result==0 and c.readmem(ctx+20,4)==crc and bytes_read==length
out={'rom_sha256':hashlib.sha256(ROM).hexdigest(),'routine':'0x4FE8','start':hex(start),'length':hex(length),'crc32':hex(crc),'return':result,'read_calls':reads,'bytes_read':bytes_read,'instructions':steps,'elapsed_seconds':time.time()-started,'scope':'Original range wrapper on full ROM range C000..80000 with a synthetic one-range selection and expected CRC computed independently by zlib; modeled full-success read callback. This verifies chunking and arithmetic across the full range, not actual descriptor provenance or programming acceptance.'}
Path('outputs/odyssey_crc_rom_range_execution.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
