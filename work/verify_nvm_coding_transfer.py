from sh2a_pcode import CPU,ROM
from pathlib import Path
import json,hashlib
class IOCPU(CPU):
 def __init__(self):super().__init__();self.io={};self.io_writes=[]
 def readmem(self,a,n):
  if 0xffffa800<=a<0xffffaa00 or 0xff460000<=a<0xff461000 or 0x80100000<=a<0x80108000:return self.io.get((a,n),0)
  return super().readmem(a,n)
 def writemem(self,a,n,v):
  if 0xffffa800<=a<0xffffaa00 or 0xff460000<=a<0xff461000 or 0x80100000<=a<0x80108000:
   self.io[(a,n)]=v&((1<<(8*n))-1);self.io_writes.append({'pc':hex(self.pc),'address':hex(a),'width':n,'value':hex(v&((1<<(8*n))-1))});return
  super().writemem(a,n,v)
c=IOCPU();c.io[(0xffffa91e,2)]=1;c.io[(0xffffa900,2)]=0x8000
# Table row 9's initialized selection word is zero; dataflash and DMA IO modeled, not real.
returns=[]
for _ in range(2):returns.append(c.run(0x31624,(0xfff83f34,0x80106800,24))[0])
assert c.io[(0xff460060,4)]==0x80106800
assert c.io[(0xff460064,4)]==0xfff83f34
assert c.io[(0xff460068,4)]==24
assert c.io[(0xff460434,4)]==0x01010100
out={'rom_sha256':hashlib.sha256(ROM).hexdigest(),'scope':'Original 31624 and 32034 executed with synthetic IO dictionary: synthetic status FFFFA91E=1 and FFFFA900=8000, other status zero, fresh RAM. Captures writes that configure a transfer; no real DMA, flash, EEPROM or ECU operations.','descriptor_address':'0x39450','descriptor_hex':ROM[0x39450:0x3946c].hex(),'source':'0x80106800','shadow_destination':'0xFFF83F34','length':24,'routine_returns':returns,'io_writes':c.io_writes}
Path('outputs/odyssey_nvm_coding_transfer.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
