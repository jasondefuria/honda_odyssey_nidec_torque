"""Small independent execution checks for the reused research interpreter."""
import sys,json
from pathlib import Path
sys.path.insert(0,'/Users/jasondefuria/Documents/Codex/2026-09-20/continue-the-odyssey-thr-a020-eps/work/venv/lib/python3.14/site-packages')
import sh2a_pcode as e
checks=[]
def test(name,code,args,expected):
    blob=bytearray(256);blob[0x40:0x40+len(bytes.fromhex(code))]=bytes.fromhex(code);e.load_rom(blob)
    c=e.CPU();actual,n=c.run(0x40,args)
    assert actual==(expected&0xffffffff),(name,hex(actual),expected)
    checks.append(dict(name=name,result='PASS',return_value=e.signed(actual,4),translation_steps=n))
test('signed arithmetic','e407 e5fd 345c 6043 000b 0009',(),4)
test('rts delay slot executes','e001 000b 7002',(),3)
test('SH-2A signed division truncates toward zero','6643 6053 4694 6063 000b 0009',(-7,3),-2)
test('SH-2A MULR low word','6643 6053 4680 6063 000b 0009',(-7,3),-21)
test('MOVI20 sign extension','00f0 fef4 000b 0009',(),-268)
test('SHAD negative count arithmetic right','6643 e5fe 465c 6063 000b 0009',(-7,),-2)
test('BRA delay slot and target','e001 a001 7002 707f 7004 000b 0009',(),7)
c=e.CPU()
for name,fn in [('ROM writes fail',lambda:c.writemem(0x40,2,0)),('unmapped reads fail',lambda:c.readmem(0xff600000,2))]:
    try:fn()
    except ValueError:checks.append(dict(name=name,result='PASS'))
    else:raise AssertionError(name)
Path(__file__).resolve().parents[2].joinpath('outputs/THR_2p5_emulator_engine_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
