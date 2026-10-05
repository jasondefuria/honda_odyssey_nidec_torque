# Odyssey R2 versus supplied 2019 Pilot TG7-A060

Compared actual RWD bytes for THR-A020 R2, TG7-A060 stock and the previously supplied TG7-A060 2X reference. The source identifies a 2019 Pilot; Elite trim is not independently established by these files.

| Feature | Odyssey R2 | Pilot 2X reference |
|---|---|---|
| Processor / byte order | SH-2A / big-endian | V850 / little-endian, per earlier instruction trace |
| Download range | C000–7FFFF | 10000–5FFFF |
| Payload bytes | 475,136 | 327,680 |
| Decoder | THR substitution mapping, verified with captured boot routine | (((c+1)^2)-3) & 255; stock decode matches raw stock |
| Target map | Nine-point interpolation | 256-entry direct lookup |
| Modified banks | Normal banks 1–3, primary and reference copies | Five pointer-selected banks |
| Curve endpoint, stock → modified | 4864 → 12160 (2.5x) | 5120 → 10246 (2.00117x) |
| D limit | 640 → 640 | 80 → 80 |
| P limit | 1024 → 2560 | 128 → 190 |
| Combined controller limit | 1024 → 2560 | 160 → 190 |
| Later correction clamp | Different THR output path; not directly equivalent | 409 → 486 |
| Changed decoded bytes vs own stock | 112 | 1,894 |

Numbers are firmware-specific units, not directly comparable physical torque. Neither label establishes measured physical gain. Both modifications leave the D limit unchanged.

Pilot's first 66 target entries are unchanged. Samples at indices 66, 128, 192 and 255 change 3087→3104, 4307→5626, 5120→8314 and 5120→10246. R2 changes its first two nonzero points by approximately 1.965x and 2.457x, with the rest scaled 2.5x with integer rounding. Both are shaped changes rather than uniform multiplication.

The Pilot also raises a dynamic-limit bound 40960→48640 and changes a per-bank status threshold 20→1. Existing Pilot tracing identifies another five 10→1 threshold edits affecting a status path. These are not torque multipliers, and their complete physical/fault effects are not established. R2 does not reproduce these changes. Pilot's downstream path contains blending and further limits; a doubled target endpoint does not imply doubled final output.

Fresh checks: all three container trailers pass; Pilot stock decode exactly equals its catalogued raw binary; Pilot stock and 2X cumulative LE32 sums through payload offsets A000, 1D000 and 4FF00 are zero. R2 decode exactly equals its reviewed candidate payload. Main Pilot bank values were freshly read for all five banks. Functional names and architectural conclusions use the earlier Pilot disassembly work; no new Pilot emulation was performed.

The files are useful for functional comparison, but processor, units, map layout, security header and checksum differences prevent direct patch/address translation. No files were modified or flashed.

Exact identities and values: THR_R2_vs_Pilot.json.
