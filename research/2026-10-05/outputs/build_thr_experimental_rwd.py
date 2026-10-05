"""Build ONLY the reviewed THR bench candidate as an experimental RWD.

Offline container checks do not validate ECU acceptance, controller dynamics,
or physical steering torque. This program has no ECU/vehicle interface.
Python 3, standard library only.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

STOCK_SHA = 'e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2'
TEMPLATE_SHA = '5fb7dbc298cfc4c897644f100d664aaa2a55a6c9b46355cd8e13a5f3fd782c4c'
CANDIDATE_SHA = '04b48282b8350c2f987af2efe5c59bc73d62fe6bc3ddfbf01eed06b5d27f5189'
START, LENGTH = 0xC000, 0x74000

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def parse_container(blob):
    require(blob[:3] == b'Z\r\n', 'Wrong RWD signature')
    pos, headers = 3, []
    def take(n):
        nonlocal pos
        require(n >= 0 and pos+n <= len(blob), 'Truncated container')
        part = blob[pos:pos+n]
        pos += n
        return part
    for _ in range(6):
        count = take(1)[0]
        headers.append([take(take(1)[0]) for _ in range(count)])
    start, length = struct.unpack('>II', take(8))
    payload_offset = pos
    payload = take(length)
    trailer = struct.unpack('<I', take(4))[0]
    require(pos == len(blob), 'Unexpected trailing data')
    require(trailer == sum(blob[:-4]) & 0xffffffff, 'Invalid container byte-sum trailer')
    return headers, start, length, payload_offset, payload

def checksum16(blob):
    require(len(blob) % 2 == 0, 'Odd-sized word-sum input')
    return sum(v[0] for v in struct.iter_unpack('>H', blob)) & 0xffff

def verify_rom_checksums(rom):
    require(len(rom) == 0x80000, 'Wrong full image size')
    a = int.from_bytes(rom[0x7ff80:0x7ff82], 'big')
    require(a == checksum16(rom[START:0x7ff80]), 'Invalid ROM checksum A')
    require(rom[0x7fffa:0x7fffc] == bytes.fromhex('b7c8'), 'Family magic changed')
    require(checksum16(rom[START:]) == 0, 'Invalid whole-application negative sum')

def build(stock, template, candidate, lookup, manifest):
    require(sha(stock) == STOCK_SHA, 'Stock image hash mismatch')
    require(sha(template) == TEMPLATE_SHA, 'Stock RWD hash mismatch')
    require(sha(candidate) == CANDIDATE_SHA, 'Candidate hash mismatch: not the reviewed bench candidate')
    require(len(lookup) == 256 and all(type(x) is int for x in lookup)
            and sorted(lookup) == list(range(256)), 'Lookup must be a 256-byte permutation')
    headers, start, length, offset, encrypted = parse_container(template)
    require((start,length) == (START,LENGTH), 'Wrong THR download range')
    expected_headers = [[b'\x00'],[],[b'\x30'],[b'39990-THR-A020\x00\x00'],
                        [bytes.fromhex('011101121120')],[bytes.fromhex('010203')]]
    require(headers == expected_headers, 'Unexpected identity/security/container headers')
    require(set(encrypted) == set(range(256)), 'Stock sample does not exercise every lookup entry')
    decode = bytes(lookup)
    require(encrypted.translate(decode) == stock[START:START+LENGTH],
            'Stock RWD does not decode exactly to stock application')
    verify_rom_checksums(stock)
    verify_rom_checksums(candidate)
    recreated = bytearray(stock)
    patched_addresses = set()
    for item in manifest['patch_words']:
        addr = int(item['address'],16)
        require(0 <= addr <= len(stock)-2 and addr % 2 == 0, 'Invalid patch address')
        require(not {addr,addr+1} & patched_addresses, 'Overlapping patch words')
        patched_addresses.update([addr,addr+1])
        require(int.from_bytes(stock[addr:addr+2],'big') == item['old'], 'Patch preimage mismatch')
        recreated[addr:addr+2] = struct.pack('>H',item['new'])
    require(bytes(recreated) == candidate, 'Manifest does not reproduce candidate exactly')
    require(candidate[:START] == stock[:START], 'Boot region changed')
    require(candidate[0x5eb00:0x5eed4] == stock[0x5eb00:0x5eed4], 'Identity records changed')
    inverse = [0]*256
    for encrypted_byte, plain_byte in enumerate(lookup):
        inverse[plain_byte] = encrypted_byte
    enc = candidate[START:START+LENGTH].translate(bytes(inverse))
    body = template[:offset] + enc
    result = body + struct.pack('<I',sum(body) & 0xffffffff)
    after = parse_container(result)
    require(after[:4] == (headers,start,length,offset), 'Container metadata changed')
    require(after[4].translate(decode) == candidate[START:START+LENGTH], 'Candidate round-trip failed')
    require(len(result) == len(template), 'Container size changed')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reproduce-failed-for-analysis',action='store_true',
                        help='Explicitly reproduce the known-failed RWD for offline analysis only')
    for name in ['stock-bin','stock-rwd','candidate-bin','lookup','manifest','output']:
        parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    require(args.reproduce_failed_for_analysis,
            'This candidate FAILED SH-2A curve-monitor execution. Do not flash. '
            'Use --reproduce-failed-for-analysis only to reproduce the rejected research artifact.')
    inputs=[args.stock_bin,args.stock_rwd,args.candidate_bin,args.lookup,args.manifest]
    require(args.output.resolve() not in {p.resolve() for p in inputs}, 'Output would overwrite an input')
    require(not args.output.exists(), 'Output already exists; choose a new output path')
    result=build(args.stock_bin.read_bytes(), args.stock_rwd.read_bytes(),args.candidate_bin.read_bytes(),
                 json.loads(args.lookup.read_text()),json.loads(args.manifest.read_text()))
    with args.output.open('xb') as f:
        f.write(result)
    print(json.dumps({'path':str(args.output),'size_bytes':len(result),'sha256':sha(result),
        'physical_torque_validation':'NOT_PERFORMED','ecu_acceptance':'NOT_TESTED',
        'classification':'EXPERIMENTAL BENCH CANDIDATE'},indent=2))

if __name__ == '__main__':
    main()
