from sh2a_pcode import CPU,ROM
from pathlib import Path
Path(__file__).resolve().parent.joinpath("results").mkdir(exist_ok=True)
import json,zlib,hashlib
rows=[]
for ranges in [[],[(17,101)],[(0,64),(128,99)],[(0,256)]]:
 for corrupt in [False,True]:
  c=CPU();ctx=0xfff8e000;lst=ctx+0x100;expected_ptr=ctx+0x200;data=bytes(range(256));base=0xfff8c000
  for i,v in enumerate(data):c.writemem(base+i,1,v)
  selected=b''.join(data[start:start+length] for start,length in ranges)
  expected=zlib.crc32(selected)^int(corrupt)
  fields=[len(ranges)<<24,lst,base,len(data),expected_ptr,0,0x4ed0,0xffff0000]
  for i,v in enumerate(fields):c.writemem(ctx+4*i,4,v)
  for i,(start,length) in enumerate(ranges):
   c.writemem(lst+12*i,4,0);c.writemem(lst+12*i+4,4,base+start);c.writemem(lst+12*i+8,4,length)
  c.writemem(expected_ptr,4,expected);reads=[]
  def read(cpu):
   src,dst,n=[cpu.getreg('r'+str(i)) for i in (4,5,6)]
   reads.append([src-base,n])
   for i in range(n):cpu.writemem(dst+i,1,cpu.readmem(src+i,1))
   cpu.setreg('r0',n)
  c.hooks[0xffff0000]=read
  result,steps=c.run(0x4fe8,(ctx,),limit=1000000)
  all_crc=c.readmem(ctx+20,4)
  assert result==(2 if corrupt else 0),(ranges,corrupt,result)
  assert all_crc==zlib.crc32(data),(ranges,hex(all_crc))
  rows.append({'ranges':ranges,'expected_crc_corrupted':corrupt,'return':result,'selected_crc':hex(zlib.crc32(selected)),'whole_crc':hex(all_crc),'read_calls':reads,'instructions':steps})
Path(str(Path(__file__).resolve().parent / 'results') + '/odyssey_crc_range_execution.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'routine':'0x4FE8','scope':'Original routine and CRC helpers with synthetic descriptor/input RAM and a modeled successful read callback; no programming entry point or flash acceptance tested.','cases':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
