from sh2a_pcode import CPU,ROM
from curve_oracle import calibration,evaluate
from pathlib import Path
Path(__file__).resolve().parent.joinpath("results").mkdir(exist_ok=True)
import hashlib,json
rows=[]
for bank in range(7):
 for field in range(4):
  for bit in range(16):
   c=CPU();off=bank*0x300;c.writemem(0x1000f000,4,1)
   c.run(0x306ce,(0x67bc4+off,0x67bd6+off,0xfff8a574,9));c.writemem(0xfff82f04,4,off//2)
   raw=400;cl,mag,val,_=evaluate(raw,*calibration(bank));snapshot=[raw,cl,mag,val];bad=snapshot.copy();bad[field]^=1<<bit
   records=[]
   for step in range(5):
    current=bad if step<3 else snapshot
    for j,v in enumerate(current):c.writemem(0xfff8a484+2*j,2,v)
    c.run(0x6acc4,(0xfff8a484,))
    records.append({'counters':[c.readmem(0xfff8a622+2*j,2) for j in range(3)],'flag_byte':c.readmem(0xfff8a5db,1)})
   rows.append({'bank':bank+1,'corrupted_field_word':field,'flipped_bit':bit,'steps':records})
assert all(x['steps'][0]['flag_byte']==0 and x['steps'][1]['flag_byte']==0 and x['steps'][2]['flag_byte'] and x['steps'][3]['counters']==[0,0,0] and x['steps'][4]['flag_byte']==x['steps'][2]['flag_byte'] for x in rows)
Path(str(Path(__file__).resolve().parent / 'results') + '/odyssey_monitor_fault_injection.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'scope':'Directed snapshot corruption at raw input 400, each of 16 bits in each of 4 snapshot words, all 7 banks. Three consecutive corrupted snapshots followed by two correct snapshots. Original monitor and initializer, synthetic RAM, no scheduling.','cases':rows},indent=2)+'\n')
from collections import Counter
print(Counter((x['corrupted_field_word'],x['steps'][2]['flag_byte'],x['steps'][4]['flag_byte']) for x in rows))
