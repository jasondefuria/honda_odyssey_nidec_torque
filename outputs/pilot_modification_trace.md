# Pilot TG7-A060: traced modification regions and Odyssey comparison

All 1,894 changed payload bytes in the supplied Pilot 2X reference are now accounted for by the regions below. This is complete coverage of the differences, **not a claim that the complete CAN-to-motor path or all fault behavior is proven**. Originals remain unchanged.

## Bank selection and complete target table

`0x36BFA` obtains a selector through `0x35BC8`, accepts values 1–5, subtracts one, and defaults to index zero otherwise. Pointer table `0x1E4C4` selects these bases, in selector order:

`0x21FB2, 0x21130, 0x202AE, 0x1F42C, 0x1E5AA`.

The selected pointer is stored at `gp-0x4584`. Absolute gp has not been established in this pass; retaining relative RAM addresses avoids inventing absolute addresses.

Function `0x363DE` reads signed input from `gp-0x45C8`, takes its magnitude, limits the index to 255, and reads a 256-entry LE16 table at selected-base + `0x426`. It restores the input sign and writes the target to `gp-0x45C6`. The ascending-address first table spans `0x1E9D0`–`0x1EBD0` (end exclusive). It uses direct indexing, not the Odyssey's nine-point interpolation.

The changed indices are 66–255 in all five tables; indices 0–65 are unchanged. Representative values:

| Index | Stock | Pilot 2X |
|---:|---:|---:|
| 0 | 0 | 0 |
| 65 | 3067 | 3067 |
| 66 | 3087 | 3104 |
| 128 | 4307 | 5626 |
| 192 | 5120 | 8314 |
| 255 | 5120 | 10246 |

Thus even within the table, this is a shaped increase, not uniform doubling. The index clamp permits selecting entry 255, but upstream operating conditions determine whether it is reached.

## Controller and all other main-bank changes

The target is consumed by `0x3644E`. It subtracts feedback at `gp-0x45D4`, uses scheduled byte gains from bank + `0xA26` and `0xB26`, and computes proportional and difference contributions. The previous error is stored at `gp-0x45FC`.

The helper at `0x33722` is significant: for positive shift count n it performs signed rounding to nearest, with half-magnitudes rounded away from zero:

`R(x,n) = sign(x) * floor((abs(x) + 2^(n-1)) / 2^n)`.

This differs from truncation toward zero. The Pilot formulas must not inherit the Odyssey's rounding assumptions.

The proportional term is limited by byte bank + `0xC78`; the difference term by byte + `0xC77`. Their sum undergoes a scheduled multiplication and `R(product,16)`, then a clamp from byte + `0xC79`, producing `gp-0x45C4`.

`0x365A2` clamps this result again to a dynamic byte limit at `gp-0x4586`, multiplies by 655, applies `R(product,8)`, and limits the final correction using word bank + `0xC7A`, producing `gp-0x45C0`.

| Changed field | Stock → 2X | Traced role |
|---|---:|---|
| bank + `0xC34`, LE16 | 40960 → 48640 | Upper bound in the computation ending at `0x3752C`; its result is shifted right eight to publish the dynamic byte limit at `gp-0x4586`. These upper bounds correspond to 160 → 190 after that shift. |
| bank + `0xC78`, byte | 128 → 190 | Proportional-term magnitude clamp at `0x364DC` onward. |
| bank + `0xC79`, byte | 160 → 190 | Combined scheduled-correction clamp at `0x36568` onward. |
| bank + `0xC7A`, LE16 | 409 → 486 | Final correction clamp at `0x365DC` onward. |
| bank + `0xC81`, byte | 20 → 1 | Lower threshold in a compound status/acceptance test at `0x36F36`–`0x36F4C`, compared against r28; upper threshold is + `0xC82`. It is not a torque scale factor. The input's physical meaning remains unresolved. |

Each change repeats across five banks. Byte + `0xC77`, the difference-term clamp, is not one of the changed fields.

## Separate 10 → 1 threshold

The five bytes at `0x2BDB8 + k*0x278` are selected through pointer table `0x2BDA4` by `0x3B018`; selected pointer storage is `gp-0x4380`.

