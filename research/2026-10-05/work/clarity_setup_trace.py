exec(open('work/map_clarity.py').read().split('targets=')[0])
out=[]
for a,b in [(0x342e0,0x343fc),(0x28d80,0x29014)]:
 out.append(f'RANGE {a:x}-{b:x}')
 for i in ctx.disassemble(d[a:b],a).instructions:out.append(f'{i.addr.offset:08x}: {i.mnem} {i.body}')
for t in [0xfff879e4,0xfff87a0c,0xfff87ad8,0xfff87aec,0xfff87b70,0xfff87a48]:
 for a in range(0x4000,len(d)-3,2):
  if int.from_bytes(d[a:a+4],'big')==t:out.append(f'PTR {t:x} at {a:x}: '+d[max(0,a-16):a+36].hex())
for a in [0x34600,0x356ec,0x2afe8,0x2a178,0x2a17c]:out.append(f'POOL {a:x} {int.from_bytes(d[a:a+4],"big"):08x}')
(R/'outputs/clarity_ptm_comparison/setup_trace.txt').write_text('\n'.join(out));print('\n'.join(out))
