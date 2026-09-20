from pathlib import Path
import json,hashlib
r=Path('work/pilot-a060');s=(r/'39990-TG7-A060-STOCK.rwd.decoded.bin').read_bytes();m=(r/'39990-TG7-A060-2X (2019 Honda Pilot).decoded.bin').read_bytes();base=0x10000
u=lambda b,a:int.from_bytes(b[a-base:a-base+2],'little')
rows=[];covered=set()
for bank in range(5):
 b=0x1e5aa+bank*0xe82;t=b+0x426
 curve_s=[u(s,t+2*i) for i in range(256)];curve_m=[u(m,t+2*i) for i in range(256)]
 ids=[i for i,(x,y) in enumerate(zip(curve_s,curve_m)) if x!=y]
 for a in range(t,t+512):
  if s[a-base]!=m[a-base]:covered.add(a)
 fields=[]
 for off,size,role in [(0xc34,2,'upper bound before /256'),(0xc78,1,'proportional clamp'),(0xc79,1,'combined correction clamp'),(0xc7a,2,'final correction clamp'),(0xc81,1,'status acceptance lower threshold')]:
  a=b+off;fields.append({'offset':hex(off),'address':hex(a),'stock':int.from_bytes(s[a-base:a-base+size],'little'),'modified':int.from_bytes(m[a-base:a-base+size],'little'),'role':role})
  covered.update(a+i for i in range(size) if s[a+i-base]!=m[a+i-base])
 a=0x2bdb8+bank*0x278;covered.add(a)
 rows.append({'ascending_address_bank':bank+1,'variant_selector':5-bank,'base':hex(b),'table':hex(t),'changed_indices':[min(ids),max(ids)],'samples':[{'index':i,'stock':curve_s[i],'modified':curve_m[i]} for i in [0,65,66,128,192,255]],'fields':fields,'multi_signal_threshold_address':hex(a)})
covered.update(range(0x2cffc,0x2d000))
actual={base+i for i,(x,y) in enumerate(zip(s,m)) if x!=y};assert actual==covered
out={'changed_bytes':len(actual),'all_changed_bytes_accounted_for_by_regions':True,'banks':rows,'rounding_helper':'sign(x)*floor((abs(x)+2**(n-1))/2**n) for positive shift n','caveat':'Region coverage is complete; full behavioral and hardware tracing is not.'}
Path('outputs/pilot_trace_verification.json').write_text(json.dumps(out,indent=2)+'\n')
lines=Path('work/pilot-disassembly.txt').read_text().splitlines();ranges=[(0x363de,0x36608),(0x36b06,0x36cd4),(0x36f24,0x36f78),(0x37506,0x37540),(0x3b018,0x3b048),(0x3b352,0x3b39e),(0x3b6a4,0x3b6c2),(0x31ba0,0x31bf4),(0x32a50,0x32a7c),(0x33722,0x3374c),(0x3e82a,0x3e844)]
selected=['V850 LE32 disassembly. gp-relative addresses intentionally retained. Some SLEIGH relative-call displays exceed 32 bits; do not treat linear listings as a complete CFG.']
for a,z in ranges:
 selected.append(f'\nWINDOW {a:X}..{z:X}')
 selected.extend(l for l in lines if a<=int(l.split()[0],16)<z)
Path('outputs/pilot_reader_disassembly.txt').write_text('\n'.join(selected)+'\n')
print('All',len(actual),'changed bytes covered. Samples:',rows[0]['samples'])
