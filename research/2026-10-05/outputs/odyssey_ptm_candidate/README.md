# Odyssey PTM experimental candidate

File: PTM-39990-THR,A020-EXPERIMENTAL.rwd

This packages the previously tested exploratory profile based on mod25xv4. It is not a calibrated or ECU-validated release. The original v4 file is unchanged.

## Included changes

Banks1–3: P gains75% and D gains125% of v4, rounded to integer entries; matched independent monitor gain tables; tracker alpha308; D clamp512; P and combined clamps2048 with matching reference limits. The target curves and minimum-engagement fields remain those of v4.

Feedforward gain8 and independently checked reference gain8 apply globally, including bank7. Controller helper at0x75800 and monitor helper at0x75900 preserve scratch registers and retain diagnostic rejection of an inconsistent feedforward result. Header and embedded identity remain inherited from v4; embedded ID is39990-THR,A020. ECU identity alone therefore does not distinguish this candidate from v4.

## Packaging verification

Exact reviewed patch manifest applied with original-byte assertions. Both documented runtime CRCs, application A/C checksums, downloaded word sum and trailing RWD sum pass. Parsing and decrypting the final container reproduces the intended patched payload byte-for-byte. See verification.json and SHA256SUMS.

Prior tests exercised the executable profile in an offline SH-2A model, including gain mismatches, saturation and a wider schedule/rate/weight grid. The final packaging verification establishes payload identity with that profile, not new hardware acceptance evidence.

## Unresolved before hardware deployment

Candidate helper space has not been proven unowned at runtime. Hardware execution permissions, interrupt stack margin and execution timing remain unverified. No measured physical torque, plant stability or vehicle safety validation exists. Global feedforward and inherited low-speed fields are intentional properties of this artifact, not independently validated calibration choices. Do not treat checksum success or an absence of flags in synthetic tests as evidence of readiness for vehicle use.

Detailed assembly/test reports are in ../odyssey_ff_inimage/REPORT.md and ../odyssey_ff_combined_grid/REPORT.md. Packaging script: work/package_ptm_candidate.py in the workspace.
