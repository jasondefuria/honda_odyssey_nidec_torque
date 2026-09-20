#!/usr/bin/env python3
"""Read-only, standard-library verification of the analyzed Odyssey THR-A020 image.
Usage: python3 verify_user_bin.py /path/to/user.bin
Addresses below are image offsets, equal to the ROM addresses used in the report.
This verifies bytes and mathematical claims, not all static control/data flow.
"""
import hashlib, json, math, sys
from pathlib import Path
b = Path(sys.argv[1]).read_bytes()
u16 = lambda a: int.from_bytes(b[a:a+2], 'big')
s16 = lambda a: int.from_bytes(b[a:a+2], 'big', signed=True)
u32 = lambda a: int.from_bytes(b[a:a+4], 'big')
expected = 'e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
assert len(b) == 0x80000, 'Unexpected image size'
assert hashlib.sha256(b).hexdigest() == expected, 'Different image: findings must be reassessed'
def crc_raw(data, crc=0xffffffff):
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            crc = ((crc << 1) ^ (0x04c11db7 if crc & 0x80000000 else 0)) & 0xffffffff
    return crc
checks = {}
checks['sha256'] = expected
checks['size'] = len(b)
checks['can_slot_22_record'] = b[0x3dbf0:0x3dc00].hex()
assert checks['can_slot_22_record'] == '0000000000e400000000000005010000'
assert 0x3da90 + 22 * 16 == 0x3dbf0
atan = [u16(0x3a128 + 2*i) for i in range(2049)]
assert atan == [round(math.atan(i/2048)*8192/math.pi) for i in range(2049)]
checks['arctangent_table'] = {'start':'0x3A128', 'entries':2049, 'last':atan[-1], 'exact_formula_match':True}
checks['octant_offsets'] = [s16(0x3b12a+2*i) for i in range(8)]
additive = sum(u16(a) for a in range(0xc000,0x7ff80,2)) & 0xffff
assert additive == u16(0x7ff80) == 0xd0ca
checks['additive_checksum'] = {'range':'[0xC000,0x7FF80)', 'computed':hex(additive), 'stored':hex(u16(0x7ff80))}
checks['crc_blocks'] = []
for start in (0x40000,0x60000):
    end = start+0xff60
    trailer = start+0xff7c
    raw = crc_raw(b[start:end])
    stored = u32(trailer)
    assert stored == (raw ^ 0xffffffff)
    residue = crc_raw(b[trailer:trailer+4], raw)
    assert residue == 0xc704dd7b
    checks['crc_blocks'].append({'range':f'[{start:#x},{end:#x})', 'trailer_address':hex(trailer), 'raw_crc':hex(raw), 'stored_complement':hex(stored), 'residue':hex(residue)})
for i in range(256):
    assert u32(0xf05c+4*i) == crc_raw(bytes([i]), 0)
checks['crc_table_matches_polynomial_04C11DB7'] = True
fields = {'fault_command_clamp':0x57cda,'command_monitor_upper':0x57cd6,'command_monitor_lower':0x57cd8,'nonlinear_input_clamp':0x57bac,'feedback_filter_coefficient':0x57bd2,'feedback_clamp':0x57bd4,'difference_term_clamp':0x57bd6,'proportional_term_clamp':0x57bd8,'combined_term_clamp':0x57bda,'later_combination_clamp':0x57c94}
checks['calibration_banks'] = [{name:s16(addr+bank*0x300) for name,addr in fields.items()} for bank in range(7)]
checks['curves_bank_1'] = {name:[s16(addr+2*i) for i in range(9)] for name,addr in {'command_limit_axis':0x57b2a,'command_limit_values':0x57b3c,'nonlinear_axis':0x57bae,'nonlinear_values':0x57bc0,'difference_gain_axis':0x57c4c,'difference_gain_values':0x57c5e,'proportional_gain_axis':0x57c70,'proportional_gain_values':0x57c82}.items()}
checks['final_multiplier_at_500A6'] = s16(0x500a6)
checks['unresolved_tail_words'] = [hex(u32(0x7fff8)),hex(u32(0x7fffc))]
print(json.dumps(checks, indent=2))
