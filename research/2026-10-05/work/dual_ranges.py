exec(open('work/continue_dual_map.py').read().split('for name,path,targets')[0])
name=sys.argv[1];path='/Users/jasondefuria/Downloads/mod4/mod25xv4-39990-THR,A020.rwd' if name=='odyssey' else '/Users/jasondefuria/Downloads/39990-TRW-A020 (stock).rwd'
f=x5a(Path(path).read_bytes());d=bytes(f.firmware_blocks[0]['start'])+f.firmware_encrypted[0].translate(lut)
for pair in sys.argv[2:]:
 a,b=[int(x,16) for x in pair.split(':')];print('RANGE',hex(a),hex(b))
 for i in ctx.disassemble(d[a:b],a).instructions:
  line=f'{i.addr.offset:08x}: {i.mnem} {i.body}'
  import re
  m=re.search(r'@\(0x([0-9a-f]+),pc\)',i.body)
  if m and i.mnem=='mov.l':
   p=int(m[1],16);line+=f' ; literal={int.from_bytes(d[p:p+4],"big"):08x}'
  print(line)
