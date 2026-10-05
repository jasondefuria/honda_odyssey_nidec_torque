from pathlib import Path
import json,numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
p=Path('outputs/drive_analysis_today');inv={x['route']:x for x in json.loads((p/'inventory.json').read_text())};rs=json.loads((p/'torque_metrics.json').read_text())['routes'];extra=[]
lines=['# October 4, 2026 route comparison','','32 rlogs across six routes downloaded and source-SHA256 verified. All parsed without errors. Times are America/New_York, from initData wallTimeNanos.','','All six routes use software commit 580e0fe on sp-honda-dev-202608 and torque control. Morning routes report stock identity 39990-THR-A020; afternoon routes report modified identity 39990-THR,A020. Identity is not flash readback and cannot distinguish v2/v3.','','| Route | Start EDT | Identity | Recorded min | Lateral active min | Max mph | Qualified min | MAE m/s² | P95 m/s² | Demand >=95% |','|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
for r in rs:
 i=inv[r['route']];t=datetime.fromtimestamp(i['software']['wallTimeNanos']/1e9,ZoneInfo('America/New_York')).strftime('%H:%M:%S');q=r['qualified'];v='stock' if i['eps'][0]=='39990-THR-A020' else 'modified'
 stats=f'{q["seconds"]/60:.2f} | {q["mae"]:.4f} | {q["p95"]:.4f} | {q["near_limit_pct"]:.2f}%' if q['seconds'] else '0 | — | — | —'
 lines.append(f'| {r["route"]} | {t} | {v} | {r["recorded_seconds"]/60:.2f} | {r["active_seconds"]/60:.2f} | {r["max_mph"]:.1f} | {stats} |')
 a=np.load(p/(r['route']+'.npz'));c=a['cs'];w=np.diff(c[:,0],append=c[-1,0]+.01);w=np.where((w>0)&(w<=.05),w,0);m=c[:,6]>0
 extra.append(dict(route=r['route'],temporary_seconds=float(w[m].sum()),permanent_seconds=float(w[c[:,7]>0].sum()),temporary_with_driver_pressed_seconds=float(w[m&(c[:,4]>0)].sum()),raw_eps_status_counts=r['eps_status_counts']))
lines+=['','## Shared speed bands','','| Speed | Morning 10:17 MAE / demand >=95% | Morning 11:05 | Afternoon 14:09 |','|---|---:|---:|---:|']
for band in ['22-35','35-45']:
 cells=[]
 for r in [rs[0],rs[1],rs[-1]]:
  x=r['speed_bins'][band];cells.append(f'{x["mae"]:.4f} m/s² / {x["near_limit_pct"]:.2f}% ({x["seconds"]/60:.2f} min)')
 lines.append('| '+band+' mph | '+' | '.join(cells)+' |')
lines+=['','## Fault indications','','No route contains raw EPS status 5, 6 or 7; no carState permanent-fault time was recorded. This is not a stored-DTC read. Status 3 is a general degradation/lockout indicator and does not uniquely identify low speed. Stationary route 27 has 11255 status-3 frames out of 11258, so normal operation should not be inferred for that session.','','| Route | Temporary indication total s | Coincident steeringPressed s | Permanent indication s |','|---|---:|---:|---:|']
for r in extra:lines.append(f'| {r["route"]} | {r["temporary_seconds"]:.3f} | {r["temporary_with_driver_pressed_seconds"]:.3f} | {r["permanent_seconds"]:.3f} |')
lines+=['','## Interpretation','','The afternoon moving route shows lower logged tracking error and less near-limit demand than either morning drive, also within shared speed bands. Different curvature, surface, driver behavior, and retained learned parameters prevent attribution to firmware alone. No physical torque multiplier is established.','','The estimator already reported 100% calibration before the identity changed. Bucket points were 11101 after the second morning drive and remained 11101 during all three stationary afternoon sessions, then reached 11110. This suggests retained learning rather than a fresh independent calibration. Final afternoon filtered factor 1.90573, friction 0.14115, offset -0.26509.','','## Method and limits','','Qualified tracking requires speed >=10 m/s (22.37 mph), valid CAN/messages, lateral control active for at least two seconds, no steeringPressed or temporary/permanent fault, and causal stream alignment within 100 ms. Error is logged desired minus actual lateral acceleration; durations are time-weighted with gaps over 50 ms excluded. Percentiles are sample-based. Raw EPS status uses bus-0 0x18F high nibble byte 4; CAN checksums not independently validated. No ECU memory readback, physical torque measurement or safety validation.']
(p/'REPORT.md').write_text('\n'.join(lines)+'\n');(p/'fault_comparison.json').write_text(json.dumps(extra,indent=2));print(json.dumps(extra,indent=2))
