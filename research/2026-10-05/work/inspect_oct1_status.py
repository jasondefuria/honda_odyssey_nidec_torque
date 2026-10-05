import pathlib,json,collections,numpy as np
P=pathlib.Path(__file__).resolve().parent.parent/'outputs/drive_analysis_20261001'
names={0:'normal',1:'driver_steering',2:'no_torque_alert_1',3:'low_speed_lockout',4:'no_torque_alert_2',5:'fault_1',6:'tmp_fault',7:'permanent_fault'}
result=[]
for f in sorted(P.glob('*.npz')):
 a=np.load(f)
 if 'eps_status' not in a:continue
 e=a['eps_status'];c=a['cs'];ix=np.clip(np.searchsorted(c[:,0],e[:,0],side='right')-1,0,len(c)-1);cs=c[ix];fresh=(e[:,0]>=cs[:,0])&(e[:,0]-cs[:,0]<.1);m=fresh&(cs[:,2]>=10)&(cs[:,6]>0)
 counts=collections.Counter(e[m,1].astype(int));allcounts=collections.Counter(e[:,1].astype(int))
 result.append({'route':f.stem,'all_bus0_status_frames':{names.get(int(k),str(k)):int(v) for k,v in allcounts.items()},'frames_during_moving_temporary_flag':{names.get(int(k),str(k)):int(v) for k,v in counts.items()}})
(P/'eps_status_codes.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
