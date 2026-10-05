"""Offline packaging of the reviewed R2 experimental calibration.

Requires passing, image-matched local execution reports. Does not establish
physical torque, complete ECU behavior, or programming acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
STOCK='e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
RWD='5fb7dbc298cfc4c897644f100d664aaa2a55a6c9b46355cd8e13a5f3fd782c4c'
R2='688f36d6fb0c3b0ae1a3c8d620c509f7279f015b5d74eb05fd98e2abf9b5847c'
def need(ok,message):
    if not ok:raise ValueError(message)
def digest(x):return hashlib.sha256(x).hexdigest()
def parse(blob):
    need(blob[:3]==b'Z\r\n','signature');i=3;headers=[]
    def read(n):
        nonlocal i
        need(0<=n and i+n<=len(blob),'truncated RWD');p=blob[i:i+n];i+=n;return p
    for _ in range(6):
        headers.append([read(read(1)[0]) for _ in range(read(1)[0])])
    start,length=struct.unpack('>II',read(8));offset=i;payload=read(length)
    checksum=int.from_bytes(read(4),'little')
    need(i==len(blob),'trailing data');need(checksum==sum(blob[:-4])&0xffffffff,'RWD trailer')
    return headers,start,length,offset,payload
def build(stock,template,candidate,table,manifest,emulator,pipeline):
    need(digest(stock)==STOCK,'stock identity');need(digest(template)==RWD,'template identity');need(digest(candidate)==R2,'R2 identity')
    need(manifest['candidate_sha256']==R2,'manifest identity')
    need(emulator.get('overall')=='PASS_FOR_TESTED_SCOPES_ONLY' and emulator['images']=={'stock':STOCK,'r2':R2},'emulator reports')
    need(pipeline.get('status')=='PASS_FOR_TESTED_SCOPES_ONLY' and pipeline['images']=={'stock':STOCK,'r2':R2},'pipeline report')
    need(len(table)==256 and sorted(table)==list(range(256)),'lookup permutation')
    h,start,size,offset,payload=parse(template)
    need((start,size)==(0xc000,0x74000),'THR range')
    need(h==[[b'\0'],[],[b'0'],[b'39990-THR-A020\0\0'],[bytes.fromhex('011101121120')],[bytes.fromhex('010203')]],'header identities')
    need(payload.translate(bytes(table))==stock[start:start+size],'stock decode')
    reproduction=bytearray(stock)
    for item in manifest['patch_words']:
        a=int(item['address'],16);need(int.from_bytes(reproduction[a:a+2],'big')==item['old'],'manifest preimage')
        reproduction[a:a+2]=item['new'].to_bytes(2,'big')
    need(reproduction==candidate,'exact manifest match')
    word_sum=lambda x:sum(int.from_bytes(x[i:i+2],'big') for i in range(0,len(x),2))&65535
    need(int.from_bytes(candidate[0x7ff80:0x7ff82],'big')==word_sum(candidate[start:0x7ff80]),'checksum A')
    need(word_sum(candidate[start:])==0 and candidate[0x7fffa:0x7fffc]==b'\xb7\xc8','checksum C/magic')
    enc=[0]*256
    for cipher,plain in enumerate(table):enc[plain]=cipher
    body=template[:offset]+candidate[start:start+size].translate(bytes(enc))
    result=body+struct.pack('<I',sum(body)&0xffffffff)
    after=parse(result);need(after[:4]==(h,start,size,offset),'metadata');need(after[4].translate(bytes(table))==candidate[start:],'roundtrip')
    return result
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['stock-bin','stock-rwd','candidate-bin','lookup','manifest','emulator-report','pipeline-report','output']:
        ap.add_argument('--'+name,required=True,type=Path)
    a=ap.parse_args();paths=[a.stock_bin,a.stock_rwd,a.candidate_bin,a.lookup,a.manifest,a.emulator_report,a.pipeline_report]
    need(a.output.resolve() not in {p.resolve() for p in paths},'refusing input overwrite')
    need(not a.output.exists(),'output already exists')
    load=lambda p:json.loads(p.read_text())
    result=build(a.stock_bin.read_bytes(),a.stock_rwd.read_bytes(),a.candidate_bin.read_bytes(),load(a.lookup),load(a.manifest),load(a.emulator_report),load(a.pipeline_report))
    with a.output.open('xb') as f:f.write(result)
    print(json.dumps(dict(path=str(a.output),bytes=len(result),sha256=digest(result),classification='EXPERIMENTAL; physical torque and ECU programming acceptance unvalidated'),indent=2))
if __name__=='__main__':main()
