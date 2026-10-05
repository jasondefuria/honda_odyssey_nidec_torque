from pathlib import Path
import sys,json,pypcode
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));ctx=pypcode.Context('SuperH:BE:32:SH-2A');out=[]
for name in ['39990-TRW-A020 (stock).rwd','ClarityMax-PTM.rwd']:
 f=x5a((Path('/Users/jasondefuria/Downloads')/name).read_bytes());d=bytes(0x4000)+f.firmware_encrypted[0].translate(lut)
 out.append('\nFILE '+name)
 for x in [0x2a18c,0x2a194,0x2a1a4,0x2a1a8,0x2a45c,0x2a460,0x2a464,0x2a478,0x2a47c,0x2a480,0x2a484,0x2a488,0x2a48c,0x2a490,0x2a494,0x2a710,0x2afec]:out.append(f'POOL {x:x}: {int.from_bytes(d[x:x+4],"big"):08x}')
 ranges=[(0x3add6,0x3aeb0)]
 for a,b in ranges:
  if 'stock' in name and a in [0x1b81e,0x4f9cc]:continue
  out.append(f'RANGE {a:x}-{b:x}')
  for i in ctx.disassemble(d[a:b],a).instructions:out.append(f'{i.addr.offset:08x}: {i.mnem} {i.body}')
  if a==0x4f9cc:
   for x in range(0x4fa68,0x4fac0,4):out.append(f'POOL {x:x}: {int.from_bytes(d[x:x+4],"big"):08x}')
(R/'outputs/clarity_ptm_comparison/interpolation_trace.txt').write_text('\n'.join(out));print('\n'.join(out))
