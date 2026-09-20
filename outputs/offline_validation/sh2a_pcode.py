"""Read-only ROM execution model using Ghidra SLEIGH via pypcode.
No peripherals, interrupts, timing, or vehicle model. Unsupported operations fail.
RAM must lie in explicitly allocated offline regions. ROM writes always fail.
"""
from pathlib import Path
import pypcode
ROM=Path(__file__).resolve().parent.parent.joinpath('user.original.bin').read_bytes()
import hashlib
assert hashlib.sha256(ROM).hexdigest() == 'e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2', 'Unexpected firmware image'
CTX=pypcode.Context('SuperH:BE:32:SH-2A')
CACHE={}

def signed(v,n):
 m=1<<(n*8);return v-m if v&(m>>1) else v

def compile_block(pc):
 if pc in CACHE:return CACHE[pc]
 tx=CTX.translate(ROM[pc:pc+16],pc,max_instructions=1)
 ops=[];end=pc
 for op in tx.ops:
  ins=[(v.space.name,v.offset,v.size) for v in op.inputs]
  out=None if op.output is None else(op.output.space.name,op.output.offset,op.output.size)
  if op.opcode.name=='IMARK':
   end=max(v.offset+v.size for v in op.inputs);continue
  ops.append((op.opcode.name,out,ins))
 CACHE[pc]=(end,ops);return end,ops

