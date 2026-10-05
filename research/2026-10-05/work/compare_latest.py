import pathlib,json,datetime,zoneinfo
import numpy as np
P=pathlib.Path(__file__).resolve().parent.parent/'outputs/drive_analysis_latest'
B=P.parent/'drive_analysis_20260930'
j=json.loads((P/'metrics.json').read_text());b=json.loads((B/'metrics.json').read_text());inv=json.loads((P/'inventory.json').read_text());integ=json.loads((P/'download_integrity.json').read_text())
# Supplementary crosschecks and fault intervals are computed from each raw extracted stream.
faults=[];checks=[]
for r in j['routes']:
 a=np.load(P/(r['route']+'.npz'));c=a['cs'];p=a['pid'];mask=(c[:,2]>=10)&(c[:,6]>0);ix=np.where(mask)[0]
 for group in np.split(ix,np.where(np.diff(ix)>1)[0]+1):
  if len(group):faults.append({'route':r['route'],'seconds_from_first_carState':float(c[group[0],0]-c[0,0]),'duration_approx_seconds':float(c[group[-1],0]-c[group[0],0]+.01),'median_mph':float(np.median(c[group,2])*2.236936),'driver_pressed_fraction':float(np.mean(c[group,4]))})
 m=(p[:,2]>0)&(abs(p[:,5])>.2)&(abs(p[:,6])<.8)
 checks.append({'route':r['route'],'p_over_error_p5_median_p95':np.percentile(p[m,8]/p[m,5],[5,50,95]).tolist() if m.any() else [],'max_angle_error_consistency_deg':float(np.max(abs(p[:,5]-p[:,4]+p[:,3]))),'max_speed_mph':float(np.max(c[:,2])*2.236936)})
(P/'checks_and_faults.json').write_text(json.dumps({'checks':checks,'temporary_faults':faults},indent=2))
lines=['# Latest rlog comparison with saved stock baseline','','Retrieved read-only from the comma. No firmware, tuning, or device configuration changes were made.','',f'**{len(integ)} new rlogs; {sum(x["match"] for x in integ)} source hashes match.** The saved baseline is unchanged.','', '## Firmware and software','', 'All three new routes report EPS identity `39990-THR-A020`, not modified identity `39990-THR,A020`. The recorded software commit is `b3366b5b56512805be8f0bf832b4981bfd958072` (`nrdr-clean`). Recorded kpV=0.28, kiV=0.08, kf=0.00006, torqueBP=torqueV=[0,4096], and configured actuator delay=0.10 s match the saved baseline. An identity string is not a byte-level verification of the installed firmware.','', '| New route | Recorded start (America/New_York) |','|---|---|']
for x in inv:
 d=datetime.datetime.fromtimestamp(x['software']['wallTimeNanos']/1e9,zoneinfo.ZoneInfo('America/New_York'));lines.append(f'| `{x["route"]}` | {d:%Y-%m-%d %H:%M:%S %Z} |')
lines+=['','## Aggregate comparison','','The same filters are applied to both datasets: valid messages and CAN, lateral PID and carControl active, speed ≥10 m/s, no steeringPressed indication or steering fault, at least two seconds since activation, and causally aligned carState/carControl less than 100 ms old. Observed PID intervals up to 50 ms provide time weights. Percentiles are sample-based.','', '| Metric | Previous baseline | Latest drives |','|---|---:|---:|']
for name,key,factor,unit in [('Qualified time','seconds',1/60,' min'),('Mean absolute angle error','mean_abs_angle_error_deg',1,'°'),('RMS angle error','rms_angle_error_deg',1,'°'),('95th percentile absolute error','p95_abs_angle_error_deg',1,'°'),('PID demand ≥95%','near_limit_percent',1,'%'),('Logged PID saturation flag','pid_saturated_percent',1,'%')]:
 lines.append(f'| {name} | {b["aggregate"][key]*factor:.3f}{unit} | {j["aggregate"][key]*factor:.3f}{unit} |')
