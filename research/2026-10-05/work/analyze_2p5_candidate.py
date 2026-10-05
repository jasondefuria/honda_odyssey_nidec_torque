"""Offline THR calibration study. Never communicates with an ECU.

Uses table roles and interpolation limit reported in the supplied findings.
This is not a ROM emulator or a vehicle-dynamics model.
"""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
STOCK = ROOT / 'work/firmware/user.bin'
EXPECTED = 'e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
OUT = ROOT / 'outputs'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def words(b, addr, count):
    return list(struct.unpack('>' + 'H' * count, b[addr:addr + count * 2]))

def sum16(b, start, end):
    return sum(words(b, start, (end - start) // 2)) & 0xffff

def lerp(x, axis, values):
    """Ideal rational interpolation, explicitly NOT firmware Q26 lookup."""
    if x <= axis[0]:
        return Fraction(values[0])
    for i in range(1, len(axis)):
        if x <= axis[i]:
            return Fraction(values[i - 1]) + Fraction(
                (x - axis[i - 1]) * (values[i] - values[i - 1]),
                axis[i] - axis[i - 1])
    return Fraction(values[-1])

def main():
    stock = STOCK.read_bytes()
    assert len(stock) == 0x80000 and sha(stock) == EXPECTED
    axis = words(stock, 0x57bae, 9)
    curve = words(stock, 0x57bc0, 9)
    kp_axis = words(stock, 0x57c70, 9)
    kp = words(stock, 0x57c82, 9)
    assert axis == list(range(0, 1025, 128))
    assert curve == [0,2019,3230,3980,4345,4577,4721,4864,4864]
    assert words(stock, 0x57bd6, 3) == [640,1024,1024]
    assert stock[0x57b00:0x57e00] == stock[0x57e00:0x58100] == stock[0x58100:0x58400]
    target = [(5 * x + 1) // 2 for x in curve]
    limited = [target[0]]
    for i in range(1, len(target)):
        limited.append(min(target[i], limited[-1] + 31 * (axis[i] - axis[i-1])))
    assert limited == [0,3968,7936,9950,10863,11443,11803,12160,12160]
    assert all(0 <= limited[i]-limited[i-1] <= 31*(axis[i]-axis[i-1]) for i in range(1,9))
    assert max(limited) < 32768

    # A review candidate only: curve and P/u ceilings; D and loop gains unchanged.
    candidate = bytearray(stock)
    manifest = []
    allowed = set()
    def write_word(addr, value, label, bank=None):
        old = words(stock, addr, 1)[0]
        candidate[addr:addr+2] = struct.pack('>H', value)
        allowed.update([addr,addr+1])
        manifest.append(dict(address=f'0x{addr:05X}', old=old, new=value,
                             old_hex=f'{old:04X}', new_hex=f'{value:04X}',
                             role=label, bank=bank))
    for bank in range(1,4):
        shift = (bank-1)*0x300
        for i, value in enumerate(limited):
            if value != curve[i]:
                write_word(0x57bc0+shift+2*i, value, f'command_curve[{i}]', bank)
        write_word(0x57bd8+shift,2560,'P ceiling',bank)
        write_word(0x57bda+shift,2560,'controller output ceiling',bank)
    write_word(0x7ff80,sum16(candidate,0xc000,0x7ff80),'checksum A')
    write_word(0x7fffe,(-sum16(candidate,0xc000,0x7fffe))&0xffff,'checksum C')
    changed = [i for i,(a,b) in enumerate(zip(stock,candidate)) if a != b]
    assert set(changed) <= allowed
    assert sum16(candidate,0xc000,0x80000) == 0
    assert words(candidate,0x7ff80,1)[0] == sum16(candidate,0xc000,0x7ff80)
    assert candidate[0x5eb00:0x5eb00+14*0x46] == stock[0x5eb00:0x5eb00+14*0x46]
    assert candidate[0x58400:0x59300] == stock[0x58400:0x59300]
    assert candidate[:0xc000] == stock[:0xc000]
    for bank in range(3):
        q=bank*0x300
        for a,n in [(0x57b00,2),(0x57b04,2),(0x57b06,2),(0x57b4e,6),
                    (0x57bd2,6),(0x57c4c,72),(0x57c94,2)]:
            assert candidate[a+q:a+q+n] == stock[a+q:a+q+n]
    # Not published as a flash deliverable; retained for future ROM execution.
    bench = ROOT/'work/firmware/THR_A020_2p5_peak_BENCH_ONLY_UNVALIDATED.bin'
    bench.write_bytes(candidate)
    assert sha(STOCK.read_bytes()) == EXPECTED

    sweep=[]
    for x in range(1025):
        k=lerp(x,kp_axis,kp)
        s=lerp(x,axis,curve); c=lerp(x,axis,limited)
        sweep.append(dict(input=x, stock_curve=float(s), candidate_curve=float(c),
                          ideal_stock_p=float(k*s/64),ideal_candidate_p=float(k*c/64),
                          curve_ratio=float(c/s) if s else None))
    report={
        'status':'BENCH STUDY ONLY: not ROM-executed, not vehicle-tested, no flashable RWD generated',
        'assumption':'2.5x positive steady controller output at the top of the command range, zero feedback, full authority, no driver fade. NOT 2.5x physical torque or uniform output gain.',
        'stock_sha256':EXPECTED,'candidate_sha256':sha(candidate),
        'source_of_semantics':'THR_A020_FINDINGS_20260925.md; table bytes independently read',
        'axis':axis,'stock_curve':curve,'naive_2p5_curve':target,'slope_limited_candidate_curve':limited,
        'naive_first_two_slopes':[float(Fraction(target[i]-target[i-1],128)) for i in (1,2)],
        'candidate_peak_curve':12160,'stock_peak_curve':4864,
        'positive_peak_p_at_ref_zero':{'stock':4864*11//64,'candidate':12160*11//64},
        'negative_peak_arithmetic_shift_model':{'stock':(-4864*11)>>6,'candidate':(-12160*11)>>6},
        'clamps':{'stock':{'D':640,'P':1024,'u':1024},'candidate':{'D':640,'P':2560,'u':2560}},
        'changed_byte_count':len(changed),'patch_words':manifest,
        'static_checks':'source hash, size, expected tables, slope cap, signed table range, bank consistency, byte whitelist, checksum reproduction, identity and unselected banks unchanged',
        'not_verified':['exact Q26 interpolation','signed intermediate widths and overflow','controller ROM execution','transient D response','monitor/state machine interactions','motor-side response and physical torque','THR resident decryption and final programming dependency check'],
        'model_warning':'Sweep uses ideal rational interpolation; cannot substitute for the missing ROM emulator. Peaks use integer shifts with constant Kp=11.',
        'idealized_sweep':sweep,
    }
    (OUT/'THR_2p5_peak_candidate_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'THR_2p5_peak_candidate_patch.json').write_text(json.dumps({k:v for k,v in report.items() if k!='idealized_sweep'},indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','candidate_sha256','changed_byte_count','positive_peak_p_at_ref_zero','naive_first_two_slopes','slope_limited_candidate_curve']},indent=2))

if __name__ == '__main__':
    main()
