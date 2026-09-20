from pathlib import Path
import json,hashlib
b=Path('work/pilot-a060/stock-rom.bin').read_bytes();u=lambda a:int.from_bytes(b[a:a+4],'little')
assert b[0x10140:0x1014c].hex()=='04000000e400000000010100'
assert u(0x10258)==0x40fe4 and u(0x12828)==0x40534
assert b[0x10074:0x10078].hex()=='0303000a'
assert b[0x12824:0x12828].hex()=='01000100'
r={'rom_table_base_inferred':hex(0x12000),'base_evidence':'Multiple tp-relative accesses align descriptor, policy, callback and dispatcher tables; no tp initialization captured.','hardware_slot':10,'descriptor_address':'0x10140','descriptor_hex':b[0x10140:0x1014c].hex(),'can_id':hex(u(0x10144)),'logical_rx_index':b[0x1014a],'driver_callback':'0x40FE4','payload_parser':'0x40534','policy':b[0x10074:0x10078].hex(),'checksum_seed':8+14+4,'reference_hash':hashlib.sha256(Path('work/pilot-a060/39990-TG7-A060-2X (2019 Honda Pilot)').read_bytes()).hexdigest(),'scope':'Static routing and byte verification; no hardware execution.'}
Path('outputs/pilot_can_verification.json').write_text(json.dumps(r,indent=2)+'\n')
lines=Path('work/pilot-disassembly.txt').read_text().splitlines();ranges=[(0x422d0,0x4236c),(0x4704e,0x470a0),(0x40b50,0x40be4),(0x40eaa,0x41074),(0x412d2,0x41370),(0x41530,0x41568),(0x40534,0x40558),(0x408a6,0x408c8),(0x41a84,0x41a90)]
o=['V850 LE32. tp-relative ROM base 0x12000 is inferred from consistent table alignment; gp remains symbolic.']
for a,z in ranges:
 o.append(f'\nWINDOW {a:X}..{z:X}');o.extend(l for l in lines if a<=int(l.split()[0],16)<z)
Path('outputs/pilot_can_disassembly.txt').write_text('\n'.join(o)+'\n')
print('Descriptor and callback anchors verified')
