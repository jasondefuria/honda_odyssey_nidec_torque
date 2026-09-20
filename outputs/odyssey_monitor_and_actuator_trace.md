# Odyssey THR-A020: parallel monitor and actuator trace

This extends the earlier CAN and Civic-comparison reports with static analysis of the original `user.bin`. No firmware bytes were changed. Image size: 524,288 bytes. SHA-256: `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`.

## Findings

The limited assist request reaches a lower-level feedback controller and then three hardware count writes. This is a statically connected, conditional execution path; it does not establish the active operating mode, physical current units, or achievable steering torque on a vehicle.

A separate monitor recomputes the nonlinear command curve using its own calibration tables. Consequently, checksum correctness alone would not establish that an altered main curve is consistent with the running firmware.

## Parallel calibration monitor

The main nonlinear conversion at `0x7415C` produces the structure at `0xFFF82FF0`, mirrored to `0xFFF8A484` by `0x7276A`. The scheduled function at `0x727E4`, called from `0x19098`, alternates work using `0xFFF86F4E`. One branch calls `0x6ACC4` at `0x72900`, passing the mirrored structure.

`0x6ACC4` snapshots four words: input, clamped input, interpolated magnitude, and signed target. It independently recomputes the last three and compares them with the snapshot.

| Calibration | Main bank 1 | Monitor bank 1 | Size |
|---|---:|---:|---:|
| Input magnitude limit | `0x57BAC` | `0x67BC2` | 2 bytes |
| Interpolation axis | `0x57BAE` | `0x67BC4` | 18 bytes |
| Interpolation values | `0x57BC0` | `0x67BD6` | 18 bytes |

The bank stride is `0x300`. Each pair is byte-identical in all seven banks. The limit is 1024; bank 1 values are `[0,2019,3230,3980,4345,4577,4721,4864,4864]`.

Comparisons occur at `0x6AD30`, `0x6ADF2`, and `0x6AE22`. Their counters are `0xFFF8A622`, `0xFFF8A624`, and `0xFFF8A626`. Constants at `0x398CC` specify threshold 255, increment 86, and decrement 255. Starting at zero, three consecutive evaluated mismatches produce 86, 172, 255. A matching evaluation returns the counter to zero. At threshold, the code sets bits 0, 1, and 2 respectively in `0xFFF8A5DB`. The elapsed time and resulting fault response require further tracing; these are evaluation counts, not milliseconds. This function does not clear the flag bits, but that does not establish permanent latching elsewhere.

There is also a larger controller-state monitor: `0x74C64` onward copies 116 bytes from `0xFFF83004` to `0xFFF8A498`; `0x6B010`, called at `0x727FA`, recomputes and compares portions of that state. Its complete correspondence and fault propagation remain unresolved.

## From outer control to the published request

The earlier analysis established the outer target conversion at `0x7415C`, feedback filtering at `0x742C0`, and proportional/difference terms at `0x7435C`. The combined result at `0xFFF83074` enters the weighted combiner at `0x74C9C`, called from `0x19E00`. The separately scaled value at `0xFFF83076` is not the identified input to this combiner.

Function `0x19D92` filters the combined request, supports an override, and applies several conditional magnitude limits before publishing it. Identified limit sources include:

- Conditional fixed magnitude 388 at `0x19E5C`–`0x19E82`.
- `M32[0xFFF8541C] / 4096`, with truncation toward zero.
- `M16[0xFFF83488]`, conditionally enabled by a status bit.
- `M16[0xFFF85460]`.
- `M32[0xFFF853C4] / 4096`.
- Conditional limits from `M32[0xFFF85428] / 4096` and `M32[0xFFF85430] / 4096`.

The `0xFFF8541C` limit is applied again later, and disable gates can zero the request. The final request is written to `0xFFF8534E` at `0x1A1FA`, then to `0xFFF81F52` and `0xFFF89402` at `0x1A23C`/`0x1A23E`. The preceding word at `0xFFF81F50` has a separate source and must not be conflated with this assist request.

These are runtime limits: their source addresses do not establish their active numerical values or engineering units.

## Lower-level feedback controller

Initialization at `0x38438` obtains `0xFFF81F50` through getter `0x18F22` and stores the pointer at `0xFFF86A78`. The processing function at `0x385A6` dereferences its second word at `0x38656`, fetching the published assist request.

