exec(open('work/map_clarity.py').read().split('targets=')[0])
import math
p=int.from_bytes(d[0x34e5c:0x34e60],'big');q=int.from_bytes(d[0x34e58:0x34e5c],'big')
y=[int.from_bytes(d[p+2*i:p+2*i+2],'big') for i in range(2049)]
print('LUT',hex(p),'octants',hex(q),[int.from_bytes(d[q+2*i:q+2*i+2],'big',signed=True) for i in range(8)])
for i in [0,256,512,1024,1536,2048]:print(i,y[i],math.atan(i/2048)*32768/(2*math.pi))
errors=[y[i]-math.atan(i/2048)*16384/(2*math.pi) for i in range(2049)]
r={'table_address':hex(p),'octant_table':hex(q),'entries':2049,'max_abs_difference_from_atan_scaled_16384_per_turn':max(map(abs,errors)),'scaling_after_lookup':'SHLL2 multiplies angle result by four; consistent with 65536 counts per reconstructed cycle','physical_sensor':'not established','sample_period':'not established'}
(R/'outputs/clarity_ptm_comparison/angle_evidence.json').write_text(json.dumps(r,indent=2));print(r)
