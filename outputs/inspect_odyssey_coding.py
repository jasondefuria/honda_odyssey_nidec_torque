#!/usr/bin/env python3
"""Read-only decoder of an Odyssey coding record already acquired by the user.
No vehicle connection, acquisition, coding write, or firmware patch operation.
"""
import argparse,hashlib,json
from pathlib import Path
EXPECTED='e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
SOURCE=0x80106800

def inspect(record,rom):
 if len(record)!=24:raise ValueError('Exactly 24 coding bytes are required')
 if len(rom)!=0x80000 or hashlib.sha256(rom).hexdigest()!=EXPECTED:raise ValueError('ROM does not match the analyzed original')
 markers=record[:2]==b'\x55\xaa' and record[17:19]==b'\xaa\x55'
 duplicate=record[2:7]==record[7:12]
 complement=record[2:7]==bytes(v^255 for v in record[12:17])
 ident=record[2:7];match=next((i for i in range(14) if rom[0x5eb00+70*i:0x5eb05+70*i]==ident),None)
 selected=match if markers and duplicate and complement and match is not None else 0
 data=rom[0x5eb00+70*selected:0x5eb00+70*(selected+1)]
 valid_bank=1<=data[16]<7
 if not valid_bank:selected=0;data=rom[0x5eb00:0x5eb46]
 return {'rom_sha256':EXPECTED,'record_hex':record.hex(),'source_address':hex(SOURCE),'marker_check':markers,'duplicate_check':duplicate,'complement_check':complement,'supplied_coding_hex':ident.hex(),'supplied_coding_ascii':ident.decode('ascii',errors='replace'),'matched_table_record':match,'selected_table_record':selected,'loaded_coding_hex':data[:5].hex(),'mode':data[6],'table_bank':data[16],'can_assist_enable_from_coding':int(data[11]!=0),'default_selected':selected==0,'limits':'Decodes the supplied record, not live ECU state. Runtime bank override and later state changes are not captured. It does not validate a torque modification or flashing acceptance.'}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('dump',type=Path,help='Existing 24-byte coding record or a larger memory dump')
 p.add_argument('--base',type=lambda s:int(s,0),help='Memory address corresponding to byte zero; required for larger dumps')
 p.add_argument('--rom',type=Path,default=Path(__file__).resolve().parent/'user.original.bin')
 a=p.parse_args();raw=a.dump.read_bytes()
 if a.base is None:
  if len(raw)!=24:p.error('--base is required for a dump larger or smaller than exactly 24 bytes')
  record=raw
 else:
  offset=SOURCE-a.base
  if offset<0 or offset+24>len(raw):p.error('The supplied address range does not contain 0x80106800..0x80106817')
  record=raw[offset:offset+24]
 print(json.dumps(inspect(record,a.rom.read_bytes()),indent=2))
if __name__=='__main__':main()
