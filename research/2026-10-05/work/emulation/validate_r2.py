"""Offline ROM execution of R2 and stock. No hooks, peripherals or plant."""
import sys,json,hashlib,random,time,struct
from pathlib import Path
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as e
root=Path(__file__).resolve().parents[2];started=time.monotonic()
images={'stock':(root/'work/firmware/user.bin').read_bytes(),'r2':(root/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes()}
report={'method':'SH-2A SLEIGH p-code execution; original instructions and calibration initialization; no hooks. Synthetic RAM and inputs; no physical plant.','images':{},'curve':[],'pd':[],'injection':[]}
def save():
    report['elapsed_seconds']=time.monotonic()-started
    (root/'outputs/THR_R2_emulator_validation.json').write_text(json.dumps(report,indent=2)+'\n')
def init(bank):
    c=e.CPU();c.writemem(0xfff82f04,4,(bank-1)*0x180);c.run(0x720dc);return c
def fresh(initial):
    c=e.CPU();c.ram[:]=initial.ram;c.stack[:]=initial.stack;return c
def curve(c,a):
    c.writemem(0xfff82fec,2,a);c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484))
    return e.signed(c.readmem(0xfff82ff6,2),2)
def oracle(rom,bank,raw):
    q=(bank-1)*0x300;w=lambda a:int.from_bytes(rom[a+q:a+q+2],'big',signed=True)
    xs=[w(0x57bae+2*i) for i in range(9)];ys=[w(0x57bc0+2*i) for i in range(9)]
    x=min(abs(raw),w(0x57bac));i=max(j for j,v in enumerate(xs) if v<=x);y=ys[i]
    if i<8:
        dx=xs[i+1]-xs[i];dy=ys[i+1]-ys[i];m=min(abs(dy),31*abs(dx))*((1<<26)//dx);d=x-xs[i]
        step=((m>>16)*d)//1024+((m&65535)*d)//(1<<26);y+=step if dy>=0 else -step
    return y*(-1 if raw<0 else 1 if raw>0 else 0)
def pd(c,T):
    for i,p in enumerate([0xfff82fc0,0xfff83004,0xfff8a498]):c.writemem(0x1000f000+i*4,4,p)
    c.run(0x7435c,(T,0xfff82fa0,0xfff82ff8,0xfff82ff0))
    return e.signed(c.readmem(0xfff83074,2),2)
def monitor(c):
    c.run(0x6acc4,(0xfff8a484,));c.run(0x6b010,(0xfff8a498,))
    c.run(0x4d358,(0,0,0xfff8e000))
    return dict(curve=c.readmem(0xfff8a5da,2),pd=c.readmem(0xfff8a5de,4),callback=c.readmem(0xfff8e000,1))

active=list(range(-1024,1025))+[-32768,-32767,-4096,-1025,1025,4096,32766,32767]
for name,rom in images.items():
    e.load_rom(rom);report['images'][name]=hashlib.sha256(rom).hexdigest()
    for bank in [1,2,3,7]:
        initial=init(bank);steps=0;digest=hashlib.sha256()
        for raw in active:
            c=fresh(initial);out=curve(c,raw);assert out==oracle(rom,bank,raw),(name,bank,raw,'oracle')
            for _ in range(3):c.run(0x6acc4,(0xfff8a484,))
            assert c.readmem(0xfff8a5da,2)==0 and c.readmem(0xfff8a622,6)==0,(name,bank,raw,'curve monitor')
            digest.update(struct.pack('>h',out));steps+=c.steps;assert not c.hooks
        report['curve'].append(dict(image=name,bank=bank,input_count=len(active),mismatches=0,monitor_faults=0,output_sha256=digest.hexdigest(),translation_steps=steps))
        print('curve',name,bank,'PASS',round(time.monotonic()-started,1),flush=True);save()
        # Same random cases for both images and every bank.
        rng=random.Random(0xA02002)
        cases=[dict(a=a,ref=ref,T=0,rate=0,W=16384) for a in [-1024,-400,0,400,1024] for ref in [-32765,-8000,-2000,0,2000,8000,32765]]
        cases += [dict(a=rng.randint(-1024,1024),ref=rng.randint(-32765,32765),T=rng.randint(-2176,2176),rate=rng.randint(-320,320),W=rng.randint(0,16384)) for _ in range(128)]
        digest=hashlib.sha256();steps=0;maximum=0;peak_cases=[]
        for item in cases:
            c=fresh(initial)
            for address,value in [(0xfff82f60,item['W']),(0xfff82f62,16384-item['W']),(0xfff82f64,16384),(0xfff83002,item['ref']),(0xfff82fb8,item['rate'])]:c.writemem(address,2,value)
            curve(c,item['a']);outs=[]
            for tick in range(4):
                u=pd(c,item['T']);ret,_=c.run(0x74c9c,(0,0));mix=e.signed(ret,4)
                flags=monitor(c)
                assert flags==dict(curve=0,pd=0,callback=0),(name,bank,item,tick,flags)
                limit=2560 if name=='r2' and bank<=3 else 1024
                assert abs(u)<=limit and mix==u,(name,bank,item,u,mix)
                outs.append(u);digest.update(struct.pack('>hh',u,mix));maximum=max(maximum,abs(u))
            if abs(item['a'])==1024 and item['ref']==0:
                peak_cases.append(dict(input=item,outputs=outs))
                if bank<=3:assert outs[-1]==(2090 if name=='r2' else 836)*(1 if item['a']>0 else -1)
            steps+=c.steps;assert not c.hooks
        report['pd'].append(dict(image=name,bank=bank,case_count=len(cases),ticks_per_case=4,monitor_faults=0,maximum_observed_abs_u=maximum,output_sha256=digest.hexdigest(),peak_cases=peak_cases,translation_steps=steps))
        print('PD',name,bank,'PASS',round(time.monotonic()-started,1),flush=True);save()
        # Confirm actual monitors still trip on inconsistent published snapshots.
        for kind in ['curve','pd']:
            c=fresh(initial)
            for address,value in [(0xfff82f60,16384),(0xfff82f62,0),(0xfff82f64,16384)]:c.writemem(address,2,value)
            curve(c,400);pd(c,0);pd(c,0)
            if kind=='curve':
                address=0xfff8a484+4;fn=0x6acc4;arg=0xfff8a484
            else:
                address=0xfff8a498+112;fn=0x6b010;arg=0xfff8a498
            c.writemem(address,2,c.readmem(address,2)^0x4000)
            flags=[]
            for _ in range(3):
                c.run(fn,(arg,));flags.append(c.readmem(0xfff8a5da,2) if kind=='curve' else c.readmem(0xfff8a5de,4))
            c.run(0x4d358,(0,0,0xfff8e000))
            assert flags[0]==flags[1]==0 and flags[2]!=0 and c.readmem(0xfff8e000,1)==2,(name,bank,kind,flags)
            report['injection'].append(dict(image=name,bank=bank,monitor=kind,corrupted_snapshot_address=hex(address),flags=flags,callback=2))
        print('injection',name,bank,'PASS',flush=True);save()
report['overall']='PASS_FOR_TESTED_SCOPES_ONLY';save();print('COMPLETE',round(time.monotonic()-started,1),flush=True)
