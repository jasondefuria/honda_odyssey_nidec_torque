from pathlib import Path
import sys,io,contextlib,json,hashlib
sys.path.insert(0,'work');import analyze as a
b=a.B
expected='e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
assert hashlib.sha256(b).hexdigest()==expected
assert b==Path('outputs/user.original.bin').read_bytes()
assert b[0x4f62c:0x4f642]==bytes(22)
anchors={0x2de7e:'c8c0',0x772d8:'85e9',0x772da:'220b',0x769e0:'b19b',0x769e2:'e401',0x77696:'b1fe',0x77698:'e401',0x76d3e:'8066',0x76d42:'8067',0x773de:'2421',0x343e2:'25d0'}
for p,h in anchors.items():assert b[p:p+len(h)//2].hex()==h
s=io.StringIO()
with contextlib.redirect_stdout(s):
 print('Original SHA256: '+expected+'\nStatic windows include literal pools; not every decoded line is executable.\n')
 for lo,hi in [(0x2de7a,0x2de84),(0x4b658,0x4b8c8),(0x7698c,0x769f0),(0x76d1a,0x76d4c),(0x77260,0x77412),(0x7765c,0x776a8),(0x77a96,0x77b52),(0x343ca,0x3440a)]:
  print(f'\nWINDOW {lo:X}..{hi:X}');a.dump(lo,hi)
Path('outputs/odyssey_fault_effect_disassembly.txt').write_text(s.getvalue())
Path('outputs/odyssey_fault_effect_verification.json').write_text(json.dumps({'sha256':expected,'original_unchanged':True,'zero_template':{'address':'0x4F62C','length':22,'all_zero':True},'instruction_anchors':{hex(k):v for k,v in anchors.items()},'scope':'Static byte checks, not runtime execution or physical torque validation.'},indent=2)+'\n')
print('Original hash, preserved copy, zero template and instruction anchors verified.')
