exec(open('work/dual_ranges.py').read().split('for pair in sys.argv')[0])
if name=='odyssey':
 pools={a:int.from_bytes(d[a:a+4],'big') for a in range(0,len(d)-3,2) if 0xfff80000<=int.from_bytes(d[a:a+4],'big')<=0xfff8029c}
 for pc in range(0,len(d)-1,2):
  w=int.from_bytes(d[pc:pc+2],'big');p=((pc+4)&~3)+4*(w&255)
  if w>>12==13 and p in pools:
   val=pools[p]
   if val>=0xfff80180:print(hex(pc),hex(val))
else:
 target=0x28e3c
 for pc in range(0,len(d)-1,2):
  w=int.from_bytes(d[pc:pc+2],'big');disp=w&4095;disp=disp-4096 if disp&2048 else disp
  if w>>12==11 and pc+4+2*disp==target:print('BSR',hex(pc))
