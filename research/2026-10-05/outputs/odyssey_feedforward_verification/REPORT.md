# Odyssey feedforward verification

## Result

The isolated feedforward product is verified in the stated instruction tests. A synthetic controller insertion respects existing output clamps in the tested cases but is rejected by the unchanged monitor. An integrated feedforward firmware patch is NOT verified and no RWD was created or changed.

## Proposed equation and insertion

    ff = arithmetic_shift_right(signed16(mapped_target) * signed16(gain), 10)
    sum = clamp(P_clamped + D_clamped + ff, -32767, 32767)

The synthetic addition occurs immediately before 0x74AA2, after 0x74AA0 forms P+D in r2 and before the sum is stored and multiplied by the schedule factor. All subsequent scaling and combined-output clamping execute the original v4 instructions. This is an emulator callback modifying r2, not a machine-code trampoline. Register preservation, branch reach, ROM placement, instruction timing and runtime CRC are therefore not validated.

## Instruction-level arithmetic

The isolated SH-2A helper multiplies signed16 arguments, reads MACL and arithmetic-shifts right10. 655 cases matched an independent integer expression: 131 fixed/extreme/seeded-random targets for each gain0,8,16,32,45. These are test gains, not calibrated recommendations. Negative fractions round toward negative infinity: target=-1/gain8 gives-1, while target=1/gain8 gives0. A different rounding rule would be a different implementation requiring its own checks.

Maximum product for these positive gains and signed16 targets fits signed32. Saturation of the injected sum is modeled in Python; it is not implemented by the isolated helper. The ordinary controller test cases do not reach the proposed ±32767 sum bound, so they do not verify an assembled saturation routine.

## Controller/monitor experiment

225 reset scenarios /900 updates: gains0,8,16,32,45; banks1,3,7; commands-1024,-400,0,400,1024; externally supplied feedback-2000,0,2000; four updates. The schedule argument and rate RAM are zero; weights16384/0/16384. No plant or task timing is simulated.

| Feedforward gain | Updates | Nonzero monitor observations | Observed nonzero flag |
|---|---:|---:|---|
| 0 | 180 | 0 | none |
| 8 | 180 | 72 | 0x4 |
| 16 | 180 | 72 | 0x4 |
| 32 | 180 | 72 | 0x4 |
| 45 | 180 | 72 | 0x4 |

All180 zero-gain updates exactly match prior v4 output/scaled-output/monitor observations. Every tested output remains within its original combined clamp: ±2560 for banks1/3, ±1024 for bank7. This does not validate the downstream motor/current path or physical stability. Short monitor debounce histories mean a zero flag early in a scenario is not acceptance of a nonzero feedforward term.

## Why the monitor rejects it

0x6B010 snapshots controller object +0x60 (recorded sum), +0x5C (clamped P) and +0x4C (clamped D). At0x6B718–0x6B72C it checks:

    recorded_sum - P_clamped == D_clamped

A nonzero feedforward changes that identity. The main-only synthetic insertion leads to observed diagnostic flag0x4 in later updates. Unlike the P/D table mismatch, this is an algorithmic identity, not a missing gain reference copy.

A legitimate feedforward integration would need an independently calculated target-based term in the diagnostic equation, with a separately defined gain reference, rounding and saturation contract. Merely clearing the bit, widening tolerances or presenting a false recorded sum would not verify the controller. No such changes were made here. A new diagnostic should also be tested with deliberately corrupted feedforward inputs/output to demonstrate detection, plus zero-gain compatibility.

## Decision

Arithmetic helper: PASS within655 cases.
Zero-gain compatibility: PASS within180 updates.
Existing combined-output clamps: respected in900 updates.
Unchanged-monitor compatibility for nonzero feedforward: FAIL.
Assembled controller and independent-monitor integration: NOT IMPLEMENTED/NOT VERIFIED.
Physical gain selection/stability: NOT ESTABLISHED.

Artifacts: results.json, insertion_and_monitor.txt, monitor_snapshot.txt. Reproduce with work/verify_odyssey_feedforward.py using the existing pypcode environment. Source RWD SHA256: `9e1af08d018ef905d87bc6db39cea8a740afbcadadd89fe66eaf01ee96e06fc7`.
