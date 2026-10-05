# Honda Odyssey Nidec EPS torque research

Firmware reverse engineering, experimental torque-mod candidates, SH-2A emulation, checksum validation and controller comparisons.

## Latest research snapshot

[2026-10-05 archive](research/2026-10-05/README.md) contains the newer R2–v4/PTM work, Clarity/Civic comparisons, analysis scripts and detailed test results. Existing files at the repository root and in the original `work/` and `outputs/` directories are historical and were preserved.

**Current working candidate:** [PTM-39990-THR,A020-EXPERIMENTAL.rwd](research/2026-10-05/outputs/odyssey_ptm_candidate/PTM-39990-THR,A020-EXPERIMENTAL.rwd), with global feedforward including bank 7.

SHA256: `1c45356e7dffd85a416d79ae262641756f2bdc37e99fe9f0422981f1a4e033f1`

The no-feedforward-in-bank-7 variant is retained as a **superseded experiment**. Historical binaries must not be mistaken for the current candidate.

## Verification limits

These are experimental research artifacts, not a calibrated or ECU-validated release. Checksum consistency and bounded emulation do not establish hardware code-space ownership, timing/interrupt margin, physical torque, steering stability or suitability for vehicle use. The final emulator report documents both passes and limitations, including output jumps during synthetic bank transitions and monitor detection gaps also present in stock.

Start with the [final-file emulator report](research/2026-10-05/outputs/ptm_final_emulator/REPORT.md), [candidate details](research/2026-10-05/outputs/odyssey_ptm_candidate/README.md) and [checksum comparison](research/2026-10-05/outputs/odyssey_ptm_candidate/checksum_comparison.json).
