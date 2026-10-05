from pathlib import Path
import json
O=Path('outputs/ptm_final_emulator');g=json.load(open(O/'grid.json'));tr=json.load(open(O/'transitions.json'));f=json.load(open(O/'faults.json'));plants=json.load(open(O/'assumed_plant.json'));of=json.load(open(O/'output_fault_comparison.json'))
errors=json.load(open(O/'errors.json'));assert not errors
native={(r['bank'],r['delta']):r['detected'] for r in of if r['image']=='stock'}
assert all(r['detected']==native[r['bank'],r['delta']] for r in of)
s='''# Final global-feedforward PTM: emulator verification

## Scope and outcome

The actual packaged global-feedforward RWD was decoded and executed, not rebuilt from helper source. SHA256 `1c45356e7dffd85a416d79ae262641756f2bdc37e99fe9f0422981f1a4e033f1`. The bank7-exclusion file was NOT used. No file or calibration was changed by these tests.

Completed5604 integrated controller updates across PTM, v4 and stock, plus125 final-file controller-helper boundary executions and250 monitor-helper boundary executions. There were no emulator exceptions in the completed suites. This is a bounded test campaign, not exhaustive verification of the firmware or all physical operating states.

SH-2A SLEIGH/p-code executes original and patched instructions with allocated synthetic RAM/stack. It has no ECU peripherals, real interrupts, watchdog timing or physical plant. Memory beyond mapped regions and unsupported instructions raise errors rather than silently passing. Decoder/model correctness is not independently certified by these tests.

## Final-file response grid

All seven banks; schedules-2176,0,2176; rates-320,320; weights(16384,0,16384) and(8192,8192,8192). Eight stateful command/feedback pairs per scenario: (0,0),(55,1),(400,2000),(1774,32767),(-1774,-32768),(-400,-2000),(-1,-1),(0,0). Each scenario begins with0x720DC initialization. Both0x6B010 controller monitor and0x6ACC4 curve monitor execute after every update.

| Image | Updates | PD flags | Curve flags | Combined-clamp overruns |
|---|---:|---:|---:|---:|
'''
for n,rs in g['results'].items():
 ts=[t for r in rs for t in r['ticks']];s+=f"| {n} | {len(ts)} | {sum(bool(t['pd_flags']) for t in ts)} | {sum(bool(t['curve_flags']) for t in ts)} | {sum(not t['within_limit'] for t in ts)} |\n"
s+='''
Full numeric response maps are in grid.json. Prescribed feedback is independent of output; these traces do not simulate an actual vehicle.

## Retained-state bank transitions

All42 ordered switches between distinct banks, for each image: three updates at bank A and three at bank B, retaining controller state and directly changing the selector. Command400, feedback1000. Total756 updates. This direct selector change is a stress test; real ECU transition scheduling and cache/initialization sequencing are not represented.

| Image | Scenarios with monitor flags | Largest first-switch output jump, internal units |
|---|---:|---:|
'''
for name in ['stock','v4','PTM']:
 rs=[r for r in tr if r['image']==name];s+=f"| {name} | {sum(any(t['pd_flags'] or t['curve_flags'] for t in r['ticks']) for r in rs)} | {max(abs(r['ticks'][3]['out']-r['ticks'][2]['out']) for r in rs)} |\n"
s+='''
A flag-free jump is not necessarily acceptable mechanical behavior. PTM's1184-unit jump is material and requires real mode-transition analysis before deployment. Complete transition traces are in transitions.json.

## Diagnostic corruption tests

Faults were injected only into the monitor's RAM observation copy after the controller executed. This tests observation consistency, not corrupt live motor commands, bus faults or common-mode corruption of both calculation and monitor inputs.

Twenty-eight PTM fault scenarios (seven banks ×four types), each eight updates:

| Injected observation fault | Detection |
|---|---|
| P+D+FF sum +1 | All7banks |
| P term +100 | All7banks |
| Mapped target +1024 | All7banks |
| Reported combined output +100 | Banks4–7; NOT banks1–3 |

Follow-up:126 scenarios /1008 updates across stock/v4/PTM and all banks, with output observation offsets-512,-100,-1,+1,+100,+512. Detection patterns were identical across the three images. Banks1–3 detected±512 but not±1/±100 under these test conditions. Banks4–7 detected all tested offsets. This is not proof of detection at every true output value; it characterizes the tested command400/feedback0 sequence and diagnostic tolerances/paths. Do not describe the monitor as detecting every numerical corruption.

## Final-file numerical boundaries

Used the helpers decoded from the RWD at0x75800/0x75900, with actual gain8.125 combinations of signed target/P/D boundary values exercised both saturation branches, scratch registers, MACL, r3 and stack restoration. All125 controller-helper cases matched the mathematical expression. All125 matching monitor cases met the equality contract; all125 one-count-corrupted sums produced a nonzero comparison residual. These helper cases stop at return destinations before full diagnostic debounce. Results:boundary_results.json.

## Assumed closed-loop models

Sixteen100-update simulations (v4/PTM ×two gains ×two lag coefficients ×two delays), each executing the firmware routines. The invented dimensionless plant is:

    y_next = y + alpha*(plant_gain*delayed_controller_output - y)

plant_gain∈{2,6}, alpha∈{0.05,0.2}, delay∈{0,3} updates. Command400 from samples10–64, otherwise0. Feedback supplied to the firmware is rounded/clipped y. Neither coefficients nor update duration are identified from hardware. There is no inertia/nonlinear tire model, motor-current regulation or mechanical steering model. These are sensitivity demonstrations, not validated EPS models.

All simulated traces were finite and monitor-flag-free over100updates. PTM had lower peak y in each corresponding model, consistent with reduced gains/clamps; that is not proof of better tracking or less oscillation.

| Assumed gain | Alpha | Delay updates | Peak | Final10-sample range | Image |
|---:|---:|---:|---:|---:|---|
'''
for r in plants:
 ts=r['trace'];s+=f"| {r['assumed_gain']} | {r['assumed_alpha']} | {r['delay_updates']} | {max(abs(t['feedback']) for t in ts):.2f} | {max(t['feedback'] for t in ts[-10:])-min(t['feedback'] for t in ts[-10:]):.2f} | {r['image']} |\n"
s+='''
The final10-sample range can reflect residual decay, not necessarily oscillation. A100-update finite run does not establish asymptotic stability. Full traces are in assumed_plant.json.

## Not established or not executable in this harness

- Complete boot, CAN reception/validity gates, engagement/disengagement state machine, real scheduling and interrupt behavior. Tests directly call controller functions and do not claim whole-ECU emulation.
- Actual ROM-region ownership/execution permission, flash acceptance, watchdog and worst-case execution-time margins, full-system stack headroom.
- Physical torque, mechanical stability, thermal/current limits, or resolution of reported40mph oscillation.
- Drive-log validation of internal EPS states: no fully identified log-to-internal-state replay was performed. Openpilot logs alone do not supply every required internal state.
- Exhaustive arithmetic/state coverage or independently validated SH-2A CPU semantics.

No checksum or emulator result removes those limits. The file remains an experimental candidate, not a verified vehicle release.

Reproduce with work/test_final_ptm.py, work/test_final_ptm_boundaries.py and work/test_ptm_output_faults.py using the existing pypcode environment. All result JSON files are in this directory. Source RWD files are unchanged.
'''
(O/'REPORT.md').write_text(s);print(O/'REPORT.md')