On the traced branch, `0x1A700` applies a five-sample filter. It maintains five signed words at `0xFFF86B3C`–`0xFFF86B44`, a sum at `0xFFF86B38`, and a pointer at `0xFFF86B48`. Its normal result is `trunc(sum * 3276 / 16384)`; a flag derived from `0xFFF80032` selects the unfiltered input instead. The coefficient is approximately 0.199951, rather than exactly one fifth.

At `0x3867A`, the result is passed in `r6` to `0x291DE`. This branch is conditional on `0xFFF885B8`; alternative and disable paths exist.

`0x291DE` uses an angle and phase offsets, a table at `0x3B9D8`, and three feedback words at `0xFFF855D0`/`D2`/`D4` to form two transformed feedback signals at `0xFFF855D6` and `0xFFF855D8`. The filtered assist request is compared with the latter, through helpers `0x2A1BE` or `0x2A312` selected by `0xFFF86D5A`. Calls at `0x29448` and `0x29538` carry the request and feedback explicitly; subtraction occurs inside the helpers.

The first helper contains error shaping, proportional and integral contributions, bounded integrator state, and division by 8192 before signed output saturation. Gains are read from `0xFFF86D68` and `0xFFF86D6A`. The phase offsets and two-axis feedback arithmetic are consistent with a motor-current controller, but the sensor units and exact axis identities remain unverified.

## Three-channel hardware output

After lower-level control, angle-dependent transforms form two command words at `0xFFF85634` and `0xFFF85636`. The third at `0xFFF85638` is the negative sum, subject to saturation. Function `0x2A6E2`, called at `0x29696`, processes these three words, including normalization/common-mode arithmetic, then calls `0x2A87A`.

`0x2A87A` applies another magnitude limit from `0xFFF86D4E`, multiplies by `M32[0xFFF86D40]`, divides by 32768 with truncation toward zero, and transfers to `0x29B4C`. That function applies another limit from `0xFFF86D56`, with a conditional 26214 override, and records the three commands at `0xFFF855E0`/`E2`/`E4`.

For each resulting signed command, the count conversion is:

```text
count = min(2030, (((32768 - uint16(command)) & 65535) * 2031) >> 16)
```

The 16-bit wrap is intentional in this representation. Exhaustive arithmetic evaluation over signed commands −32767 through 32767 gives a monotone decreasing count in the range 0–2030.

`0x29C44` transfers to `0x28208`, which constructs base `0xFFFF8200` from signed immediate −126 shifted left eight bits. It writes:

| Instruction | Hardware address | Argument |
|---|---:|---|
| `0x2820C` | `0xFFFF8228` | `r5` |
| `0x28210` | `0xFFFF8226` | `r6` |
| `0x28214` | `0xFFFF822A` | `r4` |

These are definite three-channel hardware count writes. Their behavior is consistent with PWM compare outputs; exact peripheral register names have not been established from a hardware manual.

## Consequences for the proposed torque increase

There is no evidence that changing one table yields 2.5 times physical steering torque. The command curve, outer feedback controller, parallel monitors, runtime assist limits, inner feedback controller, and output limits all affect the result. The Civic A030 comparison already shows why an increased table endpoint can overstate the reachable gain when an earlier input clamp prevents reaching that endpoint.

The integrity findings remain those in the original report: startup additive checksum, two periodic CRC regions, and unresolved tail fields. This work does not establish a complete Odyssey RWD packaging/acceptance procedure. No checksum bypass, monitor bypass, patched image, or flashable modification was produced.

The remaining concrete questions are the active bank and runtime limits, units of the transformed feedback/request, complete monitor-to-fault propagation, and the hardware interpretation of the three count registers. They require additional static tracing and ultimately controlled measurements to relate firmware values to physical torque.

## Evidence and verification

- [Annotated disassembly windows](monitor_actuator_disassembly.txt)
- [Byte and arithmetic verification results](actuator_trace_verification.json)
- [Earlier CAN, scaling, and integrity report](odyssey_thr_a020_analysis.md)
- [Civic-to-Odyssey function comparison](civic_odyssey_function_mapping.md)

The checks verify the exact image hash, preserved-copy equality, matching parallel tables in all seven banks, debounce constants, hardware-store instruction bytes, and count conversion. They support the static trace but are not runtime validation of the ECU.
