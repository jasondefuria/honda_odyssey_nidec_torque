# THR-A020 R2 — experimental 2.5× peak controller output

**File:** [39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd](39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd)

R2 corrects the independent-calibration mismatches found in the first revision. It passes the scoped offline SH-2A execution tests described below. **It is not validated for installation in a road-going vehicle: physical steering torque, full ECU behavior and programming acceptance remain untested.** No claim of measured 2.5× physical torque is made.

## What changed

Normal banks 1–3 receive the following coordinated calibration changes. Bank offset is `(bank−1) × 0x300`.

| Role | Main address | Independent monitor reference | New value |
|---|---|---|---|
| Command-curve ordinates | 0x57BC0 | 0x67BD6 | 0, 3968, 7936, 9950, 10863, 11443, 11803, 12160, 12160 |
| P ceiling | 0x57BD8 | 0x67BEE | 2560 |
| Controller-output ceiling | 0x57BDA | 0x67BF0 | 2560 |

The D ceiling stays 640. Gains, filters, driver-override calibration, engagement thresholds, state-machine code, diagnostic logic, mismatch debounce constants and the shared mixer ceiling remain byte-stock. Only the listed calibration words and checksum words differ from stock: **112 ROM bytes**. All executable instructions are unchanged. Identity records and unselected calibration banks are unchanged.

The first revision changed the main values only. Further execution showed that it fails both the curve and PD monitors. R2 supplies matching independent curve and clamp references; it does not disable the monitor logic. Deliberate corruptions of the resulting snapshots still produce a diagnostic fault.

## What “2.5×” establishes

Actual ROM execution reproduces steady controller output **+2090 / −2090** versus stock **+836 / −836**, at maximum positive/negative normalized command, zero feedback, no driver fade and full authority. The mixer reproduces those counts with zero base-assist contribution in the stated tests.

The first step from zero reaches the output caps, ±2560 versus stock ±1024, because of the derivative contribution. This is not a uniform torque multiplier: the changed curve alters the feedback target, lower-command scaling is constrained by interpolation, and the output ratio varies with feedback and other controller terms. It also does not establish the relation between controller counts and physical shaft torque.

## SH-2A execution checks

Execution uses Ghidra SLEIGH `SuperH:BE:32:SH-2A` via pypcode 4.0.0 and the recovered local p-code interpreter. ROM instruction bytes and actual calibration initialization execute with immutable ROM, synthetic RAM and a synthetic stack. No instruction/function hooks are used. Unsupported operations and unmapped accesses fail.

Both stock and R2 were tested in banks 1, 2, 3 and 7:

| Check | Total stock + R2 | Result |
|---|---:|---|
| Every active-range curve input −1024…+1024, plus eight signed boundary inputs per bank/image | 16,456 input cases | Exact fixed-point oracle match; zero curve-monitor mismatches |
| Directed and seeded random PD cases, including signed feedback extremes, driver input, rate and crossfade weights | 1,304 cases × 4 calls | Zero curve/PD monitor faults; output limits and mixer equality checks passed |
| Corrupted curve or PD snapshots | 16 cases | All trigger the monitor on the third evaluation and diagnostic callback state 2 |
| Combined preprocessing, fade, curve, PD and mixer with four corresponding monitor routines | 280 cases × 5 calls | Zero consistency faults; expected output bounds |

R2 alone accounts for 8,228 curve inputs, 652 PD cases, eight corruption cases and 140 combined-pipeline cases. The other half supplies the stock comparison.

The combined-pipeline tests execute `0x7276A` and `0x74C9C`, followed by monitor routines `0x6A700`, `0x6ACC4`, `0x6B010`, `0x6BE98`, and diagnostic aggregation `0x4D358`. They supply selected command values −4096, −2048, 0, +2048, +4096; driver-input values −900, −768, −767, 0, +767, +768, +900; zero feedback/base assist; full weights; and speed input 60 counts. The actual driver-override cutoff produces zero faded command and zero controller output at |driver input| ≥768 in these cases. The adjacent ±767 cases exercise the fade side of the boundary. Unchanged bank 7 matches stock in the combined tests.

A later [matched transition comparison](THR_stock_R1_R2_COMPARISON.md) qualifies that fresh-state result: when driver input crosses from 767 to 768 with existing controller history, both stock and R2 produce a one-call −57-count transient before settling to zero in the staged harness. The earlier tests started each case with fresh history. Neither suite models the full vehicle override response.

These are function/pipeline tests, not a complete boot or engagement simulation. Full weights are supplied explicitly; the suite does not prove the engagement state machine authorizes them in a real vehicle. The synthetic monitor evaluations do not establish wall-clock timing or all closed-loop dynamics.

## RWD checks and identity

- RWD size: **475,189 bytes**.
- RWD SHA-256: `dbfe61804b35c6ff8855c0c02115c72c5fdd26d6f82e5e2209cf72bbae120311`.
- Full candidate BIN SHA-256: `688f36d6fb0c3b0ae1a3c8d620c509f7279f015b5d74eb05fd98e2abf9b5847c`.
- Original BIN SHA-256: `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`.
- Download range: start 0xC000, length 0x74000.
- Firmware checksum A: **765C**; checksum C: **5BBC**; whole application word sum: zero.
- Stock-container headers, accepted THR-A020 identity and key records are preserved.
- Independent decoding recovers the exact emulator-tested candidate; deterministic rebuilding reproduces the complete RWD.
- The stock encrypted/plaintext pair independently reproduces the full encoding lookup.
- Ten negative build/container tests reject altered stock, an unreviewed candidate, failed or mismatched execution reports, incorrect patch preimages, bad lookup data, corruption, truncation, trailing bytes and incorrect declared length.

The software identity remains stock; use the filename and SHA-256 to distinguish the build. The original files and known-failed first revision were not overwritten. The first revision remains rejected; its filename lacks `R2`.

## Remaining limits

No physical torque measurements are available. The peripheral/interrupt environment, full boot, CAN reception, all safety/state-machine transitions, motor/current control, closed-loop stability, resident decryption acceptance and final programming-dependency checks have not been validated. Passing these scoped software tests does not establish road-use suitability or make the RWD a proven recovery image.

## Reproduction and evidence

- [Exact patch manifest](THR_R2_patch_manifest.json)
- [Curve, PD and corruption tests](THR_R2_emulator_validation.json)
- [Combined preprocessing/mixer tests](THR_R2_pipeline_validation.json)
- [Directed stock/R1/R2 monitor comparison](THR_R2_directed_pd_monitor.json)
- [RWD integrity and negative tests](THR_R2_RWD_validation.json)
- [R2 packaging script](build_thr_r2_rwd.py)
- [Offline build and test sources](THR_R2_reproduction_sources.zip)
