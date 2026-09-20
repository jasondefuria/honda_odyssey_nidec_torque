import sys
from pathlib import Path
import analyze
if not Path('work/civic-stock-rom.bin').exists():
 import ast
 tree=ast.parse(Path('work/nrdr-reference/openpilot/nrdr/tools/eps/check_rwd.py').read_text())
 lut=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DECRYPT_LOOKUP' for t in n.targets))
 b=Path('work/civic-a030/repository/stock-39990-TBA-A030.rwd').read_bytes();i=3
 for _ in range(6):
  count=b[i];i+=1
  for _ in range(count):s=b[i];i+=1+s
 start=int.from_bytes(b[i:i+4],'big');size=int.from_bytes(b[i+4:i+8],'big');i+=8
 Path('work/civic-stock-rom.bin').write_bytes(bytes(start)+bytes(lut[x] for x in b[i:i+size]))
analyze.B=Path('work/civic-stock-rom.bin').read_bytes()
if sys.argv[1]=='dump':analyze.dump(int(sys.argv[2],16),int(sys.argv[3],16))
if sys.argv[1]=='refs':
 for v in sys.argv[2:]:print('Target',v);analyze.refs(int(v,16))
