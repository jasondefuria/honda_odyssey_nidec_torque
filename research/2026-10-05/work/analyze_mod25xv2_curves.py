from pathlib import Path
import sys,json,hashlib,os
import numpy as np
os.environ['MPLCONFIGDIR']='/tmp/tor-matplotlib'
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path.cwd();sys.path.insert(0,str(R/'work/eps_tools_transfer/openpilot/nrdr/tools/eps'))
from rwd_format.x5a import x5a
P=R/'work/eps_rwd_publish/openpilot/nrdr/tools/eps/rwd/39990-THR-A020';O=R/'outputs/mod25xv2_curve_analysis';O.mkdir(exist_ok=True)
lut=bytes(json.loads((R/'work/tla-decrypt-lookup.json').read_text()));raw=[(P/n).read_bytes() for n in ['stock_39990-THR-A020.rwd','mod25xv2-39990-THR,A020.rwd']];d=[x5a(b).firmware_encrypted[0].translate(lut) for b in raw]
def word(im,a):return int.from_bytes(im[a-0xc000:a-0xc000+2],'big')
rows=[]
for bank in range(1,8):
 for family,base in [('main',0x57bc0),('reference',0x67bd6)]:
  a=base+(bank-1)*0x300;s=[word(d[0],a+2*i) for i in range(9)];m=[word(d[1],a+2*i) for i in range(9)]
  rows.append({'bank':bank,'family':family,'address':hex(a),'stock':s,'modified':m,'ratios':[y/x if x else None for x,y in zip(s,m)],'limits':{name:[word(im,a+delta) for im in d] for name,delta in [('D',22),('P',24),('output',26)]}})
manifest=json.loads((R/'outputs/THR_R2_patch_manifest.json').read_text());assert all(word(d[0],int(p['address'],16))==p['old'] and word(d[1],int(p['address'],16))==p['new'] for p in manifest['patch_words'] if p['bank'] is not None)
prior=x5a((R/'outputs/corrected_A010_A020_MOD_headers/mod25xv1-39990-THR,A020.rwd').read_bytes());assert prior.firmware_encrypted==x5a(raw[1]).firmware_encrypted
result={'sha256':[hashlib.sha256(b).hexdigest() for b in raw],'matches_previous_mod25xv1_payload':True,'calibration_patch_words_match':True,'tables':rows};(O/'analysis.json').write_text(json.dumps(result,indent=2))
fig,axes=plt.subplots(1,2,figsize=(11,4));r=rows[0];x=np.arange(9)
axes[0].plot(x,r['stock'],'o-',label='Stock');axes[0].plot(x,r['modified'],'o-',label='mod25xv2');axes[0].set_ylabel('Calibration ordinate (internal counts)');axes[0].legend();axes[1].plot(x[1:],r['ratios'][1:],'o-');axes[1].set_ylabel('Modified / stock ordinate');axes[1].set_ylim(1,2.7)
for ax in axes:ax.set_xlabel('Table point index (not CAN command)');ax.grid(alpha=.25)
fig.suptitle('Banks 1–3: calibration changes, not measured physical torque');fig.tight_layout();fig.savefig(O/'curves.png',dpi=160)
print(json.dumps(rows[:2],indent=2));print('unchanged banks4-7',all(r['stock']==r['modified'] and all(v[0]==v[1] for v in r['limits'].values()) for r in rows if r['bank']>=4))
