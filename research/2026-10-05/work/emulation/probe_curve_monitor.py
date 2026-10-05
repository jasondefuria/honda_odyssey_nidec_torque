import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as emu
root=Path(__file__).resolve().parents[2]
rows=[]
for name,filename in [('stock','user.bin'),('candidate','THR_A020_2p5_peak_BENCH_ONLY_UNVALIDATED.bin')]:
    rom=(root/'work/firmware'/filename).read_bytes();emu.load_rom(rom)
    for bank in [1,2,3,7]:
        for raw in [0,128,400,896,1024,-400,-1024]:
            c=emu.CPU();off=(bank-1)*0x300
            c.writemem(0x1000f000,4,1)
            c.run(0x306ce,(0x57bae+off,0x57bc0+off,0xfff83168,9))
            c.run(0x306ce,(0x67bc4+off,0x67bd6+off,0xfff8a574,9))
            c.writemem(0xfff82f04,4,off//2)
            runs=[]
            for tick in range(5):
                c.writemem(0xfff82fec,2,raw)
                c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484))
                c.run(0x6acc4,(0xfff8a484,))
                runs.append(dict(output=emu.signed(c.readmem(0xfff82ff6,2),2),
                    snapshot=[emu.signed(c.readmem(0xfff8a484+2*i,2),2) for i in range(4)],
                    counters=[c.readmem(0xfff8a622+2*i,2) for i in range(3)],flags=c.readmem(0xfff8a5da,2)))
            rows.append(dict(image=name,bank=bank,raw=raw,runs=runs,steps=c.steps))
            print(json.dumps(rows[-1]),flush=True)
(root/'outputs/THR_2p5_emulator_curve_monitor.json').write_text(json.dumps(rows,indent=2)+'\n')