class CPU:
 def __init__(self):
  self.reg=bytearray(0x200);self.ram=bytearray(0x10000);self.stack=bytearray(0x10000)
  self.unique={};self.steps=0;self.visited=set();self.hooks={};self.pc=0
 def readmem(self,a,n):
  if 0<=a and a+n<=len(ROM):return int.from_bytes(ROM[a:a+n],'big')
  if 0xfff80000<=a and a+n<=0xfff90000:return int.from_bytes(self.ram[a-0xfff80000:a-0xfff80000+n],'big')
  if 0x10000000<=a and a+n<=0x10010000:return int.from_bytes(self.stack[a-0x10000000:a-0x10000000+n],'big')
  raise ValueError(('unmapped read',hex(self.pc),hex(a),n))
 def writemem(self,a,n,v):
  raw=(v&((1<<(8*n))-1)).to_bytes(n,'big')
  if 0xfff80000<=a and a+n<=0xfff90000:self.ram[a-0xfff80000:a-0xfff80000+n]=raw;return
  if 0x10000000<=a and a+n<=0x10010000:self.stack[a-0x10000000:a-0x10000000+n]=raw;return
  raise ValueError(('unmapped or ROM write',hex(self.pc),hex(a),n))
 def get(self,v):
  sp,a,n=v
  if sp=='const':return a&((1<<(n*8))-1)
  if sp=='register':return int.from_bytes(self.reg[a:a+n],'big')
  if sp=='unique':return self.unique[(a,n)]
  if sp=='ram':return self.readmem(a,n)
  raise ValueError(v)
 def put(self,v,x):
  sp,a,n=v;x&=(1<<(8*n))-1
  if sp=='register':self.reg[a:a+n]=x.to_bytes(n,'big')
  elif sp=='unique':self.unique[(a,n)]=x
  elif sp=='ram':self.writemem(a,n,x)
  else:raise ValueError(v)
 def setreg(self,name,v):
  r=CTX.registers[name];self.put(('register',r.offset,r.size),v)
 def getreg(self,name):
  r=CTX.registers[name];return self.get(('register',r.offset,r.size))
 def run(self,pc,args=(),limit=100000):
  self.setreg('r15',0x1000f000);self.setreg('pr',0xfffffffe)
  for k,v in enumerate(args):self.setreg('r'+str(4+k),v)
  self.pc=pc;count=0
  while self.pc!=0xfffffffe:
   if count>=limit:raise RuntimeError(('instruction limit',hex(self.pc)))
   count+=1;self.steps+=1;self.visited.add(self.pc)
   if self.pc in self.hooks:
    self.hooks[self.pc](self);self.pc=self.getreg('pr');continue
   end,ops=compile_block(self.pc);i=0;target=None;self.unique={}
   while i<len(ops):
    op,out,ins=ops[i];i+=1
    if op in ('LOAD','STORE'):
     addr=self.get(ins[1])
     if op=='LOAD':self.put(out,self.readmem(addr,out[2]))
     else:self.writemem(addr,ins[2][2],self.get(ins[2]))
     continue
    if op in ('BRANCH','CBRANCH','CALL'):
     take=op!='CBRANCH' or self.get(ins[1])!=0
     if take:
      if ins[0][0]=='const':i=i-1+signed(ins[0][1],ins[0][2]);continue
      target=ins[0][1];break
     continue
    if op in ('BRANCHIND','CALLIND','RETURN'):
     target=self.get(ins[0]);break
    a=[self.get(x) for x in ins];v=None
    if op in ('COPY','INT_ZEXT'):v=a[0]
    elif op=='INT_SEXT':v=signed(a[0],ins[0][2])
    elif op=='SUBPIECE':v=a[0]>>(a[1]*8)
    elif op=='PIECE':v=(a[0]<<(ins[1][2]*8))|a[1]
    elif op=='INT_ADD':v=a[0]+a[1]
    elif op=='INT_SUB':v=a[0]-a[1]
    elif op=='INT_MULT':v=a[0]*a[1]
    elif op=='INT_DIV':v=a[0]//a[1]
    elif op=='INT_SDIV':
     x,y=signed(a[0],ins[0][2]),signed(a[1],ins[1][2]);v=(abs(x)//abs(y))*(-1 if (x<0) != (y<0) else 1)
    elif op=='INT_REM':v=a[0]%a[1]
    elif op=='INT_SREM':
     x,y=signed(a[0],ins[0][2]),signed(a[1],ins[1][2]);v=(abs(x)%abs(y))*(-1 if x<0 else 1)
    elif op in ('INT_AND','BOOL_AND'):v=a[0]&a[1]
    elif op in ('INT_OR','BOOL_OR'):v=a[0]|a[1]
    elif op in ('INT_XOR','BOOL_XOR'):v=a[0]^a[1]
    elif op=='INT_NEGATE':v=~a[0]
    elif op=='INT_2COMP':v=-a[0]
    elif op=='BOOL_NEGATE':v=int(not a[0])
    elif op=='INT_LEFT':v=0 if a[1]>=out[2]*8 else a[0]<<a[1]
    elif op=='INT_RIGHT':v=0 if a[1]>=ins[0][2]*8 else a[0]>>a[1]
    elif op=='INT_SRIGHT':v=signed(a[0],ins[0][2])>>min(a[1],ins[0][2]*8)
    elif op=='INT_EQUAL':v=int(a[0]==a[1])
    elif op=='INT_NOTEQUAL':v=int(a[0]!=a[1])
    elif op=='INT_LESS':v=int(a[0]<a[1])
    elif op=='INT_LESSEQUAL':v=int(a[0]<=a[1])
    elif op=='INT_SLESS':v=int(signed(a[0],ins[0][2])<signed(a[1],ins[1][2]))
    elif op=='INT_SLESSEQUAL':v=int(signed(a[0],ins[0][2])<=signed(a[1],ins[1][2]))
    elif op=='INT_CARRY':v=int(a[0]+a[1]>=(1<<(ins[0][2]*8)))
    elif op in ('INT_SCARRY','INT_SBORROW'):
     n=ins[0][2]*8;x=signed(a[0],ins[0][2]);y=signed(a[1],ins[1][2]);z=x+y if op=='INT_SCARRY' else x-y;v=int(not(-(1<<(n-1))<=z<(1<<(n-1))))
    elif op=='POPCOUNT':v=a[0].bit_count()
    else:raise NotImplementedError((hex(self.pc),op,out,ins))
    self.put(out,v)
   self.pc=end if target is None else target
  return self.getreg('r0'),count
