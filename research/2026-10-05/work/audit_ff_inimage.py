from assemble_ff_inimage import *
regions=[(0x75800,0x75a00)]
refs=[]
for pc in range(0xc000,len(base)-3,2):
 v=int.from_bytes(base[pc:pc+4],'big')
 if any(a<=v<b for a,b in regions):refs.append({'kind':'32bit_value_candidate','offset':hex(pc),'target':hex(v)})
 w=int.from_bytes(base[pc:pc+2],'big');disp=w&0xfff;disp=disp-4096 if disp&2048 else disp
 if w>>12 in [10,11]:
  target=pc+4+2*disp
  if any(a<=target<b for a,b in regions):refs.append({'kind':'unclassified_BRA_BSR_encoding','offset':hex(pc),'target':hex(target)})
def crc(data):
 c=0xffffffff
 for byte in data:
  c^=byte<<24
  for _ in range(8):c=((c<<1)^(0x04c11db7 if c&0x80000000 else 0))&0xffffffff
 return c^0xffffffff
def ws(d):return sum(int.from_bytes(d[i:i+2],'big') for i in range(0,len(d),2))&0xffff
b,h,m=build(8,8);changes=[i for i in range(len(base)) if b[i]!=base[i]]
assert len(b)==len(base)==0x80000
assert all(0x74a98<=i<0x74aa8 or 0x6b718<=i<0x6b724 or 0x75800<=i<0x75800+len(h) or 0x75900<=i<0x75900+len(m) for i in changes)
# Offline round-trip trial only, no RWD file written.
b[0x6ff7c:0x6ff80]=crc(b[0x60000:0x6ff60]).to_bytes(4,'big');b[0x7ff80:0x7ff82]=ws(b[0xc000:0x7ff80]).to_bytes(2,'big');b[-2:]=((-ws(b[0xc000:-2]))&65535).to_bytes(2,'big')
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));inv=bytes(lut.index(i) for i in range(256));off=len(raw)-4-0x74000;body=raw[:off]+bytes(b[0xc000:]).translate(inv);container=body+(sum(body)&0xffffffff).to_bytes(4,'little');parsed=x5a(container)
assert parsed.firmware_encrypted[0].translate(lut)==b[0xc000:];assert ws(b[0xc000:])==0
for start in [0x40000,0x60000]:assert int.from_bytes(b[start+0xff7c:start+0xff80],'big')==crc(b[start:start+0xff60])
out={'scope':'Gain8 assembly/serialization test, no release gain selected or RWD written','controller_address':'0x75800','controller_bytes':len(h),'monitor_address':'0x75900','monitor_bytes':len(m),'original_fill':'FF','reference_scan':refs,'scan_limit':'Raw encodings include possible data; indirect/computed targets and reserved ownership cannot be excluded','changed_code_bytes':len(changes),'image_size':len(b),'roundtrip_pass':True,'checksum_A':b[0x7ff80:0x7ff82].hex(),'checksum_C':b[-2:].hex(),'crc60000':b[0x6ff7c:0x6ff80].hex(),'container_sum':container[-4:].hex()}
(O/'placement_and_roundtrip.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
