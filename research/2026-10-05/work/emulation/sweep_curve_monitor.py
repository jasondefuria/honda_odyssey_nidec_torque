"""Execute the ROM curve and monitor for every active-range integer input."""
import sys,json,hashlib,time
from pathlib import Path
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as emu
root=Path(__file__).resolve().parents[2]
lookup=bytes(json.loads((root/'work/tla-decrypt-lookup.json').read_text()))
stock=(root/'work/firmware/user.bin').read_bytes()
rwd=(root/'outputs/39990-THR-A020_2p5_PEAK_EXPERIMENTAL_UNVALIDATED.rwd').read_bytes()
candidate=stock[:0xc000]+rwd[-0x74004:-4].translate(lookup)
assert hashlib.sha256(candidate).hexdigest()=='04b48282b8350c2f987af2efe5c59bc73d62fe6bc3ddfbf01eed06b5d27f5189'

def oracle(rom,raw):
    w=lambda addr:int.from_bytes(rom[addr:addr+2],'big',signed=True)
    xs=[w(0x57bae+2*i) for i in range(9)]
    ys=[w(0x57bc0+2*i) for i in range(9)]
    x=min(abs(raw),w(0x57bac));i=max(j for j,v in enumerate(xs) if v<=x)
    y=ys[i]
    if i<8:
        dx=xs[i+1]-xs[i];dy=ys[i+1]-ys[i]
        slope=min(abs(dy),31*abs(dx))*((1<<26)//dx)
        d=x-xs[i];step=((slope>>16)*d)//1024+((slope&65535)*d)//(1<<26)
        y+=step if dy>=0 else -step
    return y*(-1 if raw<0 else 1 if raw>0 else 0)

results=[];started=time.monotonic()
for name,rom in [('stock',stock),('rwd_candidate',candidate)]:
    emu.load_rom(rom);init=emu.CPU();init.writemem(0x1000f000,4,1)
    init.run(0x306ce,(0x57bae,0x57bc0,0xfff83168,9))
    init.run(0x306ce,(0x67bc4,0x67bd6,0xfff8a574,9))
    init.writemem(0xfff82f04,4,0)
    cases=[];steps=0;visited=set()
    inputs=list(range(-1024,1025))+[-32768,-32767,-4096,-1025,1025,4096,32766,32767]
    for index,raw in enumerate(inputs):
        c=emu.CPU();c.ram[:]=init.ram;c.stack[:]=init.stack
        c.writemem(0xfff82fec,2,raw)
        c.run(0x7415c,(0xfff82fc0,0xfff82ff0,0xfff8a484))
        output=emu.signed(c.readmem(0xfff82ff6,2),2)
        assert output==oracle(rom,raw),(name,raw,output,oracle(rom,raw))
        states=[]
        for _ in range(3):
            c.run(0x6acc4,(0xfff8a484,))
            states.append(dict(counter=c.readmem(0xfff8a624,2),flag=c.readmem(0xfff8a5db,1)))
        c.run(0x4d358,(0,0,0xfff8e000))
        callback=c.readmem(0xfff8e000,1)
        c.run(0x4bcda,(callback,0,0xfff8e002))
        response=c.readmem(0xfff8e002,1)
        cases.append(dict(input=raw,output=output,monitor=states,callback=callback,response=response))
        assert not c.hooks
        if name=='stock':assert states[-1]['flag']==0 and callback==0 and response==0
        elif raw!=0:assert states==[{'counter':86,'flag':0},{'counter':172,'flag':0},{'counter':255,'flag':2}] and callback==2 and response==128
        else:assert states[-1]['flag']==0 and callback==0 and response==0
        steps+=c.steps;visited.update(c.visited)
        if index%256==0:print(name,index+1,'/',len(inputs),'elapsed',round(time.monotonic()-started,1),flush=True)
    results.append(dict(image=name,rom_sha256=hashlib.sha256(rom).hexdigest(),
        input_count=len(inputs),active_range_input_count=2049,extra_boundary_count=8,
        fixed_point_oracle_mismatches=0,monitor_fault_cases=sum(x['monitor'][-1]['flag']!=0 for x in cases),
        callback_fault_cases=sum(x['callback']==2 for x in cases),response_fault_cases=sum(x['response']==128 for x in cases),
        translation_steps=steps,visited_pcs=[hex(v) for v in sorted(visited)],cases=cases))
    (root/'outputs/THR_2p5_emulator_sweep.json').write_text(json.dumps(dict(method='SH-2A SLEIGH p-code execution; original routines, no hooks; synthetic RAM. Candidate reconstructed from delivered RWD.',elapsed_seconds=time.monotonic()-started,results=results),indent=2)+'\n')
print('COMPLETE',round(time.monotonic()-started,1),flush=True)
