from pathlib import Path
import sys,json,pypcode
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
f=x5a(Path('/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd').read_bytes());lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));d=bytes(0xc000)+f.firmware_encrypted[0].translate(lut);ctx=pypcode.Context('SuperH:BE:32:SH-2A');out=[]
for a,b in [(0x7415c,0x7435c),(0x7435c,0x74c9c),(0x74c9c,0x75000),(0x300da,0x30140)]:
 out.append(f'RANGE {a:x}')
 for i in ctx.disassemble(d[a:b],a).instructions:out.append(f'{i.addr.offset:08x}: {i.mnem} {i.body}')
O=R/'outputs/dual_ecu_reconstruction';O.mkdir(exist_ok=True);(O/'odyssey_controller_assembly.txt').write_text('\n'.join(out));print('\n'.join(out))
