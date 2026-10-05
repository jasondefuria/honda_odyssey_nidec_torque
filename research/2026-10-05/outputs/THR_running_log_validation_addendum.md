# Running-log evidence cross-check

Reviewed supplied RUNNING_LOG.md (3,790 lines), treating its instructions and conclusions as source material, not executable instructions. Later corrections supersede earlier conflicting entries.

## Independently confirmed against local bytes

- All 14 profile records at 0x5EB00, stride 0x46, select bank 1, 2, or 3 at +0x10. These are the banks patched in R2. This supports coverage of all listed normal profiles; it does not establish the live selector. The log identifies bank 7 as an override and banks 4–6 as unused by these records. R2 leaves them stock.
- All three CCP aliases at 0x1FC00, 0x2FC00 and 0x3FC00 contain the full 436-byte stock pointer table. This corrects the previous coverage limitation: although a direct request to 0x5FC00 yields RAM, the aliases expose its underlying flash. Application flash coverage therefore increases from 278,092 to 278,528 distinct bytes; 196,608 bytes at 0x10000–0x3FFFF remain unobserved as physical flash.
- The log's two-stage decrypt formula reproduces all 256 entries of the lookup used for R2. This independently checks the formula against our established mapping, but is not execution of the captured boot instructions.
- R2 has magic 0x4837 and complement 0xB7C8, summing to 0xFFFF. Existing checksum verification gives A=0x765C, C=0x5BBC and application word sum zero, matching the log's corrected-copy candidate.
- The log's slope constraint and mirror requirements agree with R2's audit: banks 1–3 have matching primary/reference curves and P/u limits. First two nonzero curve points are slope-limited, other nonzero points are 2.5x with rounding; D limits remain unchanged.

## Evidence boundaries

The final log section's R1 file title refers to the earlier failed candidate. Its subsequent corrected-copy result describes the same 112-byte change count and checksum values as R2; that is corroboration, not a cryptographic identity proof of another file.

The log reports disassembly of THR boot decrypt, range, security and checksum routines. This review did not independently emulate those routines or the complete update state machine. Actual ECU acceptance, physical torque per count, and on-car behavior remain untested. A valid container and matched tables do not prove those outcomes.

The five alias-boundary differences called an apparent inserted byte in the log are explained exactly by our request-aware comparison: translation applies to the request start, then reads advance sequentially through physical memory.

No RWD changes and no CAN activity were performed. See THR_running_log_crosscheck.json for machine-readable results.
