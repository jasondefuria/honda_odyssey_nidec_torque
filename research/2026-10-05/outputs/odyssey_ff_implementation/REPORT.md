# Odyssey controller and monitor feedforward implementation

## Status

Implemented two assembled SH-2A helpers and exercised them through the original Odyssey controller and diagnostic routines. The integration is an **emulator-only relocation prototype**, not a flashable firmware implementation. Helper addresses0x80000 and0x80400 are outside the original0x80000-byte image. No RWD or altered firmware binary was emitted.

This distinction matters: successful instruction execution at synthetic addresses does not prove a safe production ROM placement, execution permissions, CRC coverage, timing or stack headroom.

## Implementation

Controller stub replaces0x74A98–0x74AA7 in emulator memory, reproduces displaced instructions, independently loads mapped target from its stack snapshot, and evaluates:

    ff = (signed16(target) * signed16(controller_gain)) arithmetic_shift_right 10
    sum = clamp(P_clamped + D_clamped + ff, -32767, 32767)

It restores scratch state, stores the sum in the original observation field and resumes at0x74AA8 after the original schedule-factor multiplication. Original downstream scaling and output clamps remain in place.

Monitor stub replaces0x6B718–0x6B723 in emulator memory. It reads the target from its own previously captured snapshot and recomputes the expected sum from P, D and a separate monitor gain literal. It resumes at the original compare0x6B724 with a residual that equals D only if the recorded sum equals the independently recomputed expected sum. Original compare, debounce, flag generation and subsequent arithmetic checks remain enabled.

The helpers save/restore r0,r1,r4,r5,r6 and MACL around their arithmetic (r6 has its original displaced-instruction value). r2 is the intended result; r3 is the trampoline jump scratch register. Controller r0/r6 and monitor r14 intentionally retain their displaced-instruction effects. Neither helper calls a subroutine or changes PR. Each temporarily consumes24 bytes of stack. Whole-firmware r3 liveness and worst-case interrupt stack margin have not been proven; tested paths behaved correctly.

No diagnostic bit is cleared, no tolerance widened, and no false P or D observation is substituted. Shared corruption of both gains or of an upstream target snapshot is outside the demonstrated detection scope; the gain values are separate literals, not separate hardware safety channels.

## Integrated instruction tests

Five configurations ×45 reset scenarios ×4 updates =900 updates. Banks1,3,7; commands±1024,±400,0; feedback±2000,0. As in earlier tests, schedule argument0, rate RAM0 and blend weights16384/0/16384 restrict the operating slice.

| Controller gain | Independent monitor gain | Updates | Nonzero flag observations |
|---|---|---:|---:|
| 0 | 0 | 180 | 0 |
| 8 | 8 | 180 | 0 |
| 45 | 45 | 180 | 0 |
| 16 | 8 | 180 | 72, flag0x4 |
| 8 | 16 | 180 | 72, flag0x4 |

Zero-gain outputs exactly match the previous v4 baseline. Matched8 and matched45 outputs exactly match the prior synthetic-addition experiment. The difference is that these runs execute assembled helpers, and matched monitor equations no longer flag them. Nonzero counts arise after diagnostic debounce; zero command creates no gain-dependent discrepancy.

## Saturation and preservation tests

375 boundary combinations: gains0/8/45; targets-32768,-1,0,1,32767; P-32768,-2560,0,2560,32767; D-32768,-640,0,640,32767. These deliberately exceed normal calibrated P/D limits to exercise both saturation branches.

All375 controller helper cases matched an independent mathematical result. For each, the monitor helper was executed twice: once with the correct recorded sum and once with a one-count corruption. All375 correct sums satisfied the retained equality condition; all375 corrupt sums differed by one at that comparison. These are helper-boundary detection tests, not a claim that every one-count corruption was run through full debounce.

Saved scratch-register sentinels, MACL and stack pointer matched expected values after all boundary runs. Test harness stop hooks operate only at helper return destinations; arithmetic and preservation execute real SH-2A instructions. Full integrated900-update tests use no arithmetic hooks.

## Remaining production work

- Prove a suitable in-image executable placement and relocate stubs/helpers there. padding_inventory.json lists uniform-byte runs only; they are NOT certified unused regions. Zero runs can be tables; FF runs can be reserved/checksummed space.
- Prove scratch-register liveness across all branch paths, interrupt stack headroom and execution-time budget.
- Sweep nonzero schedules, rates, history transitions and active-bank changes; test the combined P/D/filter candidate alongside feedforward.
- Select explicit numerical candidate gains. Gains8/45 here are test points, not calibrated recommendations.
- Recompute applicable block/application/container checksums only after final placement and code are settled, and verify decode/re-encode round trip.

No physical plant, motor current, vehicle timing or torque/stability validation is claimed.

## Reproducible artifacts

- work/implement_ff_pair.py: instruction builder, relocated integration and900-update tests.
- work/test_ff_boundaries.py:375 controller and750 monitor helper executions.
- helper_bytes.json and helper_disassembly.txt: assembled helpers at synthetic addresses. Disassembly may stop when it reaches a literal pool; pool bytes are data.
- results.json and boundary_results.json: complete results.

Source v4 and existing RWD files are unchanged.
