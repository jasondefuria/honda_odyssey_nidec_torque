# SH-2A execution result: candidate FAILED

**Do not flash the previously delivered RWD.** Its main command curve disagrees with the independently recomputed reference curve. The original candidate and RWD are retained unchanged to make this failure reproducible; no corrected RWD is being represented as passing.

The earlier candidate construction missed this monitor-calibration dependency. Passing the checksums and producing the intended isolated peak output were insufficient. The builder now refuses its ordinary CLI operation; an explicit analysis-only option is required to reproduce this rejected artifact.

## Image identity and execution method

| Item | Identity |
|---|---|
| Stock BIN SHA-256 | `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2` |
| Delivered RWD SHA-256 | `4a8965d4c5991afa14e250b068d38a268e805699398c51674dfa016200d431eb` |
| RWD-reconstructed candidate SHA-256 | `04b48282b8350c2f987af2efe5c59bc73d62fe6bc3ddfbf01eed06b5d27f5189` |
| ISA definition | Ghidra SLEIGH `SuperH:BE:32:SH-2A` via pypcode 4.0.0 |
| Execution engine | Local p-code interpreter recovered from the September 20 analysis and adapted to select an immutable ROM per image |

The candidate for the sweep was decrypted from the actual delivered RWD, combined with the unchanged stock prefix below 0xC000, and hash-checked. A Python mathematical model was **not** substituted for the firmware routines. The interpreter translated and executed the routines' actual instruction bytes, including their interpolation and arithmetic helpers.

The harness rejects unsupported operations, ROM writes, and accesses outside the ROM, modeled RAM, or synthetic stack. No hooks or helper substitutions were used in these new execution cases. Nine focused engine checks passed: signed arithmetic, return/branch delay slots, SH-2A signed division, MULR, MOVI20 sign extension, arithmetic shifting, ROM-write rejection, and unmapped-read rejection. These checks do not certify the interpreter as a hardware-accurate emulator.

## Curve and monitor sweep

Routines executed:

- `0x306CE`: actual fixed-point slope initialization, independently for main and monitor tables.
- `0x7415C`: actual main command-curve calculation and monitor snapshot publication.
- `0x6ACC4`: actual independent curve-consistency monitor.
- `0x4D358`: actual aggregate monitor evaluation callback.
- `0x4BCDA`: actual fault response callback.

Each input starts with fresh synthetic RAM and actual ROM-initialized slopes. Bank 1 is selected. The main curve executes once, its genuine snapshot is supplied to three successive monitor evaluations, and the two diagnostic callbacks execute. This deliberately isolates consistency checking; it is not a full ECU scheduler or a CAN-to-motor boot simulation.

Inputs: every integer from **−1024 through +1024** (2,049 cases), plus −32768, −32767, −4096, −1025, +1025, +4096, +32766 and +32767 (eight boundary cases).

| Result | Stock | Candidate |
|---|---:|---:|
| Inputs executed | 2,057 | 2,057 |
| Main-curve discrepancies against independent fixed-point oracle | 0 | 0 |
| Curve-monitor fault cases | 0 | **2,056** |
| Evaluation callback state 2 | 0 | **2,056** |
| Response callback byte 0x80 | 0 | **2,056** |
| Translation blocks executed | 2,204,149 | 2,216,485 |

Every tested nonzero candidate input sets the fault. Zero passes. Translation blocks can include delay-slot instructions; these counts are not CPU cycles or precise instruction counts.

Additional directed tests ran seven inputs in each of banks 1, 2, 3 and 7 for both images, for 56 image/bank/input cases. They reproduce the mismatch in modified banks 1–3 and show no mismatch in unchanged bank 7 for those tested inputs.

### Concrete failure

At normalized input +1024:

- Stock main curve: **4864**.
- Candidate main curve: **12160**.
- Independent reference still uses the stock curve, including **4864** at this point.
- Monitor counter `0xFFF8A624` progresses **86 → 172 → 255**.
- On the third evaluation, byte `0xFFF8A5DB` becomes **0x02**.
- Aggregate callback writes state **2**; response callback writes **0x80**.

The main curve uses ordinates at `0x57BC0 + bank_offset`. The reference uses `0x67BD6 + bank_offset`. The prior patch changed the former only. This is a mismatch between two calibrations, not a container-integrity failure.

Three evaluations are not a measured wall-clock duration. These tests establish the monitor fault and callback response; they do not execute the complete diagnostic publication/scheduler chain or establish the vehicle's precise assist response.

## Isolated PD and mixer execution

The actual calibration initializer `0x720DC`, curve `0x7415C`, PD `0x7435C`, and mixer `0x74C9C` were also executed. Bank 1, zero driver torque/rate input, W=R=16384, zero base assist, and synthetic feedback values were supplied. The curve output was fed into the real PD routine with its actual stack arguments. Three repeated PD/mixer calls expose the initial derivative transient and subsequent steady result.

These tests intentionally exercise isolated stages. The state machine is not used to authorize engagement, and the earlier monitor fault is not cleared or bypassed in a claimed end-to-end execution. These numerical results cannot make the failing candidate acceptable.

| Normalized input | Feedback | Stock first / steady u | Candidate first / steady u |
|---:|---:|---:|---:|
| +1024 | 0 | 1024 / **836** | 2560 / **2090** |
| −1024 | 0 | −1024 / **−836** | −2560 / **−2090** |
| +400 | 0 | 1024 / 503 | 1898 / 1258 |
| +1024 | +2000 | 1024 / 492 | 2386 / 1746 |
| +1024 | −1000 | 1024 / 1007 | 2560 / 2261 |
| +1024 | +4864 | 0 / 0 | 1894 / 1254 |
| −1024 | −2000 | −1024 / −492 | −2386 / −1746 |
| +1024 | −32765 | 1024 / 1024 | 2560 / 2560 |

With the stated mixer inputs, its returned value equals u in these cases. This reproduces the **limited zero-feedback steady 2.5× digital-output result**, not a universal multiplier or a physical torque measurement. The tested signed arithmetic is actual ROM execution; this supersedes formula-only rounding assumptions for these particular cases.

## Release conclusion and limits

**Release status: REJECTED AFTER EMULATION.** The earlier RWD remains a known-failed experimental artifact. Its checksum validation remains valid but is not behavioral validation.

No monitor bypass or replacement firmware was produced during this test. A future calibration revision must account for independent recomputation and any other controller/monitor dependencies, then repeat the relevant execution tests; the monitor should not simply be disabled.

Not modeled: peripherals, interrupts, real-time scheduling, full boot, complete CAN reception, all controller states, motor/current-control dynamics, programming/dependency acceptance, or the physical steering mechanism. No vehicle communication or flashing occurred. Physical 2.5× torque remains unvalidated.

## Evidence

- [Full active-range and boundary sweep](THR_2p5_emulator_sweep.json)
- [Directed curve/monitor bank cases](THR_2p5_emulator_curve_monitor.json)
- [PD/mixer execution cases](THR_2p5_emulator_pd.json)
- [Interpreter checks](THR_2p5_emulator_engine_checks.json)
- [Updated RWD validation status](THR_2p5_RWD_validation.json)
- [Reproduction source package](THR_2p5_emulator_sources.zip)
