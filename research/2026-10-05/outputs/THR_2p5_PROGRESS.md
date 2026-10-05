# THR-A020: offline 2.5× peak-output candidate

**Superseded by emulator results: this candidate failed its independent curve monitor. Do not flash its RWD.** See [THR_2p5_EMULATOR_REPORT.md](THR_2p5_EMULATOR_REPORT.md). The following records the earlier static-analysis stage.

An offline candidate has been constructed from the verified stock BIN. It is retained as a bench-analysis intermediate, not released as a flashable RWD. The stock BIN and supplied RWD remain unchanged.

## What “2.5×” means in this candidate

The target is **2.5× the positive steady controller output at the upper end of the command range**, with zero feedback, zero driver fade, no derivative contribution, and full controller/mixer authority. It is not a promise of 2.5× physical steering torque or a uniform gain over every command and feedback state.

Using the September 25 controller formula and independently read calibration bytes:

- Stock: curve 4864 × Kp 11 / 64 = **836 counts**.
- Candidate: curve 12160 × Kp 11 / 64 = **2090 counts**, exactly 2.5 × 836.
- Candidate P/output ceilings: **2560 / 2560**, so they do not clip that idealized steady peak.
- D ceiling remains **640**; Kp, Kd, feedback filters, driver override, engagement thresholds, monitors, and the total mixer ceiling remain byte-stock.

Changing the command curve changes the controller's target, not merely its output gain. At nonzero feedback, the ratio is generally not 2.5: the error changes from s−ref to s_candidate−ref. Transients can also change despite retaining the D gain and ceiling.

## Curve study

The supplied findings report a maximum interpolation slope of 31 counts per input count. This limit still needs independent ROM reproduction. Under that limit, a 128-count segment may rise at most 3968.

Simply scaling the first stock segment by 2.5 gives a rise of 5048, exceeding that limit. After reducing the first candidate point to 3968, the second point must also be reduced to keep the following segment within 3968. The other proposed points fit.

| Normalized input | Stock curve | Naive 2.5×, rounded | Candidate curve |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 128 | 2019 | 5048 | 3968 |
| 256 | 3230 | 8075 | 7936 |
| 384 | 3980 | 9950 | 9950 |
| 512 | 4345 | 10863 | 10863 |
| 640 | 4577 | 11443 | 11443 |
| 768 | 4721 | 11803 | 11803 |
| 896 | 4864 | 12160 | 12160 |
| 1024 | 4864 | 12160 | 12160 |

At input 128, the curve ratio is approximately **1.965×**; at 256 it is **2.457×**. This is therefore a peak-output proposal, not an exact 2.5× curve. Half-count targets were rounded upward. This choice is a research proposal, not an established vehicle calibration.

## What was built and checked

The candidate changes the nine-point command curve and P/output ceiling words in normal banks 1–3, then recomputes the two firmware checksum words. Total: **58 changed bytes**. The all-zero first curve point is unchanged.

Independent static checks passed:

- Original image length and SHA-256 match the imported stock reference.
- Expected stock table contents and identical normal banks match.
- Candidate table values fit signed 16-bit range and the reported slope bound.
- Candidate normal banks remain identical.
- All changed bytes fall within the intended curve, P/output ceilings, and checksum locations.
- The identity records, banks 4–8, boot region, and all other bytes are unchanged.
- The sum checksum reproduces, and the complete application window's BE-u16 sum is zero.
- A separate byte audit agrees with the generator.

Stock SHA-256: `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`.

Bench candidate SHA-256: `04b48282b8350c2f987af2efe5c59bc73d62fe6bc3ddfbf01eed06b5d27f5189`.

## What remains before a flash deliverable

The prior `sh2a_emu.py` and `verify_controller.py` files were not among the supplied files or found in the targeted Downloads search. Their reported bit-exact results cannot be treated as a test of this new candidate.

The next required work is ROM execution of the candidate, including actual Q26 lookup behavior, signed intermediate widths, feedback extremes, both command signs, derivative kicks, driver override, monitor-triggered cuts, engagement/ramp transitions, and the output mixer. A rational-interpolation sweep was generated for screening only; it is explicitly not a ROM execution result or a closed-loop stability test.

The supplied RWD's TLA encoding is now independently verified to contain stock THR application bytes. Acceptance by THR's resident decryptor and final programming dependency check remains unproven. A valid offline checksum cannot establish ECU acceptance or safe vehicle behavior.

## Deliverables

- `THR_2p5_peak_candidate_patch.json`: exact original/replacement words, hashes, scope, and limitations.
- `THR_2p5_peak_candidate_analysis.json`: the same evidence plus a 1025-input idealized sweep.

No ECU communication, flashing, or on-vehicle test was performed.
