"""Compare actual decoded stock/R1/R2 RWDs in an identical SH-2A harness."""
import sys,json,hashlib,time,struct
from pathlib import Path
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as e
root=Path(__file__).resolve().parents[2];start_time=time.monotonic()
stock=(root/'work/firmware/user.bin').read_bytes()
lookup=bytes(json.loads((root/'work/tla-decrypt-lookup.json').read_text()))
files={'stock':root/'work/imported/39990-THR-A020_stock_pure.rwd',
       'r1':root/'outputs/39990-THR-A020_2p5_PEAK_EXPERIMENTAL_UNVALIDATED.rwd',
       'r2':root/'outputs/39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd'}
expected={'stock':'e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2','r1':'04b48282b8350c2f987af2efe5c59bc73d62fe6bc3ddfbf01eed06b5d27f5189','r2':'688f36d6fb0c3b0ae1a3c8d620c509f7279f015b5d74eb05fd98e2abf9b5847c'}
digest=lambda b:hashlib.sha256(b).hexdigest()
def parse(b):
    assert b[:3]==b'Z\r\n';p=3;headers=[]
    for _ in range(6):
        n=b[p];p+=1;items=[]
        for _ in range(n):
            size=b[p];p+=1;items.append(b[p:p+size].hex());p+=size
        headers.append(items)
    a,n=struct.unpack('>II',b[p:p+8]);p+=8
    assert (a,n)==(0xc000,0x74000) and p+n+4==len(b)
    assert int.from_bytes(b[-4:],'little')==sum(b[:-4])&0xffffffff
    return headers,p,b[p:p+n].translate(lookup)
roms={};file_info={}
for name,path in files.items():
    raw=path.read_bytes();headers,offset,plain=parse(raw);rom=stock[:0xc000]+plain
    assert digest(rom)==expected[name]
    roms[name]=rom
    file_info[name]=dict(name=path.name,rwd_sha256=digest(raw),rom_sha256=digest(rom),rwd_bytes=len(raw),firmware_changed_bytes_from_stock=sum(a!=b for a,b in zip(stock,rom)),headers=headers)
assert file_info['stock']['headers']==file_info['r1']['headers']==file_info['r2']['headers']
file_info['r2']['changed_bytes_from_r1']=sum(a!=b for a,b in zip(roms['r1'],roms['r2']))

def new_cpu(initial):
    c=e.CPU();c.ram[:]=initial.ram;c.stack[:]=initial.stack
    for a,v in [(0xfff82f60,16384),(0xfff82f62,0),(0xfff82f64,16384),(0xfff8500a,60)]:c.writemem(a,2,v)
    return c
def tick(c,command,ref,T):
    for address,value in [(0xfff8500c,command),(0xfff83002,ref),(0xfff80016,T)]:c.writemem(address,2,value)
    c.run(0x7276a,(0xfff8500c,0));ret,_=c.run(0x74c9c,(0,0))
    for fn,arg in [(0x6a700,0xfff8a454),(0x6acc4,0xfff8a484),(0x6b010,0xfff8a498),(0x6be98,0xfff8a50c)]:c.run(fn,(arg,))
    c.run(0x4d358,(0,0,0xfff8e000))
    c.run(0x4bcda,(c.readmem(0xfff8e000,1),0,0xfff8e002))
    assert not c.hooks
    return dict(command=command,ref=ref,driver_input=T,
        faded_input=e.signed(c.readmem(0xfff82fec,2),2),curve=e.signed(c.readmem(0xfff82ff6,2),2),
        controller_u=e.signed(c.readmem(0xfff83074,2),2),mixer=e.signed(ret,4),
        curve_flags=c.readmem(0xfff8a5da,2),pd_flags=c.readmem(0xfff8a5de,4),
        aggregate_callback=c.readmem(0xfff8e000,1),response=c.readmem(0xfff8e002,1))

