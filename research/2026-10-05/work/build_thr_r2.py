"""Create R2 calibration candidate from hash-pinned stock; no ECU access."""
from pathlib import Path
import hashlib,json,struct
root=Path(__file__).resolve().parents[1]
stock=(root/'work/firmware/user.bin').read_bytes()
assert hashlib.sha256(stock).hexdigest()=='e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
rom=bytearray(stock);changes=[]
curve=[0,3968,7936,9950,10863,11443,11803,12160,12160]
old_curve=[0,2019,3230,3980,4345,4577,4721,4864,4864]
def setword(a,expected,new,role,bank=None):
    old=int.from_bytes(stock[a:a+2],'big')
    assert old==expected,(hex(a),old,expected)
    if old!=new:
        rom[a:a+2]=new.to_bytes(2,'big')
        changes.append(dict(address=hex(a),old=old,new=new,role=role,bank=bank))
for bank in range(1,4):
    off=(bank-1)*0x300
    for base,role in [(0x57bc0,'main curve'),(0x67bd6,'independent curve reference')]:
        for i,(old,new) in enumerate(zip(old_curve,curve)):
            setword(base+off+2*i,old,new,role+f'[{i}]',bank)
    for a,role in [(0x57bd8,'P limit'),(0x57bda,'u limit'),(0x67bee,'independent P limit'),(0x67bf0,'independent u limit')]:
        setword(a+off,1024,2560,role,bank)
def word_sum(a,z):return sum(struct.unpack('>'+str((z-a)//2)+'H',rom[a:z]))&65535
setword(0x7ff80,0xd0ca,word_sum(0xc000,0x7ff80),'checksum A')
setword(0x7fffe,0xa6e0,(-word_sum(0xc000,0x7fffe))&65535,'checksum C')
assert word_sum(0xc000,0x80000)==0
allow={int(p['address'],16)+j for p in changes for j in [0,1]}
diff=[i for i,(a,b) in enumerate(zip(stock,rom)) if a!=b]
assert set(diff)<=allow
assert rom[0x5eb00:0x5eed4]==stock[0x5eb00:0x5eed4]
for start,end in [(0,0xc000),(0x58400,0x59300),(0x68400,0x69300)]:assert rom[start:end]==stock[start:end]
dest=root/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin';dest.write_bytes(rom)
manifest=dict(revision=2,status='EXPERIMENTAL: emulator checks pending; physical torque unvalidated',stock_sha256=hashlib.sha256(stock).hexdigest(),candidate_sha256=hashlib.sha256(rom).hexdigest(),changed_bytes=len(diff),patch_words=changes)
(root/'outputs/THR_R2_patch_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='patch_words'},indent=2))
