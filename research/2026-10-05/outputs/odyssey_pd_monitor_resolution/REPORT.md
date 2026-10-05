# Odyssey P/D monitor resolution

The observed P/D diagnostic mismatch is resolved in the tested offline configurations by maintaining the independent calibration reference tables. No monitor instructions, thresholds, tolerances or status bits were changed. No RWD was built or modified.

## Verified pairing

| Meaning | Main table | Monitor reference | Count |
|---|---|---|---|
| D X axis | 0x57C4C | 0x67C72 | 9 signed16 words |
| D Y gain | 0x57C5E | 0x67C84 | 9 signed16 words |
| P X axis | 0x57C70 | 0x67C9A | 9 signed16 words |
| P Y gain | 0x57C82 | 0x67CAC | 9 signed16 words |

Add `(bank-1)*0x300` to each address. Main/reference arrays match in unmodified v4. Experiments change banks1–3; bank7 is an unchanged control.

0x6B010 performs independent gain consistency checks: D lookup call at0x6B462 uses X0x67C72/Y0x67C84; P lookup call at0x6B616 (JSR delay context shown in evidence) uses X0x67C9A/Y0x67CAC. Both call0x30A52 with nine points and the controller's reported coefficient. The helper performs a reference interpolation-consistency check; it is not the controller's normal interpolation helper. Monitor also checks arithmetic relations and clamps separately.

## Matched experiments

Previously only the main P/D tables changed. This run changes the matching independent Y references to exactly the same signed16 values. It leaves the X axes, tolerances, monitor logic and all other experiment settings unchanged.

| Experiment | Previously flagged updates | Matched-reference flagged updates | Updates |
|---|---:|---:|---:|
| stock | 0 | 0 | 240 |
| v4 | 0 | 0 | 240 |
| P_minus_25pct | 72 | 0 | 240 |
| D_plus_25pct | 36 | 0 | 240 |
| tracker_minus_25pct | 0 | 0 | 240 |
| tracker_plus_25pct | 0 | 0 | 240 |
| limits_minus_20pct | 0 | 0 | 240 |
| combined_exploratory | 72 | 0 | 240 |

All controller-output traces are exactly identical before and after adding the reference edits (P,D,feedback,scheduled sum,clamped output and scaled output). Only monitor observations changed: 180 formerly nonzero observations cleared. The original main-table-only runs provide negative controls: the unchanged diagnostic still detects an inconsistent calibration.

Additional breakpoint sweep: 420 scenarios / 1680 updates, 0 nonzero monitor observations. It covers both P-only and D-only experiments, banks1 and7, positive/negative axis knots and endpoints, feedback inputs-2000/0/2000, four updates per reset. Absolute command samples are0,55,128,166,256,319,384,512,532,640,768,776,887,896,942,998,1024,1774. The original sweep includes banks2 and3 as well.

## Limits and next work

This resolves the observed gain-reference inconsistency under the tested schedule (schedule argument0, other rate-related RAM zero, blend weights16384/0/16384). It is not exhaustive operating-range validation, fault-injection certification, or physical stability evidence. Initialization and original controller instructions execute in the offline emulator, but no interrupts, peripherals, real task timing or plant execute.

Limit/filter experiments reporting zero flags do not establish that their own reference paths are fully consistent or that every diagnostic was exercised. Feedforward integration remains unresolved and was not added to these controller runs. A future firmware candidate also needs proper independent-reference maintenance, checksum repair and separate integration verification; no inference of flash readiness follows from this result.

Reproduce: work/resolve_pd_monitor.py and work/pd_monitor_breakpoints.py. Results and exact in-memory patch manifests: results.json; comparison.json; ../odyssey_pd_monitor_breakpoints/results.json. Disassembly evidence is in evidence/.
