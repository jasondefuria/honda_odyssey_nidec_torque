from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];s=(root/'work/firmware/user.bin').read_bytes();d=(root/'outputs/ccp_capture/THR_CCP_MAPPED_VIEW_00000_7FFFF.bin').read_bytes();r=(root/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes();lut=json.loads((root/'work/tla-decrypt-lookup.json').read_text())
print('lookup type',type(lut).__name__)
if isinstance(lut,dict): print(lut.keys())
profiles=[{'index':i,'key_hex':s[0x5eb00+i*0x46:0x5eb05+i*0x46].hex(),'selector':s[0x5eb10+i*0x46]} for i in range(14)]
res={'log_sha256':hashlib.sha256(Path('/Users/jasondefuria/Downloads/RUNNING_LOG.md').read_bytes()).hexdigest(),'alias_pointer_table_matches':[d[a:a+436]==s[0x5fc00:0x5fdb4] for a in (0x1fc00,0x2fc00,0x3fc00)],'profiles':profiles,'r2_magic':r[0xc000:0xc002].hex(),'r2_complement':r[0x7fffa:0x7fffc].hex(),'r2_magic_complement_sum':hex(int.from_bytes(r[0xc000:0xc002],'big')+int.from_bytes(r[0x7fffa:0x7fffc],'big'))}
vals=[]
for c in range(256):
 v=((c^1^2)+3)&255;x=((v<<8)|v)>>2;vals.append((x+[0x2a,-0x5d,0x57,0][x&3])&255)
if isinstance(lut,list):res['logged_decrypt_formula_matches_lookup']=vals==lut
(root/'outputs/THR_running_log_crosscheck.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
