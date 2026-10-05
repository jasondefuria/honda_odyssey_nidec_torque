from pathlib import Path
import json,hashlib
import sh2a_pcode as e
R=Path(__file__).resolve().parents[2];P=R/'work/eps_rwd_publish/eps_tools';O=R/'outputs/status_754b0_comparison';lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));ims=[]
for name in ['stock_39990-THR-A020.rwd','mod25xv2-39990-THR,A020.rwd']:
 b=(P/name).read_bytes();i=3
 for _ in range(6):
  count=b[i];i+=1
  for _ in range(count):n=b[i];i+=1+n
 a=int.from_bytes(b[i:i+4],'big');n=int.from_bytes(b[i+4:i+8],'big');rom=bytes(a)+b[i+8:i+8+n].translate(lut);ims.append(rom)
 text=[]
 for ins in e.CTX.disassemble(rom[0x754b0:0x7561c],0x754b0).instructions:text.append(f'{ins.addr.offset:08X} {ins.mnem} {ins.body}')
 (O/(name+'.asm.txt')).write_text('\n'.join(text))
r={'compared_range':'0x754B0–0x7561B inclusive (includes literal pool and adjacent bytes)','length':0x7561c-0x754b0,'identical':ims[0][0x754b0:0x7561c]==ims[1][0x754b0:0x7561c],'sha256':[hashlib.sha256(x[0x754b0:0x7561c]).hexdigest() for x in ims],'calibrations':[]}
for bank in range(1,8):
 for base in [0x57b06,0x57b52]:
  a=base+(bank-1)*0x300;r['calibrations'].append({'bank':bank,'address':hex(a),'stock':int.from_bytes(ims[0][a:a+2],'big'),'mod':int.from_bytes(ims[1][a:a+2],'big')})
(O/'comparison.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
