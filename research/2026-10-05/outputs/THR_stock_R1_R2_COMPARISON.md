# Stock, R1 and R2: matched SH-2A execution comparison

**R2 retains R1's tested controller-output behavior while resolving its observed monitor mismatches.** Stock and R2 raised no consistency faults in this comparison; R1 remains rejected. These results do not validate physical torque, ECU programming acceptance or road use.

Each image was reconstructed from its actual RWD payload and the unchanged stock prefix, then verified against its known full-image SHA-256. The same SH-2A SLEIGH interpreter, ROM routines, input sets and initial RAM conditions were used for all three. No firmware files were modified by this comparison.

## Compared files

| Image | RWD | ROM bytes changed from stock | RWD SHA-256 |
|---|---|---:|---|
| Stock | 39990-THR-A020_stock_pure.rwd | 0 | `5fb7dbc298cfc4c897644f100d664aaa2a55a6c9b46355cd8e13a5f3fd782c4c` |
| R1, rejected | 39990-THR-A020_2p5_PEAK_EXPERIMENTAL_UNVALIDATED.rwd | 58 | `4a8965d4c5991afa14e250b068d38a268e805699398c51674dfa016200d431eb` |
| R2, experimental | 39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd | 112 | `dbfe61804b35c6ff8855c0c02115c72c5fdd26d6f82e5e2209cf72bbae120311` |

All three RWDs are 475,189 bytes, carry identical headers and describe the same 0xC000 / 0x74000 application range. R1-to-R2 differs in 58 ROM bytes: independent reference calibration and checksum changes. The main controller calibration and executable instructions are identical between R1 and R2.

## Test scope

Actual routines `0x7276A` (preprocessing/fade/curve/PD) and `0x74C9C` (mixer) execute. Actual fade, curve, PD and mixer monitor routines run afterward, followed by evaluation/response callbacks. ROM slope initialization runs before each bank's cases. No function or instruction hooks are used.

Each image receives **252 static cases**, each run for six calls:

- Banks 1, 2, 3 and 7.
- Selected command: −4096, −2048, −512, 0, +512, +2048, +4096.
- Synthetic feedback: −2000, 0, +2000.
- Driver input: 0, 767, 768.

Each image also receives **four bank-1 sequences totaling 86 calls**: command step/release/reversal, a command ramp, driver-override boundary transitions, and a feedback sweep. Total comparison: 756 static cases and 258 sequence calls, or 4,794 combined pipeline/mixer evaluations including the six calls per static case.

Other supplied conditions are fixed: full W/R authority, zero base assist, speed input 60 counts, and zero synthetic E0-rate input. These are raw firmware counts, not calibrated physical torque. The engagement state machine, real-time scheduler, complete fault publication, hardware and mechanical plant are not executed.

## Monitor results

| Result per file | Stock | R1 | R2 |
|---|---:|---:|---:|
| Static cases with a monitor fault | 0 / 252 | **108 / 252** | **0 / 252** |
| Sequence calls observing a fault | 0 / 86 | **75 / 86** | **0 / 86** |
| Unchanged bank 7 behavior | Reference | Matches stock | Matches stock |

R1's outputs reported below are isolated calculations observed alongside a fault. The harness records the diagnostic callback but does not schedule the complete resulting ECU state transition. Continued numerical output after an R1 fault is therefore **not evidence that the real vehicle would continue providing that output**.

## Steady controller-output comparison

Bank 1. Values are the sixth repeated-call controller output, which also equals the mixer return under the supplied conditions.

| Command | Feedback | Driver input | Stock | R1 | R2 | R2 / stock |
|---:|---:|---:|---:|---:|---:|---:|
| +512 | 0 | 0 | 157 | 310 | 310 | **1.975×** |
| +2048 | 0 | 0 | 611 | 1527 | 1527 | 2.499× |
| +4096 | 0 | 0 | 836 | 2090 | 2090 | **2.500×** |
| −4096 | 0 | 0 | −836 | −2090 | −2090 | **2.500×** |
| +4096 | +2000 | 0 | 492 | 1746 | 1746 | **3.549×** |
| +4096 | −2000 | 0 | 1024 | 2433 | 2433 | **2.376×** |
| +4096 | 0 | 767 | 23 | 52 | 52 | 2.261× |
| +4096 | 0 | 768 | 0 | 0 | 0 | Undefined |

All R1 rows above except the final zero-output case raise a monitor fault in the repeated evaluations. R2 and stock raise none for these rows.

The complete tested output traces—not just these selected values—match between R1 and R2 for faded input, command-curve output, controller u and mixer output. The monitor behavior distinguishes them.

## Transition behavior

For zero feedback and zero driver input:

| Transition | Stock | R2 |
|---|---:|---:|
| First call after command 0 → +4096 | +1024 | +2560 |
| Subsequent steady +4096 | +836 | +2090 |
| First call after +4096 → 0 | **−640** | **−640** |
| Following zero-command call | 0 | 0 |
| First call after 0 → −4096 | −1024 | −2560 |
| Subsequent steady −4096 | −836 | −2090 |
| First call after −4096 → 0 | **+640** | **+640** |

The unchanged derivative ceiling is consistent with the equal release transients. These are invocation-indexed software traces, not milliseconds or measured vehicle motion.

The driver-input sequence adds a qualification to the earlier fresh-state cutoff test. At command +4096 and zero feedback, after holding driver input 767 and then crossing to 768, **both stock and R2 produce −57 for one call, then settle to zero**. The faded command is cut, but the staged controller retains derivative history. With fresh zero history and driver input already 768, both start and remain at zero. Full engagement/authority and fault-state dynamics are not included here; this is not a measured physical override response.

## Interpretation

R2 resolves the previously observed curve/PD consistency failures while preserving the intended modified main calculation. Its 2.5× label is valid for the specific zero-feedback peak digital-output result, not as a uniform command multiplier or a validated physical steering-torque ratio. No new firmware revision was created in this comparison.

## Evidence

- [Full matched inputs and per-call traces](THR_stock_R1_R2_emulation_comparison.json)
- [Exact byte-difference ranges](THR_stock_R1_R2_byte_comparison.json)
- [Reproduction sources](THR_three_way_comparison_sources.zip)
- [Earlier R2 validation report](THR_R2_README.md)
