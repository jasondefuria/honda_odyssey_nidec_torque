from pathlib import Path
import hashlib,json,runpy
root=Path(__file__).resolve().parents[1];out=root/'outputs'
runpy.run_path(str(root/'work/verify_r2_rwd.py'))
s=(root/'work/firmware/user.bin').read_bytes();r=(root/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes();d=(out/'ccp_capture/THR_CCP_MAPPED_VIEW_00000_7FFFF.bin').read_bytes()
# Reproduce exact SHORT_UP request boundaries in capture_thr.py. Mapping is
# applied to the request start; returned bytes then advance from that address.
a=0;bad=[];checked=0;skipped=0;alias_crossings=[]
while a<len(d):
 n=min(5,len(d)-a)
 for boundary in (0x10000,0x40000,0x5fc00,0x5fdb4):
  if a<boundary<a+n:n=boundary-a
 if 0x5fc00<=a<0x5fdb4:n=min(n,4-(a&3))
 if a<0x2000 or 0x5fc00<=a<0x5fdb4:skipped+=n
 else:
  mapped=0x50000|(a&0xffff) if 0x10000<=a<0x40000 else a
  expected=s[mapped:mapped+n]
  for j in range(n):
   if d[a+j]!=expected[j]:bad.append(hex(a+j))
  checked+=n
  if 0x10000<=a<0x40000 and (a&0xffff)+n>65536:alias_crossings.append({'request':hex(a),'length':n,'resolved_start':hex(mapped),'captured':d[a:a+n].hex(),'expected':expected.hex()})
 a+=n
assert not bad,bad[:20]
ranges=[(0xc000,0x10000),(0x40000,0x5fc00),(0x5fdb4,0x80000)]
direct=[i for a,b in ranges for i in range(a,b)]
assert all(d[i]==s[i] for i in direct)
diffs=[i for i in direct if d[i]!=r[i]]
patches=[i for i in range(len(s)) if s[i]!=r[i]]
assert diffs==patches and len(diffs)==112
summary={'status':'PASS_SCOPED_CAPTURE_COMPARISON_NOT_FLASH_ACCEPTANCE','mapped_capture_sha256':hashlib.sha256(d).hexdigest(),'rwd_sha256':hashlib.sha256((out/'39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd').read_bytes()).hexdigest(),'request_aware_stock_comparison_bytes':checked,'unexpected_mismatches':bad,'excluded_boot_and_RAM_view_bytes':skipped,'directly_observed_application_bytes':len(direct),'application_bytes_not_directly_observed':0x74000-len(direct),'direct_ranges':[[hex(a),hex(b)] for a,b in ranges],'r2_differences_from_captured_stock':len(diffs),'all_r2_patch_bytes_observed_in_stock_state':True,'cross_alias_requests':alias_crossings,'unobserved_application_ranges':[['0x10000','0x40000'],['0x5fc00','0x5fdb4']],'boot_region_in_RWD':False,'boot_decrypt_check_routines_executed':False,'physical_torque_validated':False,'flash_acceptance_validated':False}
(out/'THR_R2_live_dump_verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