`0x3B358` reads byte zero, multiplies it by 100, and compares four unsigned words at `gp-0x43F4`, `-0x43F2`, `-0x43F0`, and `-0x43EE`. It compares a fifth word at `gp-0x43EC` against the unmultiplied byte. Any value above its threshold sets `gp-0x43CA`; otherwise that flag is cleared. The modified thresholds are 100 instead of 1000 for the first four signals and 1 instead of 10 for the fifth.

`0x3B6A4` propagates this flag into bit zero at the address constructed as `(0xFEE00000 - 0xFAC) mod 2^32 = 0xFEDFF054`. This establishes a status-bit effect, not a complete fault or shutdown interpretation. Calling this edit a torque multiplier or a proven safety-check bypass would be unsupported.

## Correction added to main request, then limited

`0x36880` eventually multiplies the correction at `gp-0x45C0` by the blend at `gp-0x45B6`, applies `R(product,13)`, adds it to the original function input, and publishes `gp-0x45BE` at `0x36B26`.

The caller path is explicit:

`0x31BA8 → 0x3B12A → 0x36C34 → 0x36880 → return → 0x32A50 → 0x3E82A → 0x3585E`.

`0x36C34` conditionally runs the target/controller pipeline, so the modified curve is not necessarily active on every call. `0x32A50` clamps the resulting request to **±2457**. `0x3E82A` multiplies it by signed word `gp-0x446C` and arithmetic-shifts by 12. `0x3585E` can select an alternative computed request, itself clamped to ±2457. The result is stored at `gp-0x4A90`; `0x32FB8` reads that result and applies another signed-byte multiplication.

This proves that a doubled target endpoint does not imply a doubled final request. The net result also depends on error, term saturation, blending, the main request, later scaling, and mode gates.

## Input-side trace: established and remaining

The upstream path includes getter `0x41A8A`, which reads `gp-0x7AA8`. That word is copied at `0x408BC` from `gp-0x7FB6`. Parser `0x40534`, when its status argument permits, constructs the latter from payload bytes zero and one in big-endian order. It also combines payload byte two with a bit from byte four and publishes a status byte. A callback pointer to `0x40534` exists at `0x12828`.

This layout is consistent with the steering-command payload already studied, but the Pilot callback-to-CAN-ID association is **not yet proven**. Do not substitute a matching byte layout for the missing dispatch trace. In particular, a literal 0xE4 found elsewhere in the listing is arithmetic data and does not establish CAN routing.

## Integrity and accounting

Both supplied-reference and stock container checks pass. Decoded cumulative LE32 sums through offsets `0xA000`, `0x1D000`, and `0x4FF00` are zero. The final changed word at flash `0x2CFFC` is the balancing word immediately before the second boundary. These checks establish container/data consistency; the firmware's own startup and periodic integrity consumers still require separate tracing.

All changed bytes fall in the five target-table portions, five copies of the five fields listed above, the five separate threshold bytes, and the four-byte checksum word. No changed byte lies outside that inventory. This inventory is not a proof that every modified location is exclusively data under every possible execution path.

## Comparison with Odyssey

Both firmware paths contain nonlinear target generation, feedback subtraction, proportional/difference terms, a bounded correction, and later combination with a main request. That supports a functional comparison. The Pilot uses direct 256-entry lookup, five pointer-selected banks, a different ISA and endianness, and a different payload/integrity scheme. The Odyssey uses its independently established SH-2A path, nine-point interpolation, seven banks, and separate recomputation monitor. There is no validated address or patch translation between them.

The outstanding work is Pilot CAN dispatch and validation, complete status-to-fault propagation, the final motor-output path, firmware-side integrity consumers, and physical units/active operating modes. The Odyssey's corresponding unresolved monitor propagation and runtime units also remain open. This report does not claim that “all tracing” is finished and does not provide a validated modification.

[Complete changed-byte coverage and samples](pilot_trace_verification.json) · [Reader disassembly](pilot_reader_disassembly.txt) · [Reference verification](pilot_reference_verification.json)
