# Continued Clarity and Odyssey mapping — 2026-10-05

This supplement extends RECONSTRUCTION.md. The newly connected Odyssey sensor path supersedes that report's statement that its upstream feedback origin is unknown. Static evidence and eight focused instruction-execution cases are distinguished below.

## Odyssey: sensor phase to controller feedback

Verified chain:

    0x27682: conditioned paired-channel magnitudes/signs
      -> atan table 0x3A128, octant table 0x3B12A
      -> multiply phase by 4, complement, store FFF854EC
      -> buffered phase FFF854FA
    0x194B8: read both phases, unsigned halve each
      -> 0x1C068: wrapped difference, dynamic scaling, saturation
      -> FFF8029C
    0x726DA: snapshot FFF8029C on stack
      -> 0x742C0 -> 0x300DA tracker
      -> FFF83002
    0x7435C: mapped target minus feedback

### Sensor object binding

0x18EE8 calls 0x275F4, whose return is FFF854D4, and writes it to FFF85368. The consumer at 0x194C6 dereferences this pointer and reads object +0x18 and +0x26. Their concrete addresses are FFF854EC and FFF854FA.

0x27682 sets GBR to FFF854D4. It scales unsigned channel words at +0x30/+0x34 and +0x32/+0x36 by 1280/65536, subtracts each pair, then applies calibration and additional offsets. The two resulting signed channels at +8/+A supply magnitudes and signs for phase reconstruction. Which hardware channels and sensor axes these represent remains unproven.

At 0x27786 the old buffered word at FFF86C9C is copied to object +0x26, and the old object +0x18 is copied to FFF86C9C. The newly calculated phase is subsequently stored at +0x18. With one normal producer update per sample, +0x26 therefore represents the phase two producer updates earlier. Synchronization with the consumer still requires scheduler evidence; do not assume a millisecond interval.

### Numerical angle evidence

The 2049 words at 0x3A128 match:

    table[i] = round(atan(i/2048) * 16384/(2*pi)), i=0..2048

Maximum absolute residual from the unrounded formula: 0.4998343402814953 counts. Octant table 0x3B12A is `[0,-4096,-16384,12288,-8192,4096,8192,-12288]`. After octant handling, SHLL2 and NOT yield a cyclic 16-bit phase. These tables have the same numerical form as the Clarity tables at 0x46C94 and 0x47C96. This establishes an angle representation, not electrical/mechanical angle identity.

### Wrapped difference and normalization

0x194B8 reads the current and buffered phases as unsigned words and shifts each right by one before calling 0x1C068 with r6=0 and output pointer FFF8028C. Let a and b be those halved samples:

    delta = clamp(a-b, -32767, 32767)
    if delta > 16383: delta -= 32768
    elif delta < -16383: delta += 32768
    K = signed16(FFF80BB2)
    feedback_input = clamp((delta*K) arithmetic_shift_right 7, -32767, 32767)

The feedback input is written to output object +0x10 = FFF8029C. The same routine also writes delta at +4, a /4096-scaled saturated branch at +6, its wider intermediate at +0xC, and a separate clamped `(360*delta)>>8` branch at +8. The controller consumes +0x10, not +8. The extensive filter at 0x1C182 processes +8 and writes FFF803B0; it is a separate branch, not the direct source of FFF8029C.

0x20DA6–0x20DCE writes K as a nonnegative saturated quotient `(0x2BF2 << 16)/denominator`. The denominator's full origin and update timing are not yet resolved. K cannot currently be replaced by an assumed degrees-per-second or RPM factor.

Eight direct v4 instruction tests of 0x1C068 matched the equation: zero, positive/negative differences, both wrap directions, both half-cycle boundaries with saturation, and a non-power-of-two K. See feedback_delta_execution.json. Synthetic RAM only; no hardware timing, interrupts, or mechanical plant were tested.

## Relative controller scheduling, both ECUs

Odyssey 0x72032 calls 0x726DA on each invocation, while 0x7276A is called on alternating invocations using FFF86F4C. Consequently feedback snapshot/tracking and the larger preprocessing/PD path are not necessarily updated at the same rate.

Clarity 0x28B18 similarly calls 0x28D5A in its enabled path, and calls 0x28E3C on alternating invocations using FFF89663. Enable state FFF87994 must equal 1 for that path. Absolute task frequencies remain unknown.

## Clarity: curve-input producer connected

0x29CAE produces the signed word at +8 of the object pointed to by FFF87AD8. This is the word consumed by 0x29FB4's target curve.

The producer performs two eight-point lookups through a mode-dependent configuration pointer at FFF87A9C (=GBR FFF879E4 +0xB8). Both lookups use the absolute value of the routine's incoming r4. Their signed16 results are multiplied by weights at FFF879E4 and FFF879E6, summed, and divided by 16384 with truncation toward zero.

That weighted result is multiplied by a six-point lookup using X=0x1375E+12*row and Y=0x137B2+12*row. The six-point input is the absolute value of the word at FFF87A40 (GBR+0x5C). This product is divided by 256. A threshold at 0x1375C zeroes the result when the absolute incoming r4 is greater than or equal to it. The remaining result is multiplied by FFF87A08 (GBR+0x24), divided by 256, and saturated to ±32767.

The final +8 output is forced to zero if any of these is nonzero:

- byte FFF87B76;
- byte FFF87BA8;
- byte +6 of the routine's second-argument object.

