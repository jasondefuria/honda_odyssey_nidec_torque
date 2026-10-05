exec(open('work/map_clarity.py').read().split('targets=')[0])
out=[]
for pc in range(0x4000,len(d)-2,2):
 w=int.from_bytes(d[pc:pc+2],'big')
 if w>>12==13 and ((pc+4)&~3)+4*(w&255)==0x35118:
  out.append(f'REF {pc:x}')
  for i in ctx.disassemble(d[pc-48:pc+32],pc-48).instructions:out.append(f'{i.addr.offset:08x}: {i.mnem} {i.body}')
for a in range(0x350e0,0x35130,4):out.append(f'POOL {a:x}: {int.from_bytes(d[a:a+4],"big"):08x}')
(R/'outputs/clarity_ptm_comparison/sensor_trace.txt').write_text('\n'.join(out));print('\n'.join(out))
