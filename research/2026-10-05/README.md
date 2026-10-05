# Torque-mod research snapshot — 2026-10-05

This dated snapshot preserves the newer workspace research without replacing the repository's older archive. `ARCHIVE_MANIFEST.json` records copied-file SHA256 hashes and exclusions.

## Navigation

| Area | Entry point |
|---|---|
| Current global-feedforward PTM | [Candidate and packaging notes](outputs/odyssey_ptm_candidate/README.md) |
| Final-file verification | [5,604-update emulator campaign](outputs/ptm_final_emulator/REPORT.md) |
| Combined assembly profile | [P/D, filter, feedforward and clamp tests](outputs/odyssey_ff_combined_grid/REPORT.md) |
| In-image assembly | [Placement and serialization](outputs/odyssey_ff_inimage/REPORT.md) |
| Independent monitor resolution | [P/D reference-table pairing](outputs/odyssey_pd_monitor_resolution/REPORT.md) |
| Feedforward monitor implementation | [Instruction implementation and fault tests](outputs/odyssey_ff_implementation/REPORT.md) |
| Clarity/Odyssey signal mapping | [Reconstruction](outputs/dual_ecu_reconstruction/RECONSTRUCTION.md), [continued mapping](outputs/dual_ecu_reconstruction/CONTINUED_MAPPING.md) |
| Clarity comparisons | [Detailed signal map](outputs/clarity_ptm_comparison/PHYSICAL_SIGNAL_MAP.md), [bank 7](outputs/clarity_ptm_comparison/bank7_comparison.json) |
| R2 development history | [R2 notes](outputs/THR_R2_README.md), [patch manifest](outputs/THR_R2_patch_manifest.json) |
| Boot/UDS analysis | [Boot report](outputs/THR_BOOT_ROUTINE_REPORT.md), [UDS review](outputs/THR_UDS_R2_FLASHER_REVIEW.md) |
| Scripts | [Work directory](work/) and [SH-2A execution model](work/emulation/sh2a_pcode.py) |
| Supplied comparison firmware | [Inputs](inputs/) |

## Candidate status

- **Current:** `outputs/odyssey_ptm_candidate/PTM-39990-THR,A020-EXPERIMENTAL.rwd`. Global feedforward, including bank 7; SHA256 `1c45356e7dffd85a416d79ae262641756f2bdc37e99fe9f0422981f1a4e033f1`.
- **Superseded:** `outputs/odyssey_ptm_no_bank7/` and the corresponding no-bank7 assembly experiments. Kept for provenance, not selected for continued work.
- Older R1/R2/v2/v3/v4 files and unsuccessful/checksum-repaired variants remain research history. Read their individual reports; inclusion is not endorsement.

PTM is an exploratory profile: banks 1–3 use P75%, D125%, tracker alpha308, D clamp512 and P/combined clamps2048 with matched references; feedforward gain8 has an independent monitor implementation. Existing v4 target curves and minimum-engagement settings are inherited. Internal scaling does not prove 2.5x physical torque.

## Reproduction and provenance

Run scripts from this snapshot's root, where `work/` and `outputs/` retain their workspace layout. Python plus `pypcode` is needed for SH-2A tests. The copied RWD parser and decryption lookup are under `work/eps_tools_transfer/.../rwd_format/` and `work/tla-decrypt-lookup.json`.

This is an archival snapshot, not a turnkey portable package. Some scripts retain absolute original macOS paths, a Python virtual-environment path, or references to older workspaces and raw capture/log inputs. Substitute the corresponding files under `inputs/` where available and supply deliberately excluded inputs if reproducing those older analyses. Reports also retain original local artifact paths; use this index to navigate the uploaded equivalents. Original scripts/results are preserved rather than silently rewritten.

Stock and Clarity/Civic PTM input files are supplied comparison artifacts; authorship is not asserted. Generated emulator outputs describe the tests actually run, not full ECU behavior. The latest reports supersede earlier incomplete interpretations where explicitly stated.

## Privacy and exclusions

Credentials, local Git repositories, Python environments, full openpilot checkouts, conversation transcripts, raw drive-download directories and raw live CCP/device captures are excluded. Duplicate ZIP bundles are excluded in favor of inspectable source artifacts. Derived tuning/replay analysis outputs and source scripts are included; they are not raw rlogs. The manifest lists exclusions from the workspace outputs tree. External files, environments and unrelated repositories were not swept into this archive.

## Unresolved

Hardware execution/ROM ownership, interrupt timing, stack margin, complete boot/peripheral behavior, measured physical torque and mechanical stability remain unverified. Model assumptions and detection limitations are documented in the reports. No upload to this repository constitutes a hardware acceptance test.
