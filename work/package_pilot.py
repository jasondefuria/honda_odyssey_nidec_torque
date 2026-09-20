from pathlib import Path
import hashlib,json,pypcode
r=Path('work/pilot-a060');user=Path('/Users/jasondefuria/Downloads/39990-TG7-A060-2X (2019 Honda Pilot).rwd').read_bytes();assert user==(r/'39990-TG7-A060-2X (2019 Honda Pilot)').read_bytes()
s=(r/'39990-TG7-A060-STOCK.rwd.decoded.bin').read_bytes();m=(r/'39990-TG7-A060-2X (2019 Honda Pilot).decoded.bin').read_bytes()
checks={}
for name,b in [('stock',s),('2x',m)]:
 checks[name]={hex(e):sum(int.from_bytes(b[i:i+4],'little') for i in range(0,e,4))&0xffffffff for e in [0xa000,0x1d000,0x4ff00]};assert not any(checks[name].values())
rows=[]
for k in range(5):
 a=0x1ea54+k*0xe82;z=a+380
 assert s[a-0x10000:z-0x10000]==s[0xea54:0xebd0]
 rows.append({'bank':k+1,'changed_curve_start':hex(a),'end_exclusive':hex(z),'last_stock_word':int.from_bytes(s[z-0x10002:z-0x10000],'little'),'last_modified_word':int.from_bytes(m[z-0x10002:z-0x10000],'little')})
report={'attachment_sha256':hashlib.sha256(user).hexdigest(),'matches_repository_wip':True,'decoding':'(((byte+1)^2)-3)&255','stock_matches_raw_dump':s==(r/'39990-TG7-A060-STOCK.bin').read_bytes(),'cumulative_le32_sums':checks,'five_repeated_changed_ranges':rows,'architecture_evidence':'V850 little-endian decoding yields coherent routines; repository also profiles this identity as V850.','supersedes':'Earlier preliminary Pilot comparison used the Civic substitution decoder; that intermediate result was invalid and has been regenerated.'}
Path('outputs/pilot_reference_verification.json').write_text(json.dumps(report,indent=2)+'\n')
c=pypcode.Context('V850:LE:32:default');b=(r/'stock-rom.bin').read_bytes();lines=[]
for a,z in [(0x2d000,0x2d03e),(0x4fbf8,0x4fc38)]:
 for i in c.disassemble(b[a:z],base_address=a).instructions:lines.append(f'{i.addr.offset:08X} {i.mnem:10} {i.body}')
Path('outputs/pilot_architecture_evidence.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps(report,indent=2))
