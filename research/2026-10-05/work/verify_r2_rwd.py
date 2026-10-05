from pathlib import Path
import json,hashlib,struct,importlib.util
root=Path(__file__).resolve().parents[1];out=root/'outputs'
stock=(root/'work/firmware/user.bin').read_bytes();template=(root/'work/imported/39990-THR-A020_stock_pure.rwd').read_bytes()
candidate=(root/'work/firmware/THR_A020_R2_2p5_PEAK_EXPERIMENTAL.bin').read_bytes()
path=out/'39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd';rwd=path.read_bytes()
digest=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((out/'THR_R2_patch_manifest.json').read_text());reports=[json.loads((out/n).read_text()) for n in ['THR_R2_emulator_validation.json','THR_R2_pipeline_validation.json']]
def independent_parse(b):
    assert b[:3]==b'Z\r\n';i=3;heads=[]
    for _ in range(6):
        n=b[i];i+=1;head=[]
        for j in range(n):
            count=b[i];i+=1;head.append(b[i:i+count]);i+=count
        heads.append(head)
    start=int.from_bytes(b[i:i+4],'big');size=int.from_bytes(b[i+4:i+8],'big');i+=8
    assert i+size+4==len(b) and int.from_bytes(b[-4:],'little')==(sum(b[:-4])&0xffffffff)
    return heads,start,size,i,b[i:i+size]
o=independent_parse(template);r=independent_parse(rwd)
assert o[:4]==r[:4] and r[1:3]==(0xc000,0x74000)
mapping={}
for cipher,plain in zip(o[4],stock[0xc000:]):
    assert cipher not in mapping or mapping[cipher]==plain;mapping[cipher]=plain
assert len(mapping)==len(set(mapping.values()))==256
decoded=bytes(mapping[x] for x in r[4]);assert decoded==candidate[0xc000:]
reconstructed=stock[:0xc000]+decoded
assert digest(reconstructed)==reports[0]['images']['r2']==reports[1]['images']['r2']==manifest['candidate_sha256']
expected=bytearray(stock);allow=set()
for item in manifest['patch_words']:
    a=int(item['address'],16);assert expected[a:a+2]==item['old'].to_bytes(2,'big')
    expected[a:a+2]=item['new'].to_bytes(2,'big');allow.update([a,a+1])
assert expected==reconstructed
diffs=[i for i,(x,y) in enumerate(zip(stock,reconstructed)) if x!=y]
assert set(diffs)<=allow and len(diffs)==112
assert reconstructed[0x5eb00:0x5eed4]==stock[0x5eb00:0x5eed4]
for bank in [1,2,3]:
    off=(bank-1)*0x300
    assert reconstructed[0x57bc0+off:0x57bd2+off]==reconstructed[0x67bd6+off:0x67be8+off]
    assert reconstructed[0x57bd6+off:0x57bdc+off]==reconstructed[0x67bec+off:0x67bf2+off]
    for a,n in [(0x57b4e,6),(0x57bd2,6),(0x57c4c,72),(0x57c94,2)]:assert reconstructed[a+off:a+off+n]==stock[a+off:a+off+n]
assert reconstructed[0x398cc:0x398d2]==stock[0x398cc:0x398d2]
word_sum=lambda a,z:sum(int.from_bytes(reconstructed[i:i+2],'big') for i in range(a,z,2))&65535
assert word_sum(0xc000,0x80000)==0
assert word_sum(0xc000,0x7ff80)==int.from_bytes(reconstructed[0x7ff80:0x7ff82],'big')

spec=importlib.util.spec_from_file_location('builder',out/'build_thr_r2_rwd.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
lookup=[mapping[i] for i in range(256)]
args=[stock,template,candidate,lookup,manifest,*reports]
assert b.build(*args)==rwd
negative=[]
def reject(name,fn):
    try:fn()
    except (ValueError,IndexError,struct.error):negative.append(name)
    else:raise AssertionError('accepted '+name)
def flip(blob,addr):
    q=bytearray(blob);q[addr]^=1;return bytes(q)
reject('modified stock',lambda:b.build(flip(stock,0),*args[1:]))
reject('unreviewed candidate',lambda:b.build(stock,template,flip(candidate,0x72032),*args[3:]))
bad=json.loads(json.dumps(reports[0]));bad['overall']='FAILED'
reject('failed emulator report',lambda:b.build(*args[:5],bad,reports[1]))
bad2=json.loads(json.dumps(reports[1]));bad2['images']['r2']='wrong'
reject('mismatched pipeline image',lambda:b.build(*args[:6],bad2))
bad3=json.loads(json.dumps(manifest));bad3['patch_words'][0]['old']+=1
reject('incorrect patch preimage',lambda:b.build(*args[:4],bad3,*reports))
reject('lookup corruption',lambda:b.build(*args[:3],[0]*256,*args[4:]))
reject('payload corruption',lambda:b.parse(flip(rwd,r[3]+100)))
reject('truncated RWD',lambda:b.parse(rwd[:-1]))
reject('trailing data',lambda:b.parse(rwd+b'\0'))
badlen=bytearray(rwd);badlen[r[3]-4:r[3]]=(0x74001).to_bytes(4,'big');badlen[-4:]=(sum(badlen[:-4])&0xffffffff).to_bytes(4,'little')
reject('wrong length with recomputed trailer',lambda:b.parse(bytes(badlen)))
summary=dict(status='PASS_OFFLINE_CHECKS_ONLY',rwd_name=path.name,rwd_sha256=digest(rwd),rwd_bytes=len(rwd),candidate_sha256=digest(reconstructed),stock_sha256=digest(stock),stock_rwd_sha256=digest(template),download_start='0xC000',download_length='0x74000',header_unchanged=True,roundtrip_exact=True,deterministic_rebuild=True,firmware_changed_bytes=len(diffs),rwd_changed_bytes=sum(a!=z for a,z in zip(rwd,template)),checksum_A=reconstructed[0x7ff80:0x7ff82].hex(),checksum_C=reconstructed[0x7fffe:0x80000].hex(),negative_tests_passed=negative,physical_torque='NOT_MEASURED',ecu_acceptance='NOT_TESTED',road_use_suitability='NOT_ESTABLISHED')
(out/'THR_R2_RWD_validation.json').write_text(json.dumps(summary,indent=2)+'\n')
manifest['status']='EXPERIMENTAL: passed scoped SH-2A execution and offline container checks; physical torque and ECU acceptance unvalidated'
manifest['rwd_sha256']=digest(rwd)
(out/'THR_R2_patch_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(summary,indent=2))
