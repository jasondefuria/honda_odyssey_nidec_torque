from sh2a_pcode import ROM

def word(p):return int.from_bytes(ROM[p:p+2],'big',signed=True)
def calibration(bank):
 off=bank*0x300
 xs=[word(0x57bae+off+2*i) for i in range(9)]
 ys=[word(0x57bc0+off+2*i) for i in range(9)]
 slopes=[]
 for x0,x1,y0,y1 in zip(xs,xs[1:],ys,ys[1:]):
  dx=x1-x0;dy=y1-y0
  slopes.append((1 if dy>=0 else -1)*min(abs(dy),31*abs(dx))*((1<<26)//dx))
 return xs,ys,word(0x57bac+off),slopes

def evaluate(raw,xs,ys,limit,slopes):
 cl=max(-limit,min(limit,raw));x=abs(cl);seg=max(i for i,v in enumerate(xs) if v<=x)
 if seg==len(xs)-1:mag=ys[seg];ideal=mag
 else:
  d=x-xs[seg];s=abs(slopes[seg]);high=s>>16;low=s&65535
  step=(high*d)//1024+(low*d)//(1<<26)
  mag=ys[seg]+(step if slopes[seg]>=0 else -step)
  ideal=ys[seg]+(ys[seg+1]-ys[seg])*d//(xs[seg+1]-xs[seg])
 sign=-1 if raw<0 else 1 if raw>0 else 0
 return cl,mag,mag*sign,ideal*sign
