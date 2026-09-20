from sh2a_pcode import CPU,ROM,signed
from pathlib import Path
Path(__file__).resolve().parent.joinpath("results").mkdir(exist_ok=True)
import json,hashlib
rows=[]
ids=list(dict.fromkeys(ROM[0x5eb00+70*i:0x5eb05+70*i] for i in range(14)))+[b'XXXXX',b'THRA9']
for ident in ids:
 c=CPU();p=0xfff8e000
 for i,v in enumerate(ident):c.writemem(p+i,1,v)
 match,_=c.run(0x2f8fc,(p,));idx=signed(match&255,1)
 result,_=c.run(0x2f95a,(p,))
 rec=ROM[0x5eb00+70*max(0,idx):0x5eb00+70*max(0,idx)+70]
 assert c.readmem(0xfff81f58,18)==int.from_bytes(rec[:18],'big')
 assert c.readmem(0xfff81f58,70)==c.readmem(0xfff89408,70)
 flags=[c.readmem(0xfff86e80+i,1) for i in range(5)]
 assert flags==[int(rec[5]!=0),int(rec[6]==0),int(rec[6]!=3),int(rec[11]!=0),int(rec[13]!=0)]
 rows.append({'coding_hex':ident.hex(),'coding_text':ident.decode('ascii'),'matched_record':idx,'loader_return':result,'mode':rec[6],'bank':rec[16],'feature_flags_FFF86E80_through_84':flags})
Path(str(Path(__file__).resolve().parent / 'results') + '/odyssey_variant_loader_execution.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM).hexdigest(),'scope':'Original matcher and full loader, all unique table IDs plus two unmatched IDs. Auxiliary calibration RAM is zero; this does not establish actual EEPROM coding or active bank override state.','cases':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
