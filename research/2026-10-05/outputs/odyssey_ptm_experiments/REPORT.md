# Odyssey PTM parameter experiments

These are sensitivity experiments, not calibrated settings or a flashable candidate. Source v4 is unchanged. Calibration edits exist only in emulator memory; checksums and independent calibration copies were deliberately not treated as validated. Original SH-2A instructions execute with synthetic RAM; there is no vehicle/actuator model.

## Coverage

Eight configurations; banks 1,2,3,7; commands -1024,-400,0,400,1024; feedback inputs -2000,0,2000; four updates per case. Total 480 reset scenarios / 1920 controller updates. The schedule argument and rate-related RAM inputs are zero, weights are 16384/0/16384. These settings exercise a restricted operating slice, not the whole scheduling surface. Histories start at zero in each scenario, so the first update includes a target step. Feedback is externally imposed, not generated from controller output.

Banks 1–3 receive experimental edits; bank 7 is an unchanged control. P/D tables are scaled and rounded to integer words using Python round (ties to even). Table resolution means percentage scaling is approximate. See results.json for exact address/value manifests.

## Existing v4 parameters

P gains `[1,4,6,8,10,11,11,11,11]`; D gains `[32,32,32,32,32,32,16,16,16]` in banks 1–3. Tracker alpha 410 (Q15), feedback clamp32765, P limit2560, D limit640, combined limit2560; downstream scale4011/1024.

## Results

Nonzero monitor flags are observations from 0x6B010 and FFF8A5DE, not decoded vehicle DTCs. Zero flags only means this monitor did not flag these cases; other monitors, CRCs and runtime prerequisites were not exercised.

| Configuration | Peak absolute combined output | Updates with nonzero monitor flags /240 |
|---|---:|---:|
| stock | 1024 | 0 |
| v4 | 2560 | 0 |
| P_minus_25pct | 2163 | 72 |
| D_plus_25pct | 2560 | 36 |
| tracker_minus_25pct | 2560 | 0 |
| tracker_plus_25pct | 2560 | 0 |
| limits_minus_20pct | 2048 | 0 |
| combined_exploratory | 2034 | 72 |

## Interpretation

Main-table-only P or D edits produce diagnostic flags in cases where stock/v4 do not. The precise failed subcheck and independent calibration pairing still need tracing. These configurations must not be described as monitor-compatible, and suppressing the monitor is not a substitute for resolving the discrepancy.

Tracker alpha sweeps are 308 and512 versus410. Smaller alpha makes feedback respond more slowly in the synthetic step; larger alpha makes it respond faster. Neither result demonstrates better vehicle stability. A slower filter can increase lag even when it reduces high-frequency noise.

The limit experiment uses P/combined2048 and D512, reducing all three main limits20%; this is an arithmetic sensitivity probe, not a recommendation to increase clamps. The combined experiment uses P75%, D125%, alpha308 and those reduced limits. It still produces monitor flags.

At command400 / feedback input2000 / bank1, v4's combined outputs over four updates are `[1894,1239,1236,1233]`. P75% gives `[1581,926,924,922]`, but the last two updates carry monitor flags. These output reductions cannot be equated with reduced oscillation in a real vehicle.

## Feedforward arithmetic prototype

A standalone SH-2A helper executes signed16 target times signed16 gain, then arithmetic right shift10. Opcode bytes `254f001ae1f6401c000b0009`; disassembly corresponds to muls.w r4,r5; sts macl,r0; mov #-10,r1; shad r1,r0; rts; nop.

35 cases (target extrema, ±12160, ±1 and zero; gains0,8,16,32,45) matched the reference expression `(target*gain)>>10`. The helper is isolated at an artificial emulator address. It is NOT inserted into Odyssey firmware, and does not implement the add, clamp, register-preserving trampoline, scheduled insertion point or independent-monitor integration. Gain45 is included as a comparison with Clarity, not as an Odyssey recommendation. A negative sub-unit product rounds down under arithmetic shift; that asymmetry is intentional in this prototype.

## Candidate decision

No combined PTM setting is justified for RWD packaging yet. Keep v4 as the comparison baseline. The next specific development task is to identify the P/D monitor discrepancies and matched reference tables, then verify an Odyssey feedforward insertion point with preserved saturation and diagnostic coverage. After that, a wider schedule/history sweep and measured response are needed to select gains rather than merely explore them.

Artifacts: results.json (complete traces and patch manifests); feedforward_helper.json (35 arithmetic tests); monitor_entry.txt (initial monitor disassembly). Reproduce with work/odyssey_ptm_experiments.py using the existing pypcode virtual environment. No RWD file was produced or altered.
