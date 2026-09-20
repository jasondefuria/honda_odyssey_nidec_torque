from pathlib import Path
import sys,contextlib,io,json,hashlib
sys.path.insert(0,'work');import analyze as a
b=a.B
expected='e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
assert hashlib.sha256(b).hexdigest()==expected
assert b==Path('outputs/user.original.bin').read_bytes()
assert 36323328==8868*4096
# Check the instruction bytes that encode the ramp endpoint and increments.
anchors={0x1962a:'06212a40',0x196b0:'0420378f',0x196d4:'04406f1e',0x1979e:'0df1e9d4',0x197a8:'7d6a',0x197c6:'0ed0c871',0x197ee:'02f0721c',0x2aa5c:'0000122a',0x2aa62:'0000042a',0x2aaaa:'0000110f',0x2aab0:'000003ed'}
for p,h in anchors.items():assert b[p:p+len(h)//2].hex()==h
rows=[]
for q in (1536,2560,4352):
 lim=q&~1;gain=0x3fffffff//(q//2)
 rows.append({'q':q,'limit':lim,'reciprocal_gain':gain,'normalized_positive_limit':lim*gain//32768})
Path('outputs/runtime_constraints_verification.json').write_text(json.dumps({'sha256':expected,'original_unchanged':True,'allowance_max_stored':36323328,'allowance_max_command':8868,'steps':[{'stored':v,'command_per_update':v/4096} for v in (145295,290590,-1452950,-145295,-36324)],'instruction_anchors':{hex(k):v for k,v in anchors.items()},'normalization_examples':rows,'scope':'Byte and arithmetic checks; not runtime validation or independent proof of all dataflow.'},indent=2)+'\n')
s=io.StringIO()
with contextlib.redirect_stdout(s):
 print('Original SHA256 '+expected+'\nLinear disassembly includes inline pools; not every decoded line is executed.\n')
 for lo,hi in [(0x19600,0x19848),(0x29c48,0x29f40),(0x2a96c,0x2aace),(0x38c90,0x38dd0),(0x275ec,0x27600)]:
  print(f'\nWINDOW {lo:X}..{hi:X}');a.dump(lo,hi)
Path('outputs/runtime_constraints_disassembly.txt').write_text(s.getvalue())
print(json.dumps(rows))
