exec(open('work/dual_ranges.py').read().split('for pair in sys.argv')[0])
for target in [int(x,16) for x in sys.argv[2:]]:
 pools={a for a in range(0,len(d)-3,2) if int.from_bytes(d[a:a+4],'big')==target}
 print('TARGET',hex(target),'POOLS',list(map(hex,pools)))
 for pc in range(0,len(d)-1,2):
  w=int.from_bytes(d[pc:pc+2],'big');v=w&4095;v=v-4096 if v&2048 else v
  if (w>>12==11 and pc+4+2*v==target) or (w>>12==13 and ((pc+4)&~3)+4*(w&255) in pools):print('REF',hex(pc))
if name=='odyssey':
 print('DENOMINATOR',int.from_bytes(d[0x5f604:0x5f608],'big'));print('K',(0x2bf2<<16)//int.from_bytes(d[0x5f604:0x5f608],'big'))
