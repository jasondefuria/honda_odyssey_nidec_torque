# Experimental THR-A020 RWD — physical torque unvalidated

**UPDATE: FAILED SH-2A EMULATION — DO NOT FLASH.** The independent curve monitor flags the candidate after three evaluations of nonzero command inputs. The delivered RWD is retained unchanged only to reproduce this failure. See [the emulator report](THR_2p5_EMULATOR_REPORT.md). The offline container/checksum results below remain true but are insufficient for release.

File: `39990-THR-A020_2p5_PEAK_EXPERIMENTAL_UNVALIDATED.rwd`

**The RWD has been built and independently checked offline. A 2.5× physical steering-torque increase has NOT been validated.** The user confirmed that no physical measurements are available. This file is an experimental research artifact, not a validated vehicle update. Do not install it in a road-going vehicle on the strength of these checks.

## Build identity

- Size: 475,189 bytes.
- SHA-256: `4a8965d4c5991afa14e250b068d38a268e805699398c51674dfa016200d431eb`.
- Download range: start `0xC000`, length `0x74000`.
- Source stock image: `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`.
- Reconstructed candidate image: `04b48282b8350c2f987af2efe5c59bc73d62fe6bc3ddfbf01eed06b5d27f5189`.
- Encoding: the same 256-entry lookup as the supplied stock RWD, previously matched to the public TLA tool.
- Header, accepted software-version entry, diagnostic address, and key records: identical to the supplied THR stock-content RWD.

The original BIN and RWD have not been modified. The file retains the stock software identity; its filename and digest, not the reported part number, distinguish this experimental build.

## Changed behavior proposed by the candidate

Normal calibration banks 1–3 receive the curve and P/output ceilings listed in `THR_2p5_peak_candidate_patch.json`. The curve peak rises from 4864 to 12160. P and controller-output ceilings rise from 1024 to 2560. The derivative ceiling, gains, driver-override calibration, monitors, engagement thresholds, mixer ceiling, and other banks are byte-stock.

There are 58 changed ROM bytes including the two checksum words. There are 60 changed RWD bytes including the container trailer. Retaining other bytes does not prove unchanged dynamic behavior: the altered controller target can change the response of those same routines.

## Offline validation completed

- Strict container parsing, declared size, and trailer checksum.
- Independent parser and an independently recovered lookup from the stock encrypted/plaintext pair; every one of the 256 symbols was exercised without a mapping conflict.
- Decryption matches the exact reviewed candidate application byte-for-byte.
- The original-image prefix plus decrypted payload reproduces the pinned candidate SHA-256.
- Exact manifest reconstruction and changed-byte accounting.
- Firmware checksum A = `2393`, checksum C = `014e`, and whole-application BE-u16 sum = zero; family magic unchanged.
- Identity records and banks 4–8 unchanged.
- Deterministic rebuild reproduces the complete RWD.
- Fifteen negative tests reject corrupted inputs, incorrect candidate/template hashes, invalid lookup tables, incorrect/incomplete/overlapping manifests, corrupted/truncated containers, extra data, wrong lengths, and bad firmware checksums.

See `THR_2p5_RWD_validation.json` for machine-readable results. The builder is `build_thr_experimental_rwd.py` and has no ECU or network interface.

## Why this does not establish 2.5× physical torque

The number 2.5 describes one predicted steady controller-output condition: positive peak command, zero feedback, full authority, no fade, and no derivative contribution. Using the equations in the supplied findings, the counts change from 836 to 2090.

The same equations already rule out a universal 2.5× controller multiplier:

| Feedback at the same peak command | Stock modeled output | Candidate modeled output | Ratio |
|---:|---:|---:|---:|
| 0 | 836 | 2090 | 2.500 |
| 2000 | 492 | 1746 | 3.549 |
| -1000 | 1007 | 2261 | 2.245 |
| 4864 | 0 | 1254 | Undefined |

These are formula-only examples, not ROM execution or torque measurements. The modification changes the feedback target. It is not an output-stage multiplier, and its low-command curve also differs from uniform 2.5× scaling because of the reported interpolation limit.

Further, the LKAS output is combined with base assist and other terms before a shared clamp. No calibrated mapping from those counts to torque at a specified physical shaft has been established here. The feedback producer, downstream behavior, current limiting, and actual operating conditions remain relevant. Compute time cannot supply missing measurements or validate unknown plant dynamics.

## Validation status after emulator testing

Selected ROM routines have now been executed in a SH-2A SLEIGH p-code interpreter. The candidate **failed** its independent curve monitor. Isolated curve/PD/mixer execution reproduced the limited zero-feedback steady peak; it does not override the monitor failure. Full-system execution and the physical/ECU checks below remain unavailable.

- Complete-system SH-2A execution; the local interpreter is a research harness, not a validated hardware emulator.
- Comprehensive signed-intermediate, transient/derivative, and state-machine behavior (only the cases in the new report were executed).
- Resident THR decryption acceptance and final programming-dependency acceptance.
- Closed-loop bench behavior and stability.
- Calibrated physical torque ratio and road-use suitability.

A physical comparison must first define the torque measurement location and whether the target is total shaft torque or the incremental LKAS contribution. It needs calibrated, signed measurements from stock and candidate under matched command, speed/load, supply, temperature, driver-input and engagement conditions, with repeatability and measurement uncertainty reported. For incremental assist, the non-LKAS baseline must be accounted for. An instrumented EPS test bench and qualified test oversight are needed; controller/CAN counts alone do not validate the physical claim.

The earlier progress and patch files describe the candidate-generation stage before this RWD was built. This document supersedes their statement that no RWD has been generated; their unresolved controller and physical-validation limitations still apply.
