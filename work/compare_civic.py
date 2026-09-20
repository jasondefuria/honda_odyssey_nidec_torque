import ast,json,hashlib
from pathlib import Path
src=Path('work/nrdr-reference/openpilot/nrdr/tools/eps/check_rwd.py').read_text()
# Extract only a literal data dictionary, never import or execute repository code.
tree=ast.parse(src)
lut=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DECRYPT_LOOKUP' for t in n.targets))
def parse(p):
 raw=p.read_bytes();assert raw[:3]==b'Z\r\n';i=3;hs=[]
 for _ in range(6):
  count=raw[i];i+=1;h=[]
  for _ in range(count):
   size=raw[i];i+=1;h.append(raw[i:i+size]);i+=size
  hs.append(h)
 start=int.from_bytes(raw[i:i+4],'big');size=int.from_bytes(raw[i+4:i+8],'big');i+=8
 assert i+size+4==len(raw)
 dec=bytes(lut[x] for x in raw[i:i+size])
 u=lambda off:int.from_bytes(dec[off:off+2],'big')
 checks={'outer':sum(raw[:-4])&0xffffffff==int.from_bytes(raw[-4:],'little'),'firmware_sum':sum(u(a) for a in range(0,size-128,2))&65535==u(size-128),'firmware_negative_sum':(-sum(u(a) for a in range(0,size-2,2)))&65535==u(size-2)}
 return dec,{'source':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'start':hex(start),'length':hex(size),'checks':checks},start
paths=list(Path('work/civic-a030').rglob('*.rwd'))+list(Path('work/nrdr-reference').rglob('*C020.rwd'))
parsed={str(p):parse(p) for p in paths};out={'files':[v[1] for v in parsed.values()],'comparisons':[]}
for path,(data,meta,start) in parsed.items():
 if 'stock-' in Path(path).name:continue
 family='A030' if 'A030' in path else 'C020'
 stock=next(v[0] for p,v in parsed.items() if 'stock-' in Path(p).name and family in p)
 diffs=[i for i,(a,b) in enumerate(zip(stock,data)) if a!=b];groups=[]
 for i in diffs:
  if not groups or i>groups[-1][-1]+16:groups.append([i])
  else:groups[-1].append(i)
 ranges=[]
 for g in groups:
  a=g[0]&~1;z=(g[-1]+2)&~1
  ranges.append({'rom_start':hex(start+a),'rom_end_exclusive':hex(start+z),'changed_bytes':len(g),'stock_hex':stock[a:z].hex(),'modified_hex':data[a:z].hex()})
 out['comparisons'].append({'file':path,'changed_bytes':len(diffs),'ranges':ranges})
 (Path('work/civic-a030')/(Path(path).name+'.decoded.bin')).write_bytes(data)
Path('outputs/civic_reference_comparison.json').write_text(json.dumps(out,indent=2))
for c in out['comparisons']:
 print(c['file'],c['changed_bytes'])
 for r in c['ranges']:print(r['rom_start'],r['rom_end_exclusive'],r['changed_bytes'],r['stock_hex'][:120],r['modified_hex'][:120])
print('Checks',[(x['source'],x['checks']) for x in out['files']])
