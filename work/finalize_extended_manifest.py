from pathlib import Path
import hashlib,json,ast,datetime
root=Path('outputs')
names=['odyssey_extended_analysis.md','odyssey_extended_disassembly.txt','odyssey_curve_execution_verification.json','odyssey_monitor_execution_verification.json','odyssey_can_execution_verification.json','odyssey_fault_state_execution.json','odyssey_reflected_crc_verification.json','odyssey_crc_range_execution.json','odyssey_fault_publication_execution.json','odyssey_monitor_fault_injection.json','odyssey_variant_loader_execution.json','odyssey_coding_record_execution.json','odyssey_crc_rom_range_execution.json','odyssey_can_counter_transition_execution.json']
files=[root/n for n in names]+sorted((root/'offline_validation').glob('*'))
entries=[]
for p in files:
 if not p.is_file():continue
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
 if p.suffix=='.json':json.loads(p.read_text())
 entries.append({'path':str(p.relative_to(root)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
raw=Path('work/user.bin').read_bytes();assert raw==(root/'user.original.bin').read_bytes()
originalhash=hashlib.sha256(raw).hexdigest();assert originalhash=='e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
manifest={'original_sha256':originalhash,'original_size':len(raw),'original_preserved':True,'modified_firmware_created':False,'timebox_start_utc':'2026-09-20T18:44:51Z','requested_timebox_end_utc':'2026-09-20T19:14:51Z','manifest_created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exhaustive_cases':{'can':2097152,'main_curve':458752,'monitor':458752,'total':3014656},'additional_directed_cases':{'fault_predicate_single_bits':176,'fault_state_scenarios':35,'fault_publication_gate_bytes':256,'monitor_snapshot_corruptions':448,'crc_primitive_inputs':4,'crc_selected_range_cases':8,'crc_full_rom_range':1,'variant_loader_ids':11,'coding_record_cases':193,'can_counter_checksum_cases':4096},'limits':'Offline original-ROM execution and static analysis; no ECU, bus, scheduler, interrupts, timing, physical torque measurement or complete programming acceptance validation.','evidence':entries}
(root/'odyssey_extended_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Recorded',len(entries),'evidence/source files; original unchanged')