rows=[];sequences=[];summary={}
for image,rom in roms.items():
    e.load_rom(rom);summary[image]={'steps':0}
    for bank in [1,2,3,7]:
        initial=e.CPU();initial.writemem(0xfff82f04,4,(bank-1)*0x180);initial.run(0x720dc)
        for command in [-4096,-2048,-512,0,512,2048,4096]:
            for ref in [-2000,0,2000]:
                for T in [0,767,768]:
                    c=new_cpu(initial);ticks=[tick(c,command,ref,T) for _ in range(6)]
                    rows.append(dict(image=image,bank=bank,command=command,ref=ref,driver_input=T,ticks=ticks))
                    summary[image]['steps']+=c.steps
                    if image!='r1' or bank==7:assert all(t['aggregate_callback']==0 for t in ticks),(image,bank,command,ref,T,ticks)
        if bank==1:
            scenarios={
                'step_release_reverse':[(v,0,0) for v in [0]*3+[4096]*5+[0]*5+[-4096]*5+[0]*5],
                'command_ramp':[(v,0,0) for v in list(range(-4096,4097,256))],
                'driver_override_boundary':[(4096,0,T) for T in [0]*4+[767]*4+[768]*4+[900]*4+[0]*4],
                'feedback_sweep':[(4096,r,0) for r in [-8000,-4000,-2000,0,2000,4000,8000,16000,32765,0]],
            }
            for name,inputs in scenarios.items():
                c=new_cpu(initial);ticks=[tick(c,*values) for values in inputs]
                sequences.append(dict(image=image,scenario=name,ticks=ticks))
                summary[image]['steps']+=c.steps
                if image!='r1':assert all(t['aggregate_callback']==0 for t in ticks),(image,name,ticks)
        print(image,bank,'done',round(time.monotonic()-start_time,1),flush=True)

index={(x['image'],x['bank'],x['command'],x['ref'],x['driver_input']):x for x in rows}
output_keys=['faded_input','curve','controller_u','mixer']
for row in rows:
    if row['image']!='r2':continue
    key=(row['bank'],row['command'],row['ref'],row['driver_input'])
    r1=index[('r1',*key)];st=index[('stock',*key)]
    assert all(all(a[k]==b[k] for k in output_keys) for a,b in zip(row['ticks'],r1['ticks']))
    if row['bank']==7:assert row['ticks']==st['ticks']
for scenario in ['step_release_reverse','command_ramp','driver_override_boundary','feedback_sweep']:
    a=next(x for x in sequences if x['image']=='r1' and x['scenario']==scenario)
    b=next(x for x in sequences if x['image']=='r2' and x['scenario']==scenario)
    assert all(all(p[k]==q[k] for k in output_keys) for p,q in zip(a['ticks'],b['ticks']))
for image in roms:
    subset=[r for r in rows if r['image']==image]
    dyn=[r for r in sequences if r['image']==image]
    summary[image].update(static_cases=len(subset),static_monitor_fault_cases=sum(any(t['aggregate_callback'] for t in r['ticks']) for r in subset),sequence_count=len(dyn),sequence_ticks=sum(len(r['ticks']) for r in dyn),sequence_fault_ticks=sum(bool(t['aggregate_callback']) for r in dyn for t in r['ticks']))
selected=[]
for command,ref,T in [(512,0,0),(2048,0,0),(4096,0,0),(-4096,0,0),(4096,2000,0),(4096,-2000,0),(4096,0,767),(4096,0,768)]:
    record=dict(command=command,ref=ref,driver_input=T)
    for image in roms:
        case=index[(image,1,command,ref,T)]
        record[image]=dict(first_u=case['ticks'][0]['controller_u'],steady_u=case['ticks'][-1]['controller_u'],fault=bool(case['ticks'][-1]['aggregate_callback']))
    old=record['stock']['steady_u'];record['r2_to_stock_ratio']=record['r2']['steady_u']/old if old else None
    selected.append(record)
result=dict(status='COMPARISON_COMPLETE',method='Actual decoded RWD applications executed through SH-2A SLEIGH/pypcode, identical inputs, zero base assist and fixed full authority; synthetic feedback, no physical plant. Monitor callback is observed but full fault publication/state-machine scheduling is not executed, so continued R1 output after a flag is not a prediction of vehicle behavior.',files=file_info,summary=summary,selected=selected,static_cases=rows,sequences=sequences,r1_r2_controller_outputs_identical_in_tested_cases=True,bank7_identical_in_tested_cases=True,elapsed_seconds=time.monotonic()-start_time)
(root/'outputs/THR_stock_R1_R2_emulation_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True);print('COMPLETE',flush=True)
