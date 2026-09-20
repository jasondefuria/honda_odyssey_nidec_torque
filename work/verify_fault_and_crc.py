from sh2a_pcode import CPU,ROM,signed
from pathlib import Path
import hashlib,json,zlib,random
rows=[]
for bit in range(176):
 c=CPU();p=0xfff89366+bit//8;c.writemem(p,1,1<<(bit%8))
 c.run(0x7541e);a=c.readmem(0xfff830ec,1)
 v,_=c.run(0x77260)
 rows.append({'byte_offset':bit//8,'bit':bit%8,'can_assist_fault':a,'other_state_predicate':v})
mask1=[];mask2=[]
for j in range(22):
 mask1.append(sum(1<<r['bit'] for r in rows if r['byte_offset']==j and r['can_assist_fault']))
 mask2.append(sum(1<<r['bit'] for r in rows if r['byte_offset']==j and r['other_state_predicate']))
assert mask1[18]&128 and mask2[18]&128
states=[]
for bank in range(7):
 for state in range(1,6):
  c=CPU();c.writemem(0xfff82f04,4,bank*0x180);c.run(0x720dc)
  c.writemem(0xfff86e83,1,1);c.writemem(0xfff89378,2,0x8000);c.run(0x7541e)
  for p,v in [(0xfff82f35,state),(0xfff82f37,1)]:c.writemem(p,1,v)
  for p,v in [(0xfff82f60,16384),(0xfff82f62,0),(0xfff82f64,16384)]:c.writemem(p,2,v)
  transitions=[]
  for k in range(3):
   c.run(0x72a44,(0xfff8500c,1000,0,1000));c.run(0x73852)
   transitions.append({'state':c.readmem(0xfff82f35,1),'flags':list(c.ram[0x2f32:0x2f38]),'weights':[c.readmem(0xfff82f60+i*2,2) for i in range(3)]})
  states.append({'bank':bank+1,'initial_state':state,'transitions':transitions})
assert len(states)==35
assert all(x['transitions'][0]['weights']==[0,16384,0] for x in states)
# Original ROM CRC nibble table: four reflected rounds per entry.
poly=0xedb88320;tbl=[]
for i in range(16):
 r=i
 for _ in range(4):r=(r>>1)^(poly if r&1 else 0)
 tbl.append(r)
assert b''.join(x.to_bytes(4,'big') for x in tbl)==ROM[0x5698:0x56d8]
rng=random.Random(0xA020);cases=[b'',b'123456789',bytes(range(256)),bytes(rng.randrange(256) for _ in range(4096))];crcrows=[]
for data in cases:
 c=CPU();ctx=0xfff8e000;buf=0xfff8c000
 for i,v in enumerate(data):c.writemem(buf+i,1,v)
 c.writemem(ctx+4,1,1);c.run(0x4e86,(ctx,))
 assert c.readmem(ctx,4)==0xffffffff
 c.writemem(ctx+4,1,2);c.writemem(ctx+8,4,buf);c.writemem(ctx+12,2,len(data));c.writemem(ctx+16,4,0x4ed0)
 c.run(0x4e86,(ctx,),limit=300000)
 c.writemem(ctx+4,1,4);c.run(0x4e86,(ctx,))
 value=c.readmem(ctx,4);assert value==zlib.crc32(data),(len(data),hex(value),hex(zlib.crc32(data)))
 crcrows.append({'length':len(data),'sha256':hashlib.sha256(data).hexdigest(),'crc32':hex(value),'matches_zlib':True})
Path('outputs/odyssey_fault_state_execution.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'scope':'Offline SLEIGH p-code execution of original routines; zero-filled synthetic RAM with stated overrides, no scheduler, peripherals or vehicle dynamics. State scenarios use input structure FFF8500C zero, arguments speed-like values 1000, third argument 0; these are directed cases, not all operating conditions.','predicate_masks':{'7541E':bytes(mask1).hex(),'77260':bytes(mask2).hex()},'individual_bit_cases':rows,'directed_fault_states':states},indent=2)+'\n')
Path('outputs/odyssey_reflected_crc_verification.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'table_address':'0x5698','table_entries':16,'polynomial_reflected':hex(poly),'table_matches':True,'reader':'0x4E20','wrapper':'0x4E86','execution_cases':crcrows,'scope':'Original CRC helper and wrapper executed offline; callback 4ED0 is an actual ROM no-op. This does not validate complete programming or flashing acceptance.'},indent=2)+'\n')
print('masks',bytes(mask1).hex(),bytes(mask2).hex());print('state2',states[1]);print('CRC',crcrows)
