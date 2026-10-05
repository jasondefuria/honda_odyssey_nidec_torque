import pathlib,json,os
os.environ['MPLCONFIGDIR']='/tmp/tor-matplotlib'
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=pathlib.Path(__file__).resolve().parent.parent/'outputs/drive_analysis_20260930'
j=json.loads((P/'metrics.json').read_text()); rr=[r for r in j['routes'] if r['qualified']['seconds']>0]
fig,axs=plt.subplots(len(rr),2,figsize=(13,3.1*len(rr)),squeeze=False)
for ax,r in zip(axs,rr):
 a=np.load(P/(r['route']+'.npz'));p=a['pid'];t=(p[:,0]-p[0,0])/60;m=p[:,2]>0
 # Apply the same eligibility mask as the summary.
 def align(z):
  ix=np.clip(np.searchsorted(z[:,0],p[:,0],side='right')-1,0,len(z)-1)
  return z[ix],(p[:,0]>=z[ix,0])&(p[:,0]-z[ix,0]<.1)
 cs,fc=align(a['cs']);cc,ff=align(a['cc'])
 active=(p[:,2]>0)&(cc[:,2]>0)&fc&ff
 starts=np.where(active&~np.r_[False,active[:-1]],p[:,0],-np.inf)
 dt=np.diff(p[:,0],append=p[-1,0]+.01)
 m=active&(p[:,0]-np.maximum.accumulate(starts)>=2)&(p[:,1]>0)&(cs[:,1]>0)&(cc[:,1]>0)&(cs[:,8]>0)&(cs[:,2]>=10)&(cs[:,4]==0)&(cs[:,6]==0)&(cs[:,7]==0)&(dt>0)&(dt<=.05)
 x=np.where(m,p[:,5],np.nan);y=np.where(m,p[:,6],np.nan)
 ax[0].plot(t[::10],x[::10],lw=.6);ax[0].set_ylabel('Desired − measured angle (°)');ax[0].set_title(r['route']+' — qualified samples')
 ax[1].plot(t[::10],y[::10],lw=.6,color='#bc6326');ax[1].axhline(.95,color='gray',ls='--',lw=.6);ax[1].axhline(-.95,color='gray',ls='--',lw=.6);ax[1].set_ylim(-1.1,1.1);ax[1].set_ylabel('Normalized PID output');ax[1].set_title('Demand, not physical torque')
 for aa in ax:aa.set_xlabel('Minutes from first PID sample');aa.grid(alpha=.2)
fig.suptitle('Odyssey stock-identity steering baseline — full rlog data',fontsize=15);fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(P/'stock_baseline.png',dpi=160)
