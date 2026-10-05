from implement_ff_pair import *
import itertools
rows=[]
for gain in [0,8,45]:
 b,h,m=build(gain,gain);em.load_rom(b)
 for target,p,d in itertools.product([-32768,-1,0,1,32767],[-32768,-2560,0,2560,32767],[-32768,-640,0,640,32767]):
  expected=max(-32767,min(32767,p+d+((target*gain)>>10)))
  c=em.CPU();c.setreg('r8',d);c.setreg('r1',p);c.setreg('r4',0x12345678);c.setreg('r5',0x23456789);c.setreg('macl',0x3456789a)
  c.writemem(0x1000f000+0x90,2,target);c.writemem(0x1000f000+0xd0,4,256)
  c.hooks[0x74aa8]=lambda cpu:cpu.setreg('pr',0xfffffffe)
  c.run(0x80000)
  assert em.signed(c.readmem(0x1000f000+0xfc,4),4)==expected
  assert em.signed(c.getreg('r2'),4)==expected*256
  assert c.getreg('r4')==0x12345678 and c.getreg('r5')==0x23456789 and c.getreg('macl')==0x3456789a and c.getreg('r15')==0x1000f000
  for corrupt in [0,1]:
   q=em.CPU();q.setreg('r13',p);q.setreg('r0',0x11111111);q.setreg('r1',0x22222222);q.setreg('r4',0x33333333);q.setreg('r5',0x44444444);q.setreg('macl',0x55555555)
   for off,n,v in [(0x5c,4,expected+corrupt),(0x4c,2,d),(0x74,2,target)]:q.writemem(0x1000f000+off,n,v)
   q.hooks[0x6b724]=lambda cpu:cpu.setreg('pr',0xfffffffe)
   q.run(0x80400)
   assert em.signed(q.getreg('r2'),4)==d+corrupt
   for reg,val in [('r0',0x11111111),('r1',0x22222222),('r4',0x33333333),('r5',0x44444444),('macl',0x55555555),('r15',0x1000f000)]:assert q.getreg(reg)==val
  rows.append(dict(gain=gain,target=target,p=p,d=d,expected=expected,controller_pass=True,monitor_good_pass=True,monitor_corruption_detectable=True))
(O/'boundary_results.json').write_text(json.dumps(rows,indent=2));print('Boundary cases',len(rows),'all passed')
