import ast,json,hashlib
from pathlib import Path
root=Path('work/pilot-a060');o=Path('work/user.bin').read_bytes()
src=ast.parse(Path('work/nrdr-reference/openpilot/nrdr/tools/eps/check_rwd.py').read_text())
lut=next(ast.literal_eval(n.value) for n in src.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DECRYPT_LOOKUP' for t in n.targets))
meta=[];dec=[]
for name in ['39990-TG7-A060-STOCK.rwd','39990-TG7-A060-2X (2019 Honda Pilot)']:
 raw=(root/name).read_bytes();i=3;headers=[]
 for _ in range(6):
  c=raw[i];i+=1;h=[]
  for _ in range(c):
   n=raw[i];i+=1;h.append(raw[i:i+n].hex());i+=n
  headers.append(h)
 start=int.from_bytes(raw[i:i+4],'big');n=int.from_bytes(raw[i+4:i+8],'big');i+=8
 d=bytes(((((x+1)^2)-3)&255) for x in raw[i:i+n]);dec.append(d);(root/(name+'.decoded.bin')).write_bytes(d)
 meta.append({'name':name,'sha256':hashlib.sha256(raw).hexdigest(),'start':hex(start),'size':len(d),'headers':headers,'outer_checksum':sum(raw[:-4])&0xffffffff==int.from_bytes(raw[-4:],'little')})
s,t=dec;raw=(root/'39990-TG7-A060-STOCK.bin').read_bytes()
print('META',meta);print('raw equal',raw==s,'rawhash',hashlib.sha256(raw).hexdigest())
diffs=[i for i,(a,b) in enumerate(zip(s,t)) if a!=b];groups=[]
for i in diffs:
 if not groups or i>groups[-1][-1]+16:groups.append([i])
 else:groups[-1].append(i)
ranges=[{'start':hex(start+g[0]),'end':hex(start+g[-1]+1),'changed':len(g),'stock':s[g[0]:g[-1]+1].hex(),'wip':t[g[0]:g[-1]+1].hex()} for g in groups]
print('DIFFS',len(diffs));[print(r) for r in ranges]
match=[]
for a,z in [(0x3a128,0x3b128+2),(0x57bac,0x57bd2),(0x67bc2,0x67be8),(0x7415c,0x7417c),(0x28208,0x2821a),(0x1a700,0x1a720)]:
 needle=o[a:z];pos=[];p=s.find(needle)
 while p>=0:pos.append(hex(start+p));p=s.find(needle,p+1)
 match.append({'odyssey_start':hex(a),'length':z-a,'pilot_exact_matches':pos})
print('MATCHES',match)
Path('outputs/pilot_initial_comparison.json').write_text(json.dumps({'files':meta,'raw_equals_decoded_stock':raw==s,'modified_byte_count':len(diffs),'modified_ranges':ranges,'exact_sequences':match},indent=2))
(root/'stock-rom.bin').write_bytes(bytes(start)+s)
