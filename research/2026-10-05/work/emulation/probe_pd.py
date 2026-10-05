import sys,json
from pathlib import Path
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as emu
root=Path(__file__).resolve().parents[2]
rows=[]
for name,filename in [('stock','user.bin'),('candidate','THR_A020_2p5_peak_BENCH_ONLY_UNVALIDATED.bin')]:
    emu.load_rom((root/'work/firmware'/filename).read_bytes())
    for a,ref in [(1024,0),(-1024,0),(400,0),(1024,2000),(1024,-1000),(1024,4864),(-1024,-2000),(1024,-32765)]:
        c=emu.CPU();c.writemem(0xfff82f04,4,0)
        c.run(0x720dc)
        c.writemem(0xfff82f60,2,16384);c.writemem(0xfff82f62,2,0);c.writemem(0xfff82f64,2,16384)
        c.writemem(0xfff82fec,2,a);c.writemem(0xfff83002,2,ref)
        c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484))
        ticks=[]
        for tick in range(3):
            for i,p in enumerate([0xfff82fc0,0xfff83004,0xfff8a498]):c.writemem(0x1000f000+4*i,4,p)
            c.run(0x7435c,(0,0xfff82fa0,0xfff82ff8,0xfff82ff0))
            u=emu.signed(c.readmem(0xfff83074,2),2)
            ret,_=c.run(0x74c9c,(0,0))
            ticks.append(dict(u=u,mixer_return=emu.signed(ret,4)))
        r=dict(image=name,a=a,ref=ref,curve=emu.signed(c.readmem(0xfff82ff6,2),2),ticks=ticks,steps=c.steps,visited=len(c.visited))
        rows.append(r);print(json.dumps(r),flush=True)
(root/'outputs/THR_2p5_emulator_pd.json').write_text(json.dumps(rows,indent=2)+'\n')
