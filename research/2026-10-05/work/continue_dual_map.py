from pathlib import Path
import sys,json,pypcode
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
ctx=pypcode.Context('SuperH:BE:32:SH-2A');lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()))
for name,path,targets in [('odyssey','/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd',[0x742c0,0xfff86f60,0xfff82ff8]),('clarity','/Users/jasondefuria/Downloads/39990-TRW-A020 (stock).rwd',[0xfff87ad8,0xfff879e4,0x29fb4])]:
 f=x5a(Path(path).read_bytes());d=bytes(f.firmware_blocks[0]['start'])+f.firmware_encrypted[0].translate(lut);out=[]
 for t in targets:
  pools=[a for a in range(0,len(d)-3,2) if int.from_bytes(d[a:a+4],'big')==t];refs=[]
  for pc in range(0,len(d)-1,2):
   w=int.from_bytes(d[pc:pc+2],'big')
   if w>>12==13 and ((pc+4)&~3)+4*(w&255) in pools:refs.append(pc)
  out.append(f'TARGET {t:08x} POOLS {[hex(x) for x in pools]} REFS {[hex(x) for x in refs]}')
  for pc in refs:
   a=max(0,pc-36);out.append(f'CONTEXT {pc:x}')
   for i in ctx.disassemble(d[a:pc+100],a).instructions:out.append(f'{i.addr.offset:08x}: {i.mnem} {i.body}')
 (R/f'outputs/dual_ecu_reconstruction/{name}_next_xrefs.txt').write_text('\n'.join(out));print(name+'\n'+'\n'.join(out))
