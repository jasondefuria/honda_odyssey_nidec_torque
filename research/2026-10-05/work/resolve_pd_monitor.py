from pathlib import Path
import sys,json,hashlib,itertools
R=Path(__file__).resolve().parents[1];O=R/'outputs/odyssey_pd_monitor_resolution';O.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'work/emulation'),str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps')]
import sh2a_pcode as em
from rwd_format.x5a import x5a
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()))
def decode(p):
 raw=Path(p).read_bytes();f=x5a(raw);return bytes(f.firmware_blocks[0]['start'])+f.firmware_encrypted[0].translate(lut)
stock=decode(R/'work/eps_rwd_publish/eps_tools/stock_39990-THR-A020.rwd');v4=decode('/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd')
def word(b,a):return int.from_bytes(b[a:a+2],'big',signed=True)
base={k:word(v4,a) for k,a in {'alpha':0x57bd2,'feedback_limit':0x57bd4,'D_limit':0x57bd6,'P_limit':0x57bd8,'combined_limit':0x57bda,'global_scale':0x500a6}.items()}
configs=[dict(name='stock',source='stock'),dict(name='v4',source='v4'),dict(name='P_minus_25pct',p=.75),dict(name='D_plus_25pct',d=1.25),dict(name='tracker_minus_25pct',alpha=.75),dict(name='tracker_plus_25pct',alpha=1.25),dict(name='limits_minus_20pct',limits=.8),dict(name='combined_exploratory',p=.75,d=1.25,alpha=.75,limits=.8)]
rows=[];patches={}
for cfg in configs:
 b=bytearray(stock if cfg.get('source')=='stock' else v4);changes=[]
 for bank in [1,2,3]:
  off=(bank-1)*0x300
  for key,start,count in [('p',0x57c82,9),('d',0x57c5e,9),('alpha',0x57bd2,1),('limits',0x57bd6,3)]:
   if key not in cfg:continue
   for i in range(count):
    a=start+off+2*i;old=word(b,a);new=round(old*cfg[key]);b[a:a+2]=new.to_bytes(2,'big',signed=True);changes.append(dict(address=hex(a),old=old,new=new))
 # Keep independent gain references consistent; never alter diagnostic logic or tolerances.
 for bank in [1,2,3]:
  off=(bank-1)*0x300
  for key,main,reference in [('p',0x57c82,0x67cac),('d',0x57c5e,0x67c84)]:
   if key not in cfg:continue
   for i in range(9):
    a=reference+off+2*i;old=word(b,a);new=word(b,main+off+2*i);b[a:a+2]=new.to_bytes(2,'big',signed=True);changes.append(dict(address=hex(a),old=old,new=new,role='independent '+key+' gain reference'))
 patches[cfg['name']]=changes;em.load_rom(b)
 for bank in [1,2,3,7]:
  for cmd in [-1024,-400,0,400,1024]:
   for feedback in [-2000,0,2000]:
    c=em.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc)
    for a,v in [(0xfff82f60,16384),(0xfff82f62,0),(0xfff82f64,16384)]:c.writemem(a,2,v)
    c.writemem(0xfff82fec,2,cmd);c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484));ticks=[]
    for tick in range(4):
     c.run(0x742c0,(feedback,0xfff82ff8,0xfff8a48c))
     for i,p in enumerate([0xfff82fc0,0xfff83004,0xfff8a498]):c.writemem(0x1000f000+4*i,4,p)
     c.run(0x7435c,(0,0xfff82fa0,0xfff82ff8,0xfff82ff0))
     vals={k:em.signed(c.readmem(0xfff83004+off,n),n) for k,off,n in [('d',0x4c,2),('p',0x5c,2),('scheduled_raw',0x64,4),('out',0x70,2),('scaled',0x72,2)]}
     vals['feedback']=em.signed(c.readmem(0xfff83002,2),2)
     c.run(0x6b010,(0xfff8a498,));vals['monitor_flags']=c.readmem(0xfff8a5de,4);ticks.append(vals)
    rows.append(dict(config=cfg['name'],bank=bank,command=cmd,feedback_input=feedback,target=em.signed(c.readmem(0xfff82ff6,2),2),ticks=ticks))
 print('Completed',cfg['name'],flush=True)
result=dict(scope='Offline RAM/calibration experiments; in-memory patches only; no checksum repair, no flash image and no mechanical plant',base=base,configs=configs,patches=patches,rows=rows)
(O/'results.json').write_text(json.dumps(result,indent=2))
# Isolated SH-2A feedforward product helper: muls.w r4,r5; sts macl,r0; mov #-10,r1; shad r1,r0; rts; nop.
helper=bytes.fromhex('254f001ae1f6401c000b0009');em.load_rom(bytes(0x100)+helper);ff=[]
for target,gain in itertools.product([-32768,-12160,-1,0,1,12160,32767],[0,8,16,32,45]):
 c=em.CPU();ret,_=c.run(0x100,(target,gain));actual=em.signed(ret,4);expected=(target*gain)>>10;ff.append(dict(target=target,gain=gain,actual=actual,expected=expected,match=actual==expected))
(O/'feedforward_helper.json').write_text(json.dumps(dict(scope='Isolated arithmetic helper, NOT inserted into Odyssey controller. Clamping, scheduling and independent monitor integration remain unimplemented.',opcode_hex=helper.hex(),cases=ff,all_match=all(x['match'] for x in ff)),indent=2))
print('Feedforward cases',len(ff),'all matched',all(x['match'] for x in ff))
