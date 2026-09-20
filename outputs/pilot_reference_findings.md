# Supplied TG7-A060 Pilot 2X reference

The supplied `39990-TG7-A060-2X (2019 Honda Pilot).rwd` is byte-for-byte identical to the repository's extensionless Pilot 2X work-in-progress artifact. SHA-256: `6ef205bceb5128f48e27182fa4e128173f2f6c0995192efd57809c237b81e40f`. The supplied original was read only.

## Decoding and architecture

The container contains 0x50000 payload bytes at flash address 0x10000. Its byte transform is `(((byte + 1) ^ 2) - 3) & 255`, not the Civic substitution lookup. Applying this transform to the repository stock RWD produces an exact match to its independently catalogued raw stock dump. Both stock and modified files pass the outer byte-sum checksum and the cumulative little-endian 32-bit sums through payload offsets 0xA000, 0x1D000, and 0x4FF00.

Correction: the preliminary Pilot comparison used the Civic decoder and was invalid. The intermediate decoded images and `pilot_initial_comparison.json` have been regenerated using the verified transform. Absence of matches in the earlier incorrectly decoded data must not be used as evidence.

The repository identifies this family as V850. Independent disassembly yields coherent little-endian V850 routines, including `prepare`, `jarl`, `dispose`-family conventions, and gp-relative data accesses. The Odyssey image analyzed in this task is SH-2A big-endian. Thus the statement that Pilot is "most similar" might refer to mechanical or control behavior, but the supplied file does not establish firmware-level interchangeability or that it is a closer code reference than Civic.

## Stock-to-2X changes

There are 1,894 changed decoded bytes. Five repeated curve-like data regions have stride 0xE82:

| Changed range, flash address (end exclusive) | Stock final LE16 | Modified final LE16 |
|---|---:|---:|
| 0x1EA54–0x1EBD0 | 5120 | 10246 |
| 0x1F8D6–0x1FA52 | 5120 | 10246 |
| 0x20758–0x208D4 | 5120 | 10246 |
| 0x215DA–0x21756 | 5120 | 10246 |
| 0x2245C–0x225D8 | 5120 | 10246 |

Each range contains 372 changed bytes over 380 bytes. These are changed portions of data, not proven complete table boundaries. The stock data reaches a 5120 plateau; the modified data rises toward approximately twice that value. The beginning of each changed range changes only slightly (3087 to 3104), so the change is not uniform multiplication by two.

Other repeated edits appear near each region, and five isolated byte edits change 10 to 1 at addresses 0x2BDB8, 0x2C030, 0x2C2A8, 0x2C520, and 0x2C798. Their functional roles are unproven. The final changed four-byte word is at 0x2CFFC, immediately before one verified checksum boundary. No evidence here establishes measured 2X physical torque, successful vehicle testing, or safe compatibility with Odyssey.

## Use for Odyssey research

This is useful as a paired stock/modified example of nonlinear calibration changes. The next comparison must identify the Pilot readers of those data regions and their units and limits, then map their roles to the already traced Odyssey functions. Copying Pilot offsets, decoding, or checksum rules would be incorrect for the Odyssey image. All previously established Odyssey findings remain anchored to the original Odyssey binary.

[Verification](pilot_reference_verification.json) · [Decoded differences](pilot_initial_comparison.json) · [Architecture disassembly](pilot_architecture_evidence.txt)

Repository reference: https://github.com/nrdr/openpilot/tree/b3366b5b56512805be8f0bf832b4981bfd958072/openpilot/nrdr/tools/eps/rwd
