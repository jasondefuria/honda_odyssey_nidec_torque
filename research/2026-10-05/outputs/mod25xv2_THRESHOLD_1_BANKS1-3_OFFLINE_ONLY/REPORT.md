# Threshold 1: offline experiment

Banks 1–3 were set to one internal speed count in host memory only. No RWD or ROM file was modified or generated.

## Results

- 1,008 isolated entry-condition assertions passed across banks 1–7, nine speed inputs, and both values of request, inhibit and standstill permit.
- At zero speed, banks 1–3 stayed idle without standstill permission. With permission, they entered the special standstill path. Threshold 1 preserves that entry distinction in these tests.
- At one speed count, banks 1–3 entered the normal ramp path.
- 44 dispatcher/ramp scenarios completed: 32 engagement/release scenarios plus 8 injected fault/configuration scenarios and 4 synthetic bank switches.
- Banks 1–3 reached ACTIVE at speed 1 in the experimental variant; the baseline remained idle. Removing the request returned all engagement scenarios to IDLE with zero authority.
- Bank 7 remained idle below 70 counts in the sampled cases, and engaged at 70.
- On bank 1, injected system and severity-3 monitor flags produced ABORT then LOCKOUT with zero authority in both variants (baseline at 10 counts; experiment at 1).
- Disabling configuration zeroed authority while state remained ACTIVE.
- Injecting inhibit during ACTIVE did not reduce authority in the dispatcher/ramp-only scope, in either variant. Downstream output suppression was not evaluated by this run.
- A synthetic bank-1-to-bank-7 switch below bank 7's threshold started ramp-out; switching to bank 2 retained ACTIVE.

## Limits

This uses the historical R2 experimental base ROM (hash in extended.json), not an exact full image of the current identity-edited mod25xv2. Inputs and RAM are synthetic. Tests cover selected functions, not full ECU execution, CAN parsing, real fault generation, downstream torque output, hardware, or physical steering. Extended fault cases cover bank 1 only. Speed is reported in internal counts, not independently verified physical units. These results are not a firmware safety validation.

Raw evidence: results.json (entry assertions), extended.json (state sequences). Scripts: work/emulation/threshold_one_offline.py and threshold_one_extended.py in the workspace.
