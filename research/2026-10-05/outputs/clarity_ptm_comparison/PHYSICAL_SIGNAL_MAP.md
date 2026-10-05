# Clarity PTM signal map — evidence-bounded, physical calibration incomplete

## Scope
Stock TRW-A020 SHA256 d08a7f5c18ea6af9aaa1b366828fef226bb4ce192dc89a3d79d9c2661e1a7673 and ClarityMax SHA256 d4fe903bcf347495f4321be65a3c650c8c931f1650c3bef6443721da0dd80f7d. Latest Pminus5 variant differs only in first P-gain row and checksums. Static analysis; no hardware or live CAN access.

## Signals
| Signal | Storage / source | Consumer / mathematical meaning | Physical status |
|---|---|---|---|
| Curve input | signed16 at +8 of object pointed to by FFF87AD8 | 29FB4 clamps magnitude using 1380E, interpolates X 13810/Y 1388E with 18-byte row stride, restores sign | Raw internal units; CAN origin not proven |
| Mapped target | signed16 at +6 of object pointed to by FFF87AEC | 2A030 loads into r8; passed to 2A348 and PTM feedforward | Same numerical domain as feedback; not proven Nm |
| Feedback-like operand | signed16 FFF87A48 | 2A030 passes to 2A348, where subtracted from target | Sensor/estimator origin and units unresolved |
| Scheduling operand | same object +8 as curve input | 2A348 absolute value selects P/D gains | Not established as vehicle speed |
| Selected row | byte FFF87B7C | 18-byte offsets in P, D, and torque-curve tables | Mode-selection producer unresolved |
| Error | target minus feedback, register r11 | P multiplication and history-difference path; copied to output structure +24 | Internal error units |
| History input | caller output structure +24, loaded before current calculation | Clipped +/-65536 into FFF89690 | Consistent with previous error, but pointer alias/cycle interval unproven |
| Error difference | FFF89694 raw; FFF89698 clipped | D-like multiplication | Per-update difference, not physical derivative without sample period |
| P coefficient | 13BDC+18*row, X 13B5E+18*row | Interpolation then multiply error /1024 | Fixed-point coefficient; not sunnypilot kpV |
| D-like coefficient | 13AE0+18*row, X 13A62+18*row | Multiply clipped difference /1024 | Fixed-point coefficient; time scale unresolved |
| P clamp | signed16 1390C | Limits P term | 1774 stock,7373 PTM, internal units |
| D clamp | signed16 1390E | Limits D term | 333 stock,1774 PTM, internal units |
| P+D output | sum saturates +/-32767; raw sum at FFF8969C | returned to 2A030 | Intermediate controller output |
| Added feedforward | arithmetic shift (45*signed16(mapped target)) >>10 | Added to P+D, saturates +/-32767 | Target-based correction, not independent torque measurement |
| Later controller output | remaining scheduled factors /256 then clamp 13910 | output structure +3A | 1774 stock,9000 PTM; downstream motor/current path unresolved |
| Normalization source | signed32 FFF88548 | 2AF96 multiplies by3429 stock or1650 PTM, divides by256 and returns saturated result | Producer 35666 calls343FC then writes result;343FC processes buffered samples/differences; physical sensor and time base unproven |

## Telemetry words
The injected routine copies these words verbatim; a 32-bit quantity split into two words must not be treated as two independent physical signals.

| Mailbox | Four 16-bit source addresses in transmitted order |
|---|---|
| 51 | FFF801B2, FFF8969E, FFF87AE2, FFF87A48 |
| 48 | FFF88548, FFF8854A, FFF8968C, FFF8968E |
| 49 | FFF89690, FFF89692, FFF89694, FFF89696 |
| 50 | FFF87B02, FFF87B08, FFF87B28, FFF87B2A |

FFF8969E is the low halfword of raw P+D sum at FFF8969C. FFF88548/4A are halves of normalization source. FFF89690/92 are halves of clipped history; FFF89694/96 are halves of raw error difference. Remaining labels need pointer initialization tracing. CAN-ID-to-mailbox assignment and transmission timing remain to be independently verified.

