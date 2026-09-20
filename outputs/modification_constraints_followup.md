# THR-A020 modification analysis: runtime allowance and gain scheduling

Continued static analysis of the preserved original image. These findings identify behavior that a proposed modification must account for; they do not specify a validated torque-increase patch.

## The 8868 ceiling is also a runtime ramp endpoint

The writer at `0x196A4`–`0x1983A` updates `M32[0xFFF8541C]` between zero and 36,323,328. The downstream request limiter divides this value by 4096, so the fully enabled allowance is exactly **8868 command units**. This agrees numerically with the previously identified combiner limit at `0x57C94`.

The allowance increases or decreases according to state bits. Decoded increments, expressed both as stored units and equivalent command units, are:

| Direction/path | Stored increment | Command units per evaluated update |
|---|---:|---:|
| Increase, first branch (`0x196B0`) | 145295 | 35.4724 |
| Increase, second branch (`0x196D4`) | 290590 | 70.9448 |
| Decrease (`0x1979E` plus `0x197A8`) | −1452950 | −354.7241 |
| Decrease (`0x197C6`, `0x1980C`) | −145295 | −35.4724 |
| Decrease (`0x197EE`) | −36324 | −8.8682 |

These are per-update quantities, not per-second rates. The conditions selecting the branches must be interpreted in conjunction with upstream status logic. Writes at `0x19708` and `0x1983A` are guarded by a comparison with the previously read value, under interrupt masking. Other writers and zeroing paths exist.

A larger nonlinear target can still encounter this allowance and the earlier combiner ceiling. The numerical relationship alone does not establish a conversion to newton-metres.

## The output magnitude limit is coupled to reciprocal normalization

Function `0x29C48`, called at `0x38DCC`, takes its first argument from the word at offset 10 of the structure returned by `0x275F8`: `M16[0xFFF8554E]`. Its physical meaning is not established here.

Let `q = clamp(signed16(argument), 1536, 4352)`. The function writes:

- `M16[0xFFF86D4A] = trunc(q * 23170 / 32768)`.
- `M16[0xFFF86D4E] = q & ~1`.
- `M32[0xFFF86D40] = trunc(0x3FFFFFFF / floor(q / 2))`.

The previous trace showed that `0x2A87A` clamps a command to the `0xFFF86D4E` magnitude and then multiplies it by `0xFFF86D40 / 32768`. Thus these values form a coupled limit-and-normalization pair. Treating the limit alone as a torque multiplier would miss the compensating reciprocal gain.

The same routine computes additional state using its second argument, supplied from `M16[0xFFF8551E]`. It writes scheduled values at `0xFFF86D52` and `0xFFF86D54`; the former is clamped between 26214 and 32767. Neither has been equated to physical torque.

## Inner-loop gains have multiple operating modes

`0x29C48` transfers to `0x2A96C`. This latter function writes the gains at `0xFFF86D68` and `0xFFF86D6A`, previously observed in the lower-level feedback helpers. It also writes a third coefficient at `0xFFF86D6C`.

| Branch condition | Coefficients at `+0`, `+2`, `+4` relative to `0xFFF86D68` |
|---|---|
| Byte `0xFFF86D6E` equals 1 | 4650, 1066, 1550 |
| Otherwise, word `0xFFF86D70` equals zero | 4367, 1005, 1456 |
| Otherwise | Runtime-computed values |

In the computed branch, a sixteen-entry history at `0xFFF86D78` and sum at `0xFFF86D74` produce a factor bounded to 0–256, subject to status overrides. The first two coefficients are formed from RAM base/delta pairs:

```text
P = signed16(M16[0xFFF86D9E] + ((M16[0xFFF86DA0] * factor) >> 8))
I = low16(M16[0xFFF86DA2] + ((M16[0xFFF86DA4] * factor) >> 8))
third = trunc(P / 3)
```

The multiplications use signed words and arithmetic shifts. The code writes the computed values under interrupt masking. This analysis has not yet established every initializer for these RAM base/delta values or the physical meaning of the mode conditions.

This is feedback gain scheduling. Increasing these coefficients would alter loop response and cannot be interpreted as an equivalent increase in steady-state torque demand.

## Implication for the proposed modification

The strongest identified candidate for studying a changed command-to-target relationship remains the nonlinear conversion at `0x7415C`, with the separate recomputation at `0x6ACC4`. The earlier report established matching main/monitor tables in all seven banks. A study of that relationship must preserve agreement and account for downstream limits; it is not evidence that a 2.5× patch is ready.

Still unresolved are complete monitor-flag propagation, active bank and mode selection on the actual ECU, engineering units, and the full Odyssey flash-container integrity requirements. This pass established additional limiter and gain writers; it did not complete the monitor-to-fault trace.

Original `user.bin` and its preserved copy remain identical. No firmware modification was made.

Evidence: [runtime disassembly](runtime_constraints_disassembly.txt), [arithmetic verification](runtime_constraints_verification.json), [previous actuator trace](odyssey_monitor_and_actuator_trace.md).
