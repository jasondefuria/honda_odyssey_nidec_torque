# THR / TLA update-format comparison

Verified 2026-09-26 against the supplied THR RWD and original user.bin. No ECU communication or firmware modification was performed.

## Resolved payload discrepancy

The public jpancotti/rwd-xray tools/eps_tool.py default_decrypt_lookup_table decodes all 475,136 bytes of the supplied RWD to exactly user.bin[0xC000:0x80000]. Zero differing bytes. Re-encoding the stock window reproduces the entire encrypted payload. All 256 lookup entries are exercised. This independently resolves the prior RDX-formula mismatch.

Decoded payload SHA-256: 84bef32f4d6f99460dc0a42dda2aa681356370e8094d41a84f0f2a93fa8731d3.

This proves how this supplied container was encoded. It does not independently prove that the resident THR updater accepts that encoding.

## Comparison

| Property | Public TLA tool | Supplied THR file / stock bytes |
|---|---|---|
| Container | Z CR LF, six counted headers | Matches |
| Diagnostic address byte | 0x30 | Matches |
| Security header | 01 11 01 12 11 20 | Matches; same bytes at THR 0x51E4 |
| Encryption-key header | 01 02 03 | Matches |
| Payload encoding | 256-entry lookup | Exact match, independently decoded |
| Download start | 0x4000 | 0xC000 |
| Download length | 0x6C000 for TLA's 512 KiB dump | 0x74000 |
| Application end, exclusive | 0x70000 | 0x80000 |
| Checksum ROM slots | 0x6FF80, 0x6FFFE | 0x7FF80, 0x7FFFE |
| Integrity method | BE-u16 sum / negative sum | Reproduced: D0CA / A6E0; whole THR window sums to zero |
| Container trailer | LE-u32 byte sum | Passes |
| Version list | TLA versions | Only 39990-THR-A020, followed by two NUL bytes |

THR range record bytes at 0x52B2: 0100000000000000c00000074000. These agree with the start/length reported in the supplied findings. Establishing the rejecting RequestDownload control flow is a separate code-tracing task.

All application bytes match, including the identity table, calibration banks, checksum slots, and erased gaps. The RWD does not contain the region below 0xC000.

## Remaining UDS evidence

The September 25 notes describe SecurityAccess, F101, RequestDownload, TransferData, an updater overlay, and the final dependency check. Their code-level claims have not been independently reproduced in this comparison. Matching header constants is not proof of matching handler behavior.

No TLA firmware binary, updater disassembly, emulator scripts, or running log was supplied. The public container-building tool does not implement or document the complete resident UDS dispatch. Consequently a full TLA-to-THR handler match remains open, especially the resident decryption implementation and post-download dependency checks. Obtain the exact TLA dump used for the earlier trace and its trace/scripts to compare those paths directly.

Source: https://raw.githubusercontent.com/jpancotti/rwd-xray/master/tools/eps_tool.py (default lookup, TLA selection, stock extraction, checksum and container construction). Machine-readable local results: stock-rwd-validation.json.
