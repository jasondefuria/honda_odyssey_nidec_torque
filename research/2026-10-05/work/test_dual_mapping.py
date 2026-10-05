exec(open('work/dual_ranges.py').read().split('for pair in sys.argv')[0])
sys.path.insert(0,str(R/'work/emulation'));import sh2a_pcode as em
em.load_rom(d);rows=[]
for a,b,k in [(0,0,4096),(100,90,4096),(90,100,4096),(2,32766,4096),(32766,2,4096),(16384,0,4096),(0,16384,4096),(1200,1000,1000)]:
 c=em.CPU();c.writemem(0xfff85390,4,0);c.writemem(0xfff80bb2,2,k);c.run(0x1c068,(a,b,0,0xfff8028c))
 delta=max(-32767,min(32767,a-b))
 if delta>16383:delta-=32768
 elif delta< -16383:delta+=32768
 expected=max(-32767,min(32767,(delta*k)>>7));actual=em.signed(c.readmem(0xfff8029c,2),2)
 rows.append(dict(a=a,b=b,k=k,delta=delta,expected=expected,actual=actual,match=expected==actual))
out={'scope':'Original v4 instructions, synthetic RAM, no peripheral or physical timing model','sample_delta_cases':rows,'all_match':all(r['match'] for r in rows)}
(R/'outputs/dual_ecu_reconstruction/feedback_delta_execution.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
