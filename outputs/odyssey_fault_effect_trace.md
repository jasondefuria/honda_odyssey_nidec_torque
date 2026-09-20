# Odyssey THR-A020: curve-monitor fault effects

Analysis of the unchanged original `user.bin`; no patch or flash produced. SHA256: `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`.

## Result

The previously traced curve-monitor fault reaches an assist-state predicate, subject to an explicit fault-copy gate. Two traced state-machine paths respond by selecting reason/state value 1. This establishes a control-state consequence; it does **not** establish that the physical assist torque becomes zero.

## Fault propagation and its gate

The preceding report traced monitor flags at `FFF8A5DB` through checker `4D358`, descriptor `6FC00`, and the fault engine to internal selector `EF`: bit 15 of the word at `FFF89362` (original flags base `FFF89350` + 18). This is an internal selector, not an identified standardized DTC.

At `4B658`, the firmware copies the 22-byte ROM template at `4F62C` to stack offset 0, and the original flags to stack offset 24. All 22 template bytes are zero. Subsequent processing selectively changes flags; the observed masks on word +18 clear bits 0 through 13, not bit 15.

At `4B85C`, getter `2DE7A` tests `(byte[FFF861ED] & C0) != 0`:

- If false, `4B868..4B898` copies the processed live flags into `FFF89366`.
- If true, `4B89A..4B8C4` copies the zero template into `FFF89366`.

Thus the original fault bit does not unconditionally appear in the processed flags. The operational meaning and writers of the two gate bits remain to be established. This documents existing behavior, not a proposed way to suppress monitoring.

## Assist-state predicate

`77260` obtains processed flags through `4ABF0` and original flags through `4ABE4`. It combines selected processed fields and original byte 0 bit 5, returning 1 when their combined value is nonzero.

Crucially, instructions `772D8..772DA` include **all 16 bits of processed word +18**, at `FFF89378`. Therefore the propagated curve-monitor bit makes this predicate return 1. Other faults can also produce the same result; the predicate is not specific to this monitor.

Two concrete consumers:

| Consumer | Fault branch | Consequence |
|---|---|---|
| `7698C` block | `769DC..769E2` | Calls `76D1A(1)` and bypasses the following normal branch |
| `7765C` block | `77692..77698` | Calls `77A96(1)` and branches past the following normal calculations |

These are conditional paths within a larger state machine, not evidence that both execute every cycle.

## Exact state writes

State base is `FFF83488`; offsets below are bytes.

| Field | `76D1A(1)` | `77A96(1)` |
|---|---:|---:|
| +4 | 0 | 0 |
| +5 | 1 | 1 |
| +6 | 0 | Unchanged by this helper |
| +7 | 1 | 1 |
| +8 | 0 | 0 |
| +14 | Unchanged by this helper | 0 |

`77A96` also preserves previous +4 and +14 at +15 and +16 when either changes. Numeric field meanings beyond their traced uses are not assigned here.

`773EC` packs +4, +7 shifted left 1, and +8 shifted left 2, plus a separate bit derived from `11D70`. With either state-1 result, the low three status bits become binary `010`. At `343CA`, the firmware calls this packer and writes the returned byte as byte 0 of an output buffer, followed by a separate status byte and 54 zeros. Its transport/message identity has not been established.

## Connection to the dynamic torque cap

`772EE` computes the cap at word `FFF83488+0`, already traced as a limiter input to `19D92` when its enable condition is met. In the non-mode-2 branch:

- If byte +6 is nonzero, it subtracts an input step from accumulator word +10, using lower-bound parameters at `FFF834F2` and `FFF834E8`.
- If byte +6 is zero, it adds an input step, using upper-bound parameters at `FFF834F0` and `FFF834E6`.
- When the accumulator equals `word[FFF834E6]`, it directly publishes cap 8868.
- Otherwise it scales the input word at offset 36 by the accumulator, divides by 16384 with truncation toward zero, takes the magnitude, and bounds it using `FFF834E4` and `FFF834E2`.

Mode 2 dispatches to `781FC` with a different state pointer. The active vehicle mode and all state transitions have not been proven here.

Because `76D1A(1)` clears +6, this evidence does not support the simplistic claim “the curve fault immediately forces the dynamic cap to zero.” Establishing the complete response requires the other enable paths, mode selection, and state-machine consumers. Physical torque also cannot be inferred from a single digital cap.

## Implication for modification analysis

The independent curve monitor has a demonstrated connection to assist state and a published status byte. A main-curve change cannot be evaluated solely by its numerical gain or firmware checksum. No 2.5× physical-torque result, transferable Pilot/Civic patch, or validated Odyssey modified image has been established.

The earlier distinction remains: `3A128` is the identified atan table in the angle-processing path, not the identified CAN steering-command curve. The established command path instead reaches the `7415C` curve/controller chain.

Companion files: `odyssey_fault_effect_disassembly.txt` and `odyssey_fault_effect_verification.json`. Verification checks original identity, the zero template, and instruction anchors; it does not substitute for runtime validation.
