exec(open('work/emulation/validate_r2.py').read().split("report={'method'")[0])
rom=(root/'outputs/ccp_capture/THR_boot_0000_1FFF.bin').read_bytes()+images['stock'][0x2000:]
e.load_rom(rom)
for a,b in [(0xa00,0xa60),(0x11be,0x133e),(0x14ce,0x1550),(0x1b18,0x1b90),(0x1f1c,0x1f90),(0x1378,0x13d0),(0x1ae0,0x1b18),(0x1ef6,0x1f1c)]:
 print('\nREGION',hex(a))
 for i in e.CTX.disassemble(rom[a:b],a).instructions:print(hex(i.addr.offset),i.mnem,i.body)
