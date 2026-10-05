# R2 RWD verification against the live CCP dump

Result: PASS for the scoped byte comparison and offline RWD checks. This is not ECU flash acceptance or physical torque validation.

Verified file: `39990-THR-A020_R2_2p5_PEAK_EXPERIMENTAL.rwd`
SHA-256: `dbfe61804b35c6ff8855c0c02115c72c5fdd26d6f82e5e2209cf72bbae120311`

## What the new capture establishes

The 278,092 directly observed application bytes all match the stock image used to build R2. Every one of R2's 112 changed bytes is within these observed regions; the live capture contains the expected stock preimage at all of them. Comparing R2 to these regions produces exactly those 112 intended differences and no others.

Direct application ranges (end exclusive): 0xC000–0x10000, 0x40000–0x5FC00, and 0x5FDB4–0x80000.

Reproducing the actual capture request boundaries and the known CCP remap accounts for 515,657 captured bytes with zero unexpected differences from stock. That total includes repeated alias views, not 515,657 distinct flash addresses. The remaining 8,631 captured bytes were excluded from this stock comparison: new boot bytes, pointer-table RAM views, and three bytes in the request spanning the boot boundary.

Five apparent mismatches at 0x20001–0x20003 and 0x30001–0x30002 are explained exactly by requests starting at 0x1FFFF and 0x2FFFE. The start address is remapped, and the returned bytes continue sequentially across 0x60000 rather than wrapping to 0x50000 mid-request. No captured file was altered.

The original image's first 8 KB consists entirely of FF placeholders. The new boot bytes agree across both dedicated reads and the full capture. They lie outside this RWD's payload, which begins at 0xC000, so their discovery does not itself require changing the RWD. The newly captured boot decrypt/check routines have not been executed or analyzed by this verification.

## RWD checks rerun

- Header and download range unchanged: start 0xC000, length 0x74000.
- Encoded payload decodes exactly to the reviewed R2 candidate; deterministic rebuild matches the existing RWD.
- Exact patch manifest matches, including main/reference calibration agreement.
- Container trailer checksum and application word checks pass: A=0x765C, C=0x5BBC, total application word sum zero.
- All ten existing negative validation tests still reject malformed or unreviewed inputs.

## Limits

197,044 application bytes were not directly observed: 0x10000–0x3FFFF is aliased, and 0x5FC00–0x5FDB3 returns RAM values. Consequently this capture cannot certify the whole installed flash image byte-for-byte. Existing offline checksum tests are not evidence that the actual bootloader accepts this file. Physical 2.5x torque, full ECU operation and road suitability remain unvalidated.

The RWD was not modified or flashed. No new CAN activity was performed for this verification.

Machine-readable results: [THR_R2_live_dump_verification.json](THR_R2_live_dump_verification.json).
