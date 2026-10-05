exec(open('work/emulation/test_boot.py').read().split('# Actual byte transform')[0])
for a,b in [(0x1ab0,0x1b62),(0x4744,0x4760)]:
 for i in e.CTX.disassemble(rom[a:b],a).instructions:print(hex(i.addr.offset),i.mnem,i.body)
