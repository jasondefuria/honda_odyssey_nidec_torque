from pathlib import Path
import sys,json,pypcode
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
f=x5a(Path('/Users/jasondefuria/Downloads/39990-TRW-A020 (stock).rwd').read_bytes());lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));d=bytes(0x4000)+f.firmware_encrypted[0].translate(lut);ctx=pypcode.Context('SuperH:BE:32:SH-2A')
targets=[0xfff897e8,0xfff87a44,0xfff87b7c,0xfff8968c]
out=[]
for t in targets:
 pools=[a for a in range(0x4000,len(d)-3,2) if d[a:a+4]==t.to_bytes(4,'big')];refs=[]
 for pc in range(0x4000,len(d)-1,2):
  w=int.from_bytes(d[pc:pc+2],'big')
  if w>>12==13 and ((pc+4)&~3)+4*(w&255) in pools:refs.append(pc)
 out.append(f'TARGET {t:08x} POOLS {[hex(x) for x in pools]} REFS {[hex(x) for x in refs]}')
 for pc in refs:
  out.append(f'CONTEXT {pc:x}')
  try:
   for i in ctx.disassemble(d[max(0x4000,pc-16):pc+64],max(0x4000,pc-16)).instructions:out.append(f'{i.addr.offset:08x}: {i.mnem} {i.body}')
  except Exception as e:out.append(str(e))
(R/'outputs/clarity_ptm_comparison/producer_xrefs2.txt').write_text('\n'.join(out));print('\n'.join(out))