Physical meanings of those gates are not established by this trace. This is a processed, scheduled command, not a proven unmodified CAN word.

### Input to this preprocessing path

0x28E3C reads FFF885D8 into r12 and later passes it as r4 to 0x29CAE. FFF885D8 is written in 0x35BA8 after calls to 0x30AC8, 0x30BA8 and 0x30FA6. If byte FFF889E6 equals 1, the original signed input to that wrapper is used instead. The chain therefore includes an upstream override path. Its CAN origin and engineering units remain unresolved.

### Resolved mode-dependent object pointers

0x28E3C uses GBR=FFF879B8 and writes the following concrete pointers:

| Mode path | Config pointer at FFF87A9C | Input object pointer FFF87AD8 | Target output pointer FFF87AEC | PD object pointer FFF87B70 |
|---|---|---|---|---|
| First group | 0x45BDC | FFF87AA0 | FFF87ADC | FFF87AF0 |
| Second group | 0x45BFC | FFF87ABC | FFF87AE4 | FFF87B30 |

Mode byte FFF87813 selects the group: value 1 selects the second; values other than 1 or 2 select the first; value 2 alternates based on FFF89666. These are pointer/mode facts, not identified vehicle conditions.

This resolves useful telemetry aliases. For the first PD group, FFF87B28 and FFF87B2A correspond to PD object +0x38 and +0x3A; for the second group those same absolute addresses are outside that selected PD object. Telemetry labels must include the active pointer group. FFF87AE2 equals the first target object's +6, while the second target object's +6 is FFF87AEA. A fixed telemetry address can therefore report the first group's retained value while another group is being processed.

## Remaining boundaries

Both ECUs now have angle-derived feedback provenance, but their estimator paths differ. Clarity uses the previously traced buffered/dynamically filtered difference source and normalization; Odyssey's direct controller branch uses the wrapped difference and K scaling identified here. Neither identifies rotor versus handwheel angle, electrical versus mechanical angle, gear ratio, sample interval or physical torque. The downstream current/PWM conversion, live bank/mode selection, and CAN-to-Clarity preprocessing origin remain open.

No RWD bytes were changed.

## Further trace: normalization constant and Clarity peripheral input

### Odyssey K is initialized from flash

0x20D70 loads a pointer to flash 0x5F604. That signed32 calibration is 107930 in the decoded v4 image. On the initialization branch selected by byte FFF80BAD == 1, 0x20DA6–0x20DCE calculates:

    K = clamp(trunc((0x2BF2 << 16) / 107930), 0, 32767) = 6831

It stores K to FFF80BB2. This resolves the denominator left open above: it is a flash calibration, not a live sensor read on this path. Its physical designation is still unresolved. This statement concerns this initialization branch; it is not proof that every execution context reaches it or that RAM cannot later be written indirectly.

Consequently the traced direct feedback branch, when initialized this way, is `clamp((wrapped_delta*6831)>>7, -32767,32767)` before the 0x742C0 tracker. The pre-tracker scale is 53.3671875 internal counts per halved-phase difference count. No seconds, degrees/s or Nm should be attached without the timing and sensor conversion.

Evidence: normalization_denominator.txt; calibration extraction in work/map_callers.py. This constant was decoded statically; the earlier eight execution cases tested several synthetic K values, not this initialization routine.

### Clarity input comes from a peripheral register on the traced path

The previous search for a CAN origin needs correction: the input to the traced preprocessing branch is connected to a peripheral-register read, not to a CAN payload by the evidence currently available.

0x353B2 reads a word at 0xFFFE784A (r13 = sign-extended -0x18800, offset +0x4A). It unsigned-halves the sample, calls 0x3AA68 with state FFF8983C and argument 4, doubles the returned signed word, and stores it to FFF885BE. The helper's complete temporal response has not yet been reconstructed; do not assume its argument means four milliseconds.

0x35338 then reads FFF885BE and passes it to 0x35688. This function computes, for unsigned16 u:

    v = trunc_toward_zero((10035*u - 328826880) / 65536)
    result = clamp(v, -4014, 4014)

The intercept is exactly `-10035*32768`, so equivalently the numerator is `10035*(u-32768)`. The centered conversion result is written to FFF885BA and passed to 0x35B5E.

0x35B5E calls 0x30AC8 and 0x30BA8, then obtains the output at FFF88224 through getter 0x30FA6. Byte FFF889E6 == 1 bypasses that result with the wrapper's original signed input. The selected result is written to FFF885D8, which 0x28E3C passes to 0x29CAE.

This extends the chain to:

    peripheral word FFFE784A
      -> halving / stateful helper / doubling -> FFF885BE
      -> centered conversion 0x35688 -> FFF885BA
      -> 0x35B5E processing or override -> FFF885D8
      -> 0x29CAE scheduling and gates
      -> target curve 0x29FB4

The exact peripheral function, sensor type, engineering units, and whether other modes inject an external request are still unresolved. In particular, the presence of this path does not justify labeling the PTM mapping as affecting only LKAS or as leaving handwheel-assist behavior untouched.

Evidence: clarity_command_source_next.txt, clarity_input_filter.txt, clarity_raw_input_writer_full.txt. Addresses in this section were traced in stock TRW-A020. Effects of PTM changes on these upstream regions need a targeted byte comparison before claiming identical behavior there.
