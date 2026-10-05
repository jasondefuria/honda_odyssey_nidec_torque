from pathlib import Path
import sys,json
import sh2a_pcode as e
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'));from rwd_format.x5a import x5a
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));results=[];images=[]
for path in [R/'work/eps_rwd_publish/eps_tools/stock_39990-THR-A020.rwd',R/'outputs/mod25xv2_crc_fixed/mod25xv3-39990-THR,A020.rwd']:
 rom=bytes(0xc000)+x5a(path.read_bytes()).firmware_encrypted[0].translate(lut);images.append(rom);e.load_rom(rom)
 for index in range(14):
  c=e.CPU();rec=rom[0x5eb00+index*0x46:0x5eb00+(index+1)*0x46]
  for n,v in enumerate(rec):c.writemem(0xfff81f58+n,1,v)
  ctx=0xfff8e000;buf=0xfff8e100;c.writemem(ctx+8,4,buf)
  c.run(0x3489a,(ctx,));assert not c.hooks
  data=bytes(c.readmem(buf+n,1) for n in range(16));assert data==rec[0x37:0x45]+b'\0\0';assert c.readmem(ctx+12,2)==16
  results.append({'file':path.name,'record':index,'source_flash':hex(0x5eb37+index*0x46),'response_hex':data.hex(),'identity':data.rstrip(b'\0').decode(),'response_length':16})
out=R/'outputs/f181_trace';out.mkdir(exist_ok=True)
report={'descriptor_address':'0x3E784','handler':'0x3489A','getter':'0x2F8E8','selected_record_ram':'0xFFF81F58','identity_ram':'0xFFF81F8F','selection':'0x2F8FC compares five-byte key against 14 records at 0x5EB00, stride 0x46; 0x2F95A copies selected record to RAM, defaulting to first record on failed/invalid selection. Key producer not traced here.','handler_bytes_identical':images[0][0x3489a:0x3492a]==images[1][0x3489a:0x3492a],'scope':'28 original-handler executions with synthetic selected-record RAM. No live UDS request, transport/session dispatcher execution or flash readback.','results':results}
(out/'trace.json').write_text(json.dumps(report,indent=2));print('PASS',len(results),'handler identical',report['handler_bytes_identical']);print(results[0]);print(results[-1])
