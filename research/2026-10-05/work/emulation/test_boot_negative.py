exec(open('work/emulation/test_boot.py').read().split('# Actual byte transform')[0])
results={}
for label,blob in [('corrupted_r2',rom[:0xc010]+bytes([rom[0xc010]^1])+rom[0xc011:])]:
 e.load_rom(blob);cpu=e.CPU();cpu.writemem(0xfff80c98,4,0xc000);cpu.writemem(0xfff80c9c,4,0x74000);cpu.writemem(0xfff80ca0,1,2);cpu.run(0x11c2,(),limit=20000000)
 results[label]={'return':cpu.getreg('r0'),'nrc':hex(cpu.readmem(0xfff80c4e,1)),'steps':cpu.steps};assert results[label]['return']==1 and results[label]['nrc']=='0x72'
e.load_rom(rom)
for flag in (0,1):
 cpu=e.CPU();cpu.writemem(0xfff80c98,4,0xc000);cpu.writemem(0xfff80c9c,4,0x74000);cpu.writemem(0xfff80ca0,1,flag);cpu.run(0x11c2,(),limit=300000)
 results['record_flag_'+str(flag)]={'return':cpu.getreg('r0'),'nrc':hex(cpu.readmem(0xfff80c4e,1))}
(out/'THR_boot_negative_execution.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
