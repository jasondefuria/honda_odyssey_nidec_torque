# Integrated PTM assembly: wider operating grid

The candidate-address assembly now runs together with experimental P/D tables, matched monitor references, feedback filtering, and reduced output clamps. No flashable RWD is produced. These numbers define an exploratory test profile, not a calibrated tune.

## Explicit test profile

Banks1–3:
- P table75% of v4, rounded per entry; independent P reference updated identically.
- D table125% of v4, rounded per entry; independent D reference updated identically.
- Tracker alpha308 instead of410.
- D clamp512 instead of640; P and combined clamp2048 instead of2560.
- Matching clamp references0x67BEC/0x67BEE/0x67BF0 updated for each bank.

Target curve and existing minimum-engagement fields remain those of v4. These tests do not validate the low-speed behavior inherited from v4.

Feedforward gain8 and independent monitor gain8 are global literals in this prototype; unlike the bank1–3 table edits, they also affect bank7 and any other executing bank. Bank7 is therefore only an unchanged TABLE control, not an unchanged complete-controller control. A bank-specific feedforward activation policy has not been implemented.

## Wider test matrix

Each configuration runs108 stateful scenarios with6 updates each: banks1,3,7; schedule values-2176,0,512,2176; rate inputs-320,0,320; weights(16384,0,16384),(0,16384,16384),(8192,8192,8192). Updates transition through command0,+400,+1024,-1024,-400,0 and feedback0,+2000,+2000,-2000,-2000,0. State persists across each six-update scenario. Banks are fixed within scenarios; dynamic bank switching is not covered.

| Configuration | Updates | Nonzero flags from tested monitor |
|---|---:|---:|
| Zero-gain relocated helpers | 648 | 0 |
| Feedforward8 only | 648 | 0 |
| P/D/filter plus feedforward8, original clamps | 648 | 0 |
| Controller gain16 / monitor gain8 negative control | 648 | 324 (0x4) |
| Unmodified native v4 | 648 | 0 |
| P/D/filter plus feedforward8 and matched reduced clamps | 648 | 0 |

Total3888 integrated updates in this extended phase. The648 zero-gain traces exactly equal native-v4 traces. In the reduced-clamp profile, every observed output stays inside ±2048 for banks1/3 and ±1024 for bank7. The unchanged monitor still detects a gain disagreement in the negative control.

This exercises arithmetic behavior over a wider input slice, not a simulated vehicle. External feedback is prescribed independently of output, so no conclusion about physical stability, motor current or 40mph oscillation follows.

## Reviewable assembly artifact

review_patch_manifest.json records exact changed runs with source bytes, replacement bytes, addresses, original RWD SHA256 and image length. It includes the controller/monitor stubs, helpers and experimental calibration/reference changes. It deliberately does not contain repaired checksum bytes or claim to be a flash file. The builder is restricted to the verified source SHA256.

Source: work/test_ff_combined_grid.py; assembly: work/assemble_ff_inimage.py. The earlier in-memory serialization trial establishes the checksum/encode/decode workflow for a DIFFERENT feedforward-only profile; its checksum values must not be reused for this combined profile.

## Remaining release boundaries

Candidate ROM addresses still require ownership/execution/timing evidence. No hardware interrupt or worst-case execution-time test has run. Stack-margin and dynamic bank transitions remain unverified. The experimental parameter values are not selected from a measured plant response. No RWD or original firmware has been modified on disk; no ECU has been contacted.
