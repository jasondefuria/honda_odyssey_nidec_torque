exec(open('work/map_clarity.py').read().split('targets=')[0])
out=[]
for p in [0x2a168,0x290dc,0x290fc,0x29100,0x2ae78,0x2ae7c]:out.append(f'POOL {p:x}: {int.from_bytes(d[p:p+4],"big"):08x}')
x=int.from_bytes(d[0x2a168:0x2a16c],'big')
for a,b in [(x,x+140),(0x34646,0x34690)]:
 for i in ctx.disassemble(d[a:b],a).instructions:out.append(f'{i.addr.offset:08x}: {i.mnem} {i.body}')
# Direct branch callers and literal references to sample ingestion.
t=0x3432c
for pc in range(0x4000,len(d)-1,2):
 w=int.from_bytes(d[pc:pc+2],'big')
 if w>>12==11:
  disp=w&4095;disp=disp-4096 if disp&2048 else disp
  if pc+4+2*disp==t:out.append(f'DIRECT SAMPLE CALL {pc:x}')
for pc in range(0x4000,len(d)-3,2):
 if int.from_bytes(d[pc:pc+4],'big')==t:out.append(f'SAMPLE FN POINTER {pc:x}')
(R/'outputs/clarity_ptm_comparison/feedback_trace.txt').write_text('\n'.join(out));print('\n'.join(out))
