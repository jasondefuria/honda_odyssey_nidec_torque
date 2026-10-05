from pathlib import Path
import runpy,json,csv
root=Path(__file__).resolve().parents[1]
v=runpy.run_path(str(root/'work/verify_r2_rwd.py'))
s=v['stock'];r=v['reconstructed'];rows=[]
for bank in range(1,8):
 off=(bank-1)*0x300
 for family,base in [('main',0x57bc0),('reference',0x67bd6)]:
  for index in range(9):
   a=base+off+index*2;old=int.from_bytes(s[a:a+2],'big');new=int.from_bytes(r[a:a+2],'big')
   rows.append(dict(bank=bank,family=family,field=f'curve[{index}]',address=hex(a),stock=old,r2=new,ratio=new/old if old else None,exact_2p5=2*new==5*old,rounded_2p5=new==(5*old+1)//2))
  for field,delta in [('D_limit',22),('P_limit',24),('u_limit',26)]:
   a=base+off+delta;old=int.from_bytes(s[a:a+2],'big');new=int.from_bytes(r[a:a+2],'big')
   rows.append(dict(bank=bank,family=family,field=field,address=hex(a),stock=old,r2=new,ratio=new/old if old else None,exact_2p5=2*new==5*old,rounded_2p5=new==(5*old+1)//2))
for bank in range(1,4):
 for field in [f'curve[{i}]' for i in range(9)]+['D_limit','P_limit','u_limit']:
  pair=[x for x in rows if x['bank']==bank and x['field']==field];assert pair[0]['r2']==pair[1]['r2']
with (root/'outputs/THR_R2_table_audit.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('BANK 1 MAIN:',json.dumps([x for x in rows if x['bank']==1 and x['family']=='main']))
print('BANKS 4–7 ALL AUDITED VALUES UNCHANGED:',all(x['stock']==x['r2'] for x in rows if x['bank']>=4))
