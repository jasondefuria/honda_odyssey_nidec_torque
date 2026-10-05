exec(open('work/dual_ranges.py').read().split('for pair in sys.argv')[0])
import math
vals=[int.from_bytes(d[0x3a128+2*i:0x3a12a+2*i],'big') for i in range(2049)]
err=max(abs(v-math.atan(i/2048)*16384/(2*math.pi)) for i,v in enumerate(vals))
octants=[int.from_bytes(d[0x3b12a+2*i:0x3b12c+2*i],'big',signed=True) for i in range(8)]
out={'atan_base':'0x3A128','entries':len(vals),'atan_counts_per_turn':16384,'max_rounding_residual_counts':err,'octant_base':'0x3B12A','octants':octants,'post_lookup_multiplier':4,'stored_phase_modulus':65536,'delta_input_phase_modulus_after_halving':32768}
(R/'outputs/dual_ecu_reconstruction/odyssey_angle_evidence.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
