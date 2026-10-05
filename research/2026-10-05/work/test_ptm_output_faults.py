exec(open('work/test_final_ptm.py').read().split('results={};errors=[]')[0])
rows=[]
for name,rom in roms.items():
 em.load_rom(rom)
 for bank,delta in itertools.product(range(1,8),[-512,-100,-1,1,100,512]):
  c=init(bank);ts=[tick(c,bank,400,0,corrupt=(0x70,2,delta)) for _ in range(8)]
  rows.append(dict(image=name,bank=bank,delta=delta,detected=any(t['pd_flags'] for t in ts),flags=sorted(set(t['pd_flags'] for t in ts))))
 print('Output corruption',name,'completed',flush=True)
(O/'output_fault_comparison.json').write_text(json.dumps(rows,indent=2))
