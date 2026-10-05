# Captured THR boot routines: offline execution

## Result

R2 passes the captured decrypt, checksum and FF01 paths under the synthetic state described below. A one-byte payload corruption is rejected with NRC 0x72. No ECU actions, firmware edits or flashing were performed.

## Inputs and method

The verified 8,192-byte CCP boot capture replaces only the placeholder prefix of the existing R2 analysis image. Remaining code/calibration comes from R2. The SH-2A SLEIGH research interpreter executes original instructions without hooks. RAM begins zeroed except explicit test inputs. ROM writes and unmapped accesses fail. Peripherals, interrupts, physical flash programming and live UDS session state are not modeled. Service/watchdog branches therefore follow the synthetic RAM state, not a complete running ECU environment.

The R2 container was previously decoded and checked against this candidate with SHA-256 688f36d6fb0c3b0ae1a3c8d620c509f7279f015b5d74eb05fd98e2abf9b5847c. These tests consume that candidate; no firmware file was changed.

## Executed routines

| Routine | Inputs | Result |
|---|---|---|
| 0x0A00 byte transform | All 256 byte values after key stage 01 02 03 | Matches established decrypt table for every value |
| 0x14CE full decrypt | RAM buffer containing bytes 0–255; key 01 02 03 at FFF80C51; flag bit 2 at FFF80C58 | Return 0, all 256 outputs match; 9,707 translated blocks |
| 0x11BE validator stub | Arbitrary argument | Return 0 via original delay-slot instruction |
| 0x1306 checksum | Record with start C000 and length 74000 | Return 0; 12,895,770 translated blocks |
| 0x11C2 FF01 | One record at FFF80C98: start C000, length 74000, flag 2; other records inactive | Return 0; 12,896,047 translated blocks |
| 0x11C2 negative | Same record, one bit flipped at C010 in analysis image | Return 1; NRC 72 at FFF80C4E |
| 0x11C2 pending | Record flag 1 | Return 1; NRC 22 |
| 0x11C2 no records | All records inactive | Return 0; does not prove a payload was checked |

Counts are translated execution blocks, not timing or hardware cycles. Full checksum and FF01 include the original block reader and service routines. An initial 300,000-block limit was insufficient; the full-range runs completed with a 20-million limit. No acceptance result was inferred from the instruction-limit failures.

## Corrections and qualifications to the running log

**Range helper 0x1F1C checks overlap, not complete containment.** It tests whether either start falls within the other range. Executed cases against C000/74000 return 0 for the exact range, C000/10, BFFF/10 and C000/74001; 80000/10 returns 1. Download bounds may be constrained elsewhere. This helper alone cannot prove all range validation.

**0x1B18 is an internal block of the function starting at 0x1AD8.** Earlier code reads state and checks a marker before reaching it. The block includes both the 4837/B7C8 complementary pair and an alternative 4837/4837 case. Calling 0x1B18 as an independent function would omit its prologue and prior gates. Its full application-valid function was not executed in these tests.

**0x11BE returning zero is scoped to that stub.** This does not establish that other security/session/transport gates are absent. SecurityAccess wrappers and complete session authorization were not exercised.

**FF01 success depends on synthetic record state.** Its no-record case also returns zero, which is why the positive payload test explicitly supplies a flag-2 record and the corruption negative test is necessary. Successful execution does not prove a live ECU has reached the same state.

## Interpretation

The new boot capture now supplies direct executable evidence for R2's cipher and post-download checksum path. The corresponding corruption test demonstrates meaningful rejection. This is stronger than a formula-only checksum comparison, but is not a live flash acceptance test or validation of physical 2.5x steering torque. Remaining work includes full application-valid gating, session/erase/program sequence and hardware behavior; no claim of complete bootloader acceptance is made.

Results: THR_boot_execution.json and THR_boot_negative_execution.json.
