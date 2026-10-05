from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];p=Path('/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/pilot-a060')
lut=json.loads((root/'work/tla-decrypt-lookup.json').read_text())
def parse(path,pilot):
 b=path.read_bytes();assert b[:3]==b'Z\r\n';i=3;heads=[]
 for _ in range(6):
  c=b[i];i+=1;h=[]
  for _ in range(c):n=b[i];i+=1;h.append(b[i:i+n].hex());i+=n
  heads.append(h)
 a=int.from_bytes(b[i:i+4],'big');n=int.from_bytes(b[i+4:i+8],'big');i+=8
 assert len(b)==i+n+4 and sum(b[:-4])&0xffffffff==int.from_bytes(b[-4:],'little')
 d=bytes(((((v+1)^2)-3)&255) if pilot else lut[v] for v in b[i:i+n])
 return {'file':path.name,'sha256':hashlib.sha256(b).hexdigest(),'start':hex(a),'length':hex(n),'headers':heads,'container_checksum_valid':True},d
ms,s=parse(p/'39990-TG7-A060-STOCK.rwd',True);mt,t=parse(p/'39990-TG7-A060-2X (2019 Honda Pilot)',True);mr,r=parse(root/'outputs/39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd',False)
assert s==(p/'39990-TG7-A060-STOCK.bin').read_bytes()
assert r==(root/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes()[0xc000:]
checks={label:[sum(int.from_bytes(data[i:i+4],'little') for i in range(0,end,4))&0xffffffff for end in (0xa000,0x1d000,0x4ff00)] for label,data in [('pilot_stock',s),('pilot_2x',t)]}
rows=[]
for base in (0x21fb2,0x21130,0x202ae,0x1f42c,0x1e5aa):
 def word(data,off,n=2):return int.from_bytes(data[base+off-0x10000:base+off-0x10000+n],'little')
 rows.append({'base':hex(base),'curve_samples':[{'index':j,'stock':word(s,0x426+2*j),'modified':word(t,0x426+2*j)} for j in (0,65,66,128,192,255)],'limits':{name:[word(s,a,n),word(t,a,n)] for name,a,n in [('D',0xc77,1),('P',0xc78,1),('combined',0xc79,1),('final',0xc7a,2),('dynamic',0xc34,2),('status_threshold',0xc81,1)]}})
report={'files':[ms,mt,mr],'pilot_stock_decodes_exactly_to_raw':True,'pilot_changed_bytes':sum(x!=y for x,y in zip(s,t)),'pilot_cumulative_le32_checks':checks,'pilot_banks':rows,'trim_identity':'2019 Pilot source label; Elite trim not independently verified','method':'Fresh container decoding and raw table reads; functional roles from existing Pilot disassembly reports; no new Pilot emulation'}
(root/'outputs/THR_R2_vs_Pilot.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'files':[ms,mt,mr],'checks':checks,'bank':rows[0],'diff':report['pilot_changed_bytes']},indent=2))
