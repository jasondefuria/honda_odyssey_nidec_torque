from assemble_ff_no_bank7 import *
manifest=json.loads((R/'outputs/odyssey_ff_combined_grid/review_patch_manifest.json').read_text());b=bytearray(base)
for c in manifest['changes']:
 a=int(c['address'],16);v=bytes.fromhex(c['replacement']);assert b[a:a+len(v)]==bytes.fromhex(c['original']);b[a:a+len(v)]=v
for address,monitor in [(0x75800,False),(0x75900,True)]:
 h=helper(address,8,monitor);assert len(h)<=256;b[address:address+len(h)]=h
changes=[];start=None
for i in range(len(b)+1):
 if i<len(b) and b[i]!=base[i]:
  if start is None:start=i
 elif start is not None:
  changes.append(dict(address=hex(start),original=base[start:i].hex(),replacement=bytes(b[start:i]).hex()));start=None
manifest['changes']=changes;manifest['scope']='Exploratory profile with independent bank7 feedforward exclusion; word selector0x900'
(O/'review_patch_manifest.json').write_text(json.dumps(manifest,indent=2))
