exec(open('work/dual_ranges.py').read().split('for pair in sys.argv')[0])
for a in [0x57c4c,0x57c5e,0x57c70,0x57c82,0x67c72,0x67c84,0x67c9a,0x67cac]:print(hex(a),[int.from_bytes(d[a+i:a+i+2],'big',signed=True) for i in range(0,18,2)])
