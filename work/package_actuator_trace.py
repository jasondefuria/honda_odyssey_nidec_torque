from pathlib import Path
import sys, io, contextlib, hashlib, json
sys.path.insert(0,'work')
import analyze
b=analyze.B
expected='e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
assert hashlib.sha256(b).hexdigest()==expected
assert b==Path('outputs/user.original.bin').read_bytes()
u16=lambda a:int.from_bytes(b[a:a+2],'big')
pairs=[(0x57bac,0x67bc2,2),(0x57bae,0x67bc4,18),(0x57bc0,0x67bd6,18)]
checks=[]
for bank in range(7):
 for a,c,n in pairs:
  a+=bank*0x300;c+=bank*0x300
  assert b[a:a+n]==b[c:c+n]
  checks.append({'bank':bank+1,'main':hex(a),'monitor':hex(c),'bytes':n,'equal':True})
assert [u16(0x398cc+2*i) for i in range(3)]==[255,86,255]
assert b[0x28208:0x2821a].hex()=='e2824218325110143261101332411015006b'
counts=[min(2030,(((32768-(v&65535))&65535)*2031)>>16) for v in range(-32767,32768)]
assert min(counts)==0 and max(counts)==2030
assert all(a>=c for a,c in zip(counts,counts[1:]))
Path('outputs/actuator_trace_verification.json').write_text(json.dumps({'sha256':expected,'preserved_copy_identical':True,'parallel_calibrations':checks,'debounce_parameters':[255,86,255],'three_failure_counter_sequence':[86,172,255],'hardware_base':hex((-126<<8)&0xffffffff),'hardware_registers':['0xFFFF8228','0xFFFF8226','0xFFFF822A'],'count_conversion_exhaustive_signed_range':[-32767,32767],'count_range':[min(counts),max(counts)],'count_conversion_monotone':True,'scope':'Byte/arithmetic checks support, but do not independently prove, static dataflow.'},indent=2)+'\n')
ranges=[(0x727e4,0x7293c),(0x6acc4,0x6af30),(0x19d92,0x1a258),(0x38438,0x384a0),(0x385a6,0x386a0),(0x1a700,0x1a7b0),(0x291de,0x29748),(0x2a1be,0x2a312),(0x2a6e2,0x2a970),(0x29b4c,0x29c48),(0x28208,0x2821a)]
s=io.StringIO()
with contextlib.redirect_stdout(s):
 print('THR-A020 original SHA256 '+expected)
 print('SH-2A big endian. Linear windows may contain inline literals decoded as instructions.\n')
 for a,z in ranges:
  print(f'\nWINDOW {a:05X}..{z:05X} (end exclusive)')
  analyze.dump(a,z)
Path('outputs/monitor_actuator_disassembly.txt').write_text(s.getvalue())
print('Parallel tables match in all seven banks; hardware writes and count arithmetic verified; original unchanged.')