lines+=['','## New routes','','| Route | Qualified min | MAE ° | P95 ° | PID demand ≥95% | Temporary fault time ≥10 m/s |','|---|---:|---:|---:|---:|---:|']
for r in j['routes']:
 q=r['qualified']
 if q['seconds']:lines.append(f'| `{r["route"]}` | {q["seconds"]/60:.2f} | {q["mean_abs_angle_error_deg"]:.3f} | {q["p95_abs_angle_error_deg"]:.3f} | {q["near_limit_percent"]:.2f}% | {r["temporary_fault_moving_seconds"]:.2f} s |')
 else:lines.append(f'| `{r["route"]}` | 0 | — | — | — | {r["temporary_fault_moving_seconds"]:.2f} s |')
lines+=['','Fault durations refer to all moving samples, not the qualified subset. Driver-intervention periods are excluded from error metrics. Controller-reported output and learned-parameter quantiles are available in metrics.json. Output is a command, not measured physical motor torque.','', '## Speed comparison','','| Speed mph | Old / new qualified min | Old / new MAE ° | Old / new P95 ° | Old / new demand ≥95% |','|---|---:|---:|---:|---:|']
for old,new in zip(b['speed_bins'],j['speed_bins']):
 def pair(key):return ' / '.join(f'{x[key]:.3f}' if x['seconds'] else '—' for x in [old,new])
 lines.append(f'| {new["mph"]} | {old["seconds"]/60:.2f} / {new["seconds"]/60:.2f} | {pair("mean_abs_angle_error_deg")} | {pair("p95_abs_angle_error_deg")} | {pair("near_limit_percent")} |')
lines+=['','The first speed bin begins at 22.37 mph (10 m/s). Even within speed bins, road curvature, bank, driver input below the intervention threshold, tires and surface are not controlled. Aggregate differences cannot establish a firmware or tuning improvement.','', '## Interpretation and limitations','', 'These are additional stock-identity recordings, not an identified R2-vs-stock experiment. Use the measured errors, command limits and fault intervals as baseline evidence. No replacement PID gains, torque mapping, physical torque multiplier or actuator delay is justified by this comparison alone. The 0.10 s delay is configuration, not a measured delay. Temporary fault indications require separate diagnosis; the logs alone do not establish their cause.','', 'Downloaded source hashes, per-route parse diagnostics, configuration inventory, extracted arrays, fault intervals and route_metrics.csv are preserved alongside this report.']
status=json.loads((P/'eps_status_codes.json').read_text())
lines+=['', '## Raw EPS status cross-check', '', 'Decoded CAN ID 399 (0x18F), bus 0, seven-byte frames; STEER_STATUS is the high nibble of byte 4 per the Odyssey imported _steering_control_a.dbc. Counts below span the entire route, including stops. Raw status decoding does not independently validate the CAN checksum.', '', '| Route | Normal | No-torque alert 1 | No-torque alert 2 | Low-speed lockout | Dedicated fault codes |','|---|---:|---:|---:|---:|---:|']
for x in status:
 c=x['all_bus0_status_frames'];n=sum(c.get(k,0) for k in ['tmp_fault','fault_1','permanent_fault'])
 lines.append(f'| `{x["route"]}` | {c.get("normal",0)} | {c.get("no_torque_alert_1",0)} | {c.get("no_torque_alert_2",0)} | {c.get("low_speed_lockout",0)} | {n} |')
lines+=['', 'In this Honda parser, NO_TORQUE_ALERT_1 raises steerFaultTemporary. This flag alone is therefore not evidence of a damaged EPS or a stored diagnostic trouble code. Status-frame and carState timing differ slightly; the full cross-check includes frames near transitions. It does not prove the cause of the no-torque alerts.']
(P/'REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'baseline':b['aggregate'],'latest':j['aggregate'],'checks':checks,'fault_intervals':len(faults)},indent=2))