## Conditional P patch caveat
1B864 uses r4 after 3ADD6 interpolation. r4 is overwritten with the lower X breakpoint on interior interpolation paths; it retains input on endpoint paths. Thus threshold behavior is path-dependent, not a proven smooth physical schedule. See SIGNAL_TRACE.md.

## Missing evidence for a complete physical map
Resolve initialization/pointers, CAN command decoding and units, feedback producer, sensor conversion, cycle timing, selected-row state, downstream current request and final limits. Absolute Nm/A calibration additionally requires sensor/actuator specifications or matched instrumented measurements. No physical labels or conversion factors have been invented to fill these gaps.

## Extended producer trace (2026-10-05)

### Feedback chain now connected

3432C ingests a 16-bit sample and writes the four-entry ring at FFF897E8. It also performs wrap-aware differences against the previous half-scaled sample. Its caller at 34F26 supplies a conditioned word: 34EFE–34F2A adds 0x1555 to an upstream value, subtracts a calibration word, and can retain the prior value under status bits. This is consistent with a cyclic position-like source, but sensor identity is not proven.

343FC snapshots the ring under interrupt masking, forms recent sample differences, then maintains an eight-entry history. It selects difference horizons using magnitude thresholds 20/40/60/80, with additional large-change handling at 2000 and 9175. Thus FFF88548 is a dynamically filtered sample-change estimate, not a raw CAN torque request. 35666 writes its return to FFF88548.

2AF96 -> 29F5C -> 3AB0C -> FFF87A48 completes the feedback path. 3AB0C is a stateful first-order tracker. With S the signed32 state at FFF8968C, x the normalized signed16 estimate, and alpha the word at1380A:

    old_output = trunc_toward_zero(S / 32768)
    S_next = S + alpha * (x - old_output)  [32-bit arithmetic]
    tracked = trunc_toward_zero(S_next / 32768)

29F5C then clamps tracked using the word at1380C and stores it at FFF87A48. Alpha changes1999->3200, corresponding to approximately0.061005->0.097656 per update. A time constant in seconds cannot be assigned without the update period. Lower normalization gain3429->1650 and higher tracker alpha change feedback amplitude and transient response simultaneously.

### Row override

2AD2E reads bit6 of byte FFF889F7 (FFF889EA+0xD). If clear, the selector FFF87B7C receives the caller's r5; if set it receives6 (seventh row). The controller does not necessarily use the first row affected by Pminus5. Caller argument producer and the flag's physical condition remain unresolved.

### Pointer switching

28E3C uses GBR FFF879B8 and selects alternate state/configuration structures according to a mode byte. It copies pointer/state groups between paired offsets, and points configuration slots at45BDC/45BFC. Consequently hardcoding an unobserved pointed-to RAM object's address would be unjustified. Initialization, mode semantics, and complete pointer resolution remain open.

### Honest completeness boundary

This is a more complete computational map, not a complete physical map. CAN-to-command origin, physical sensor designation, engineering-unit conversions, interrupt/task period, full selected-mode semantics, and downstream power-stage conversion remain unresolved. No bench calibration, ECU RAM snapshot, symbols, or hardware documentation is available in these files. Those gaps are not filled by table magnitudes or PTM filenames.

## Angle reconstruction evidence

34D4A–34DC8 computes channel magnitudes, signs and octant, forms a ratio scaled by2048, and indexes the table at46C94. The2049 entries follow atan(i/2048) at16384counts per turn; octant offsets are[0,-4096,-16384,12288,-8192,4096,8192,-12288]. SHLL2 then multiplies the reconstructed phase by4, followed by complement and offset/calibration handling. The downstream difference estimator therefore processes a reconstructed cyclic angle. This is stronger than the earlier generic sample-change label. It does not distinguish mechanical versus electrical angle or establish sensor identity, gear ratio, sampling interval, Nm, or amps. See angle_evidence.json for the numerical fit error.
