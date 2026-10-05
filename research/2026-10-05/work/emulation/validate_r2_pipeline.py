"""Directed actual preprocessing/fade/PD/mixer and monitor executions."""
import sys,json,hashlib,time
from pathlib import Path
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as e
root=Path(__file__).resolve().parents[2];started=time.monotonic();rows=[];hashes={}
for name,filename in [('stock','user.bin'),('r2','THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin')]:
    rom=(root/'work/firmware'/filename).read_bytes();e.load_rom(rom);hashes[name]=hashlib.sha256(rom).hexdigest()
    for bank in [1,2,3,7]:
        initial=e.CPU();initial.writemem(0xfff82f04,4,(bank-1)*0x180);initial.run(0x720dc)
        for command in [-4096,-2048,0,2048,4096]:
            for T in [-900,-768,-767,0,767,768,900]:
                c=e.CPU();c.ram[:]=initial.ram;c.stack[:]=initial.stack
                for address,value in [(0xfff82f60,16384),(0xfff82f62,0),(0xfff82f64,16384),(0xfff8500c,command),(0xfff8500a,60),(0xfff80016,T)]:c.writemem(address,2,value)
                ticks=[]
                for tick in range(5):
                    c.run(0x7276a,(0xfff8500c,0))
                    ret,_=c.run(0x74c9c,(0,0))
                    for fn,arg in [(0x6a700,0xfff8a454),(0x6acc4,0xfff8a484),(0x6b010,0xfff8a498),(0x6be98,0xfff8a50c)]:c.run(fn,(arg,))
                    c.run(0x4d358,(0,0,0xfff8e000))
                    u=e.signed(c.readmem(0xfff83074,2),2)
                    out=e.signed(ret,4);fade=e.signed(c.readmem(0xfff82fec,2),2)
                    assert c.readmem(0xfff8e000,1)==0 and c.readmem(0xfff8a5cc,24)==0,(name,bank,command,T,tick,'monitor')
                    assert u==out and abs(u)<=(2560 if name=='r2' and bank<=3 else 1024)
                    if abs(T)>=768:assert fade==u==0,(name,bank,T,'override')
                    if command==0:assert fade==u==0
                    ticks.append(dict(u=u,mixer=out,after_fade=fade))
                if T==0 and abs(command)==4096 and bank<=3:
                    assert ticks[-1]['u']==(2090 if name=='r2' else 836)*(1 if command>0 else -1)
                assert not c.hooks
                rows.append(dict(image=name,bank=bank,command=command,driver_input=T,ticks=ticks,monitor_faults=0,translation_steps=c.steps))
        print(name,bank,'PASS',round(time.monotonic()-started,1),flush=True)
# Only source and gain-bank offsets differ; unchanged bank 7 must stay identical.
a=[x for x in rows if x['image']=='stock' and x['bank']==7]
b=[x for x in rows if x['image']=='r2' and x['bank']==7]
assert [x['ticks'] for x in a]==[x['ticks'] for x in b]
result=dict(status='PASS_FOR_TESTED_SCOPES_ONLY',images=hashes,scope='Actual ROM 7276A -> 74C9C, fade/curve/PD/mixer monitors and diagnostic callback; forced full weights, zero feedback/base assist, speed 60 counts, synthetic RAM. No engagement state machine, CAN hardware or physical plant.',case_count=len(rows),ticks_per_case=5,elapsed_seconds=time.monotonic()-started,cases=rows)
(root/'outputs/THR_R2_pipeline_validation.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPLETE',len(rows),flush=True)
