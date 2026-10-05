from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/odyssey_ff_implementation';O.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'work/emulation'),str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps')]
import sh2a_pcode as em
from rwd_format.x5a import x5a
raw=Path('/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd').read_bytes();f=x5a(raw);base=bytes(0xc000)+f.firmware_encrypted[0].translate(bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text())))
class Asm:
 def __init__(self,start):self.start=start;self.b=bytearray();self.fix=[];self.labels={};self.lits=[]
 def w(self,x):self.b+=x.to_bytes(2,'big')
 def raw(self,x):self.b+=x
 def lit(self,r,x):self.fix.append((len(self.b),'lit',r,len(self.lits)));self.lits.append(x);self.w(0)
 def bt(self,label):self.fix.append((len(self.b),'bt',0,label));self.w(0)
 def label(self,x):self.labels[x]=len(self.b)
 def end(self):
  while (self.start+len(self.b))%4:self.w(9)
  pool=len(self.b)
  for x in self.lits:self.b+=(x&0xffffffff).to_bytes(4,'big')
  for p,typ,r,v in self.fix:
   if typ=='lit':disp=(self.start+pool+4*v-((self.start+p+4)&~3))//4;word=0xd000|(r<<8)|disp;assert 0<=disp<=255
   else:disp=(self.labels[v]-p-4)//2;assert -128<=disp<=127;word=0x8900|(disp&255)
   self.b[p:p+2]=word.to_bytes(2,'big')
  return bytes(self.b)
def helper(start,gain,monitor=False):
 a=Asm(start)
 if monitor:
  a.raw(base[0x6b718:0x6b720]);a.w(0x62d3);a.w(0x326c) # expected=P+D
 else:a.raw(base[0x74a98:0x74aa2])
 for r in [0,1,4,5,6]:a.w(0x2f06|(r<<4))
 a.w(0x4f12) # sts.l macl,@-r15
 a.w(0x64f3);a.w(0x747f);a.w(0x7400|((0x74 if monitor else 0x90)+24-127))
 a.w(0x6441);a.lit(5,gain);a.w(0x254f);a.w(0x041a);a.w(0xe5f6);a.w(0x445c);a.w(0x324c)
 a.lit(4,-32767);a.w(0x3243);a.bt('lower_ok');a.w(0x6243);a.label('lower_ok')
 a.lit(5,32767);a.w(0x3523);a.bt('upper_ok');a.w(0x6253);a.label('upper_ok')
 a.w(0x4f16) # lds.l @r15+,macl
 for r in [6,5,4,1,0]:a.w(0x60f6|(r<<8))
 if monitor:
  a.w(0x622b);a.w(0x32ec);a.w(0x326c) # residual+D, comparison retained
  ret=0x6b724
 else:a.raw(base[0x74aa2:0x74aa8]);ret=0x74aa8
 a.lit(3,ret);a.w(0x432b);a.w(9)
 return a.end()
def stub(address,dest,n):
 a=Asm(address);a.lit(3,dest);a.w(0x432b);a.w(9);b=a.end();assert len(b)<=n;return b+bytes.fromhex('0009')*((n-len(b))//2)
def build(g,ref):
 b=bytearray(base+bytes(0x1000));h=helper(0x80000,g);m=helper(0x80400,ref,True)
 b[0x80000:0x80000+len(h)]=h;b[0x80400:0x80400+len(m)]=m
 b[0x74a98:0x74aa8]=stub(0x74a98,0x80000,16);b[0x6b718:0x6b724]=stub(0x6b718,0x80400,12)
 return b,h,m
if __name__=='__main__':
 cases=[]
 for name,g,ref in [('zero',0,0),('matched8',8,8),('matched45',45,45),('bad_controller',16,8),('bad_reference',8,16)]:
  b,h,m=build(g,ref);em.load_rom(b)
  if name=='matched8':
   dis=[]
   for start,code in [(0x80000,h),(0x80400,m)]:
    for i in em.CTX.disassemble(code,start).instructions:dis.append(f'{i.addr.offset:08x}: {i.mnem} {i.body}')
   (O/'helper_disassembly.txt').write_text('\n'.join(dis));(O/'helper_bytes.json').write_text(json.dumps({'controller':h.hex(),'monitor':m.hex(),'addresses':'emulator-only beyond original ROM'},indent=2))
  for bank in [1,3,7]:
   for command in [-1024,-400,0,400,1024]:
    for feedback in [-2000,0,2000]:
     c=em.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc)
     for a,v in [(0xfff82f60,16384),(0xfff82f62,0),(0xfff82f64,16384)]:c.writemem(a,2,v)
     c.writemem(0xfff82fec,2,command);c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484));ticks=[]
     for tick in range(4):
      c.run(0x742c0,(feedback,0xfff82ff8,0xfff8a48c))
      for i,p in enumerate([0xfff82fc0,0xfff83004,0xfff8a498]):c.writemem(0x1000f000+4*i,4,p)
      c.run(0x7435c,(0,0xfff82fa0,0xfff82ff8,0xfff82ff0));out=em.signed(c.readmem(0xfff83074,2),2);scaled=em.signed(c.readmem(0xfff83076,2),2)
      c.run(0x6b010,(0xfff8a498,));ticks.append({'out':out,'scaled':scaled,'flags':c.readmem(0xfff8a5de,4)})
     cases.append(dict(name=name,bank=bank,command=command,feedback=feedback,ticks=ticks))
  print(name,'done',flush=True)
 (O/'results.json').write_text(json.dumps(cases,indent=2))
