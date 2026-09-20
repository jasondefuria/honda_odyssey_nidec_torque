from pathlib import Path
import capstone,struct,sys
B=Path('work/user.bin').read_bytes()
md=capstone.Cs(capstone.CS_ARCH_SH,capstone.CS_MODE_SH2A|capstone.CS_MODE_BIG_ENDIAN);md.skipdata=True
U=lambda a,n=4:int.from_bytes(B[a:a+n],'big')
def dump(a,z):
 for i in md.disasm(B[a:z],a):
  note=''
  if i.mnemonic=='movi20':
   v=((int.from_bytes(i.bytes[:2],'big')>>4)&15)<<16|int.from_bytes(i.bytes[2:],'big')
   if v&0x80000: v-=0x100000
   note=f' ; signed immediate = {v} (0x{v&0xffffffff:08X})'
  if i.mnemonic in ('mov.l','mov.w') and i.op_str.startswith('0x'):
   p=int(i.op_str.split(',')[0],16); note=f' ; [{p:05X}] = {U(p,4 if i.mnemonic=="mov.l" else 2):08X}'
  print(f'{i.address:05X} {i.bytes.hex():8} {i.mnemonic:9} {i.op_str}{note}')
def refs(v):
 for a in range(0x2000,len(B)-4,2):
  w=U(a,2)
  if w>>12==13:
   p=((a+4)&~3)+(w&255)*4
   if U(p)==v:print(f'{a:05X}: r{(w>>8)&15} <- [{p:05X}] {v:08X}')
 for a in range(0,len(B)-3,2):
  if U(a)==v:print(f'literal {a:05X}')
if __name__=='__main__':
 if sys.argv[1]=='dump':dump(int(sys.argv[2],16),int(sys.argv[3],16))
 if sys.argv[1]=='refs':refs(int(sys.argv[2],16))
 if sys.argv[1]=='calls':
  v=int(sys.argv[2],16);refs(v)
  for a in range(0x2000,len(B)-2,2):
   w=U(a,2)
   if w>>12 in (10,11):
    disp=w&4095;disp=disp-4096 if disp&2048 else disp
    if a+4+disp*2==v:print(f'{a:05X}: {"bsr" if w>>12==11 else "bra"} {v:05X}')
