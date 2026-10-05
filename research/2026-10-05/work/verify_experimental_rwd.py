"""Independent offline verification plus negative tests. No vehicle access."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs'
stock=(ROOT/'work/firmware/user.bin').read_bytes()
original=(ROOT/'work/imported/39990-THR-A020_stock_pure.rwd').read_bytes()
candidate=(ROOT/'work/firmware/THR_A020_2p5_peak_BENCH_ONLY_UNVALIDATED.bin').read_bytes()
path=out/'39990-THR-A020_2p5_PEAK_EXPERIMENTAL_UNVALIDATED.rwd'
built=path.read_bytes()
manifest=json.loads((out/'THR_2p5_peak_candidate_patch.json').read_text())
lookup=json.loads((ROOT/'work/tla-decrypt-lookup.json').read_text())

def digest(x):return hashlib.sha256(x).hexdigest()

# Independent parser, deliberately not the builder's parser.
def unpack(blob):
    if blob[:3]!=b'Z\r\n':raise ValueError('signature')
    cursor=3;headers=[]
    for h in range(6):
        n=blob[cursor];cursor+=1;items=[]
        for i in range(n):
            length=blob[cursor];cursor+=1
            items.append(blob[cursor:cursor+length]);cursor+=length
        headers.append(items)
    start=int.from_bytes(blob[cursor:cursor+4],'big')
    size=int.from_bytes(blob[cursor+4:cursor+8],'big');cursor+=8
    assert cursor+size+4==len(blob)
    assert int.from_bytes(blob[-4:],'little')==(sum(blob[:-4])&0xffffffff)
    return headers,start,size,cursor,blob[cursor:cursor+size]

o=unpack(original);b=unpack(built)
assert o[:4]==b[:4]
assert b[1:3]==(0xc000,0x74000)
# Recover a mapping independently from the known stock pair; check all 256
# symbols and every occurrence, then decode the new file with that mapping.
empirical={}
for enc,plain in zip(o[4],stock[0xc000:]):
    assert enc not in empirical or empirical[enc]==plain
    empirical[enc]=plain
assert len(empirical)==len(set(empirical.values()))==256
assert [empirical[x] for x in range(256)]==lookup
decoded=bytes(empirical[x] for x in b[4])
assert decoded==candidate[0xc000:]
reconstructed=stock[:0xc000]+decoded
assert digest(reconstructed)=='04b48282b8350c2f987af2efe5c59bc73d62fe6bc3ddfbf01eed06b5d27f5189'
expected=bytearray(stock)
for item in manifest['patch_words']:
    addr=int(item['address'],16)
    assert int.from_bytes(expected[addr:addr+2],'big')==item['old']
    expected[addr:addr+2]=item['new'].to_bytes(2,'big')
assert expected==reconstructed
assert len(reconstructed)==0x80000
assert reconstructed[0x5eb00:0x5eed4]==stock[0x5eb00:0x5eed4]
assert reconstructed[0x58400:0x59300]==stock[0x58400:0x59300]
word_sum=lambda a,z:sum(int.from_bytes(reconstructed[i:i+2],'big') for i in range(a,z,2))&0xffff
assert word_sum(0xc000,0x7ff80)==int.from_bytes(reconstructed[0x7ff80:0x7ff82],'big')
assert word_sum(0xc000,0x80000)==0
assert reconstructed[0x7fffa:0x7fffc]==b'\xb7\xc8'
diffs=[i for i,(x,y) in enumerate(zip(stock,reconstructed)) if x!=y]
assert len(diffs)==58
file_diffs=[i for i,(x,y) in enumerate(zip(original,built)) if x!=y]
assert set(file_diffs)<={b[3]+i-0xc000 for i in diffs}|set(range(len(built)-4,len(built)))

# Exercise builder failure paths using in-memory corruptions only.
spec=importlib.util.spec_from_file_location('builder',out/'build_thr_experimental_rwd.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
tests=[]
def reject(name, fn):
    try:fn()
    except (ValueError,IndexError,struct.error):tests.append({'name':name,'result':'PASS'})
    else:raise AssertionError(name+' accepted invalid input')
def flipped(blob,index):
    x=bytearray(blob);x[index]^=1;return bytes(x)
args=[stock,original,candidate,lookup,manifest]
reject('wrong stock hash',lambda:builder.build(flipped(stock,0),*args[1:]))
reject('wrong template hash',lambda:builder.build(stock,flipped(original,20),*args[2:]))
reject('unreviewed candidate',lambda:builder.build(stock,original,flipped(candidate,0x58000),lookup,manifest))
reject('nonbijective lookup',lambda:builder.build(*args[:3],[0]*256,manifest))
bad=json.loads(json.dumps(manifest));bad['patch_words'][0]['old']+=1
reject('incorrect patch preimage',lambda:builder.build(*args[:4],bad))
bad2=json.loads(json.dumps(manifest));bad2['patch_words'].pop()
reject('incomplete manifest',lambda:builder.build(*args[:4],bad2))
bad3=json.loads(json.dumps(manifest));bad3['patch_words'].append(bad3['patch_words'][0])
reject('overlapping patch words',lambda:builder.build(*args[:4],bad3))
reject('bad container signature',lambda:builder.parse_container(flipped(built,0)))
reject('corrupted encrypted payload',lambda:builder.parse_container(flipped(built,b[3]+100)))
reject('truncated container',lambda:builder.parse_container(built[:-1]))
reject('trailing data',lambda:builder.parse_container(built+b'\x00'))
bad_length=bytearray(built);bad_length[b[3]-4:b[3]]=(0x74001).to_bytes(4,'big')
bad_length[-4:]=(sum(bad_length[:-4])&0xffffffff).to_bytes(4,'little')
reject('wrong declared length despite valid trailer',lambda:builder.parse_container(bytes(bad_length)))
reject('bad ROM A word',lambda:builder.verify_rom_checksums(flipped(candidate,0x7ff80)))
reject('bad ROM final sum',lambda:builder.verify_rom_checksums(flipped(candidate,0x7fffe)))
reject('bad family magic',lambda:builder.verify_rom_checksums(flipped(candidate,0x7fffa)))
assert builder.build(*args)==built

# Formula-only counterexamples: identical positive peak command, D=0, K=256.
# These are arithmetic checks from the supplied notes, not emulator results.
clamp=lambda v,lim:max(-lim,min(lim,v))
examples=[]
for ref in [0,2000,4864,6000,-1000,-8000]:
    u0=clamp((11*(4864-ref))>>6,1024)
    u1=clamp((11*(12160-ref))>>6,2560)
    examples.append({'ref_counts':ref,'stock_u':u0,'candidate_u':u1,
                     'ratio':u1/u0 if u0 else None})
report={
    'rwd_name':path.name,'rwd_size_bytes':len(built),'rwd_sha256':digest(built),
    'stock_bin_sha256':digest(stock),'stock_rwd_sha256':digest(original),
    'reconstructed_candidate_sha256':digest(reconstructed),
    'download_start':'0xC000','download_length':'0x74000','payload_offset':b[3],
    'headers_unchanged':True,'decoded_payload_matches_candidate':True,
    'lookup_independently_recovered_from_stock':True,
    'rom_checksum_A':reconstructed[0x7ff80:0x7ff82].hex(),
    'rom_checksum_C':reconstructed[0x7fffe:0x80000].hex(),
    'application_word_sum':word_sum(0xc000,0x80000),
    'container_byte_sum_trailer':f'{int.from_bytes(built[-4:],"little"):08x}',
    'identity_records_unchanged':True,'banks_4_to_8_unchanged':True,
    'firmware_changed_bytes':len(diffs),'container_changed_bytes':len(file_diffs),
    'deterministic_rebuild':True,'negative_tests':tests,
    'physical_torque_validation':{'status':'NOT_PERFORMED','reason':'User confirmed no physical measurements available','ratio_established':False},
    'rom_emulation':'NOT_PERFORMED','ecu_programming_acceptance':'NOT_TESTED',
    'closed_loop_stability':'NOT_TESTED','road_use_suitability':'NOT_ESTABLISHED',
    'formula_only_feedback_examples':examples,
    'interpretation':'2.5 refers only to the modeled zero-feedback steady peak controller output. It is not a verified physical torque ratio or uniform controller multiplier.',
}
(out/'THR_2p5_RWD_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['rwd_sha256','firmware_changed_bytes','container_changed_bytes','physical_torque_validation','formula_only_feedback_examples']},indent=2))
print('Independent offline audit and',len(tests),'negative tests passed.')
