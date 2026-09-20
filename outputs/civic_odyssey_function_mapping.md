# Civic–Odyssey functional mapping: follow-up

This is a static read-only comparison of Civic TBA-A030 stock, legacy mod, and PTM against the previously hashed Odyssey THR-A020 image. Repository references are pinned to commit b3366b5b56512805be8f0bf832b4981bfd958072. It identifies corresponding control roles, not interchangeable firmware addresses or physical units. No firmware was patched.

## 1. Functionally corresponding tables

| Role established from consumer arithmetic | Civic TBA-A030 | Odyssey THR-A020 |
|---|---|---|
| Bound signed command contribution, take magnitude, interpolate target, restore sign | function 0x296F6 | function 0x7415C |
| Input magnitude limit | 0x1371A = 1663 | bank-1 0x57BAC = 1024 |
| Target lookup axis | 0x1371C + selector*18 bytes | 0x57BAE + bank offset |
| Target lookup values | 0x1379A + selector*18 bytes | 0x57BC0 + bank offset |
| Difference-of-error gain values | 0x139EC + selector*18 bytes, consumer 0x29A68 | 0x57C5E + bank offset, within 0x7435C |
| Proportional gain values | 0x13AE8 + selector*18 bytes | 0x57C82 + bank offset |
| Difference term divisor / limit | 1024 / ±333 (0x1381A) | 64 / ±640 (0x57BD6) |
| Proportional term divisor / limit | 1024 / ±1774 (0x13818) | 64 / ±1024 (0x57BD8) |

Here selector strides are **decimal 18 bytes** for nine BE16 entries; Odyssey banks use a different layout. The mapping follows clamp → magnitude → interpolation → sign restoration and error/gain arithmetic. It does not assert common machine-code layout, calibration selector behavior, feedback units, or identical sampling periods.

Civic 0x29732 loads target values; 0x29734 loads the axis; 0x2973C calls interpolation helper 0x3A042 with nine entries. That helper clamps endpoints and performs integer linear interpolation with signed division. The signed result is written to an output structure at +6 (0x29768).

Odyssey 0x74180 loads its input limit, 0x741B2/0x741B8 load axis/values, and 0x7425C–0x7427A restore sign and write target at output +6, already identified as 0xFFF82FF6. Its implementation uses cached interpolation coefficients rather than the Civic helper. Initialization at 0x7234E–0x7235A passes the Odyssey axis, values, and RAM 0xFFF83168 to its setup helper; runtime lookup reads that RAM at 0x741C2. A parallel initialization also references the 0x67xxx calibration region; that path must be understood before assuming one table edit covers all execution/checking paths.

At Civic 0x29ACA, the target and feedback arguments are subtracted. At 0x29AE6, the selected historical error is subtracted from the current error. The difference is bounded, multiplied by the 0x139EC schedule, divided by 1024 at 0x29B22, and clamped. The 0x13AE8 schedule multiplies current error and is likewise divided by 1024 at 0x29B6C. This positively identifies the second legacy-mod table as a difference-of-error gain schedule. It is not a second direct torque conversion table.

In Odyssey the corresponding products are divided by 64 at 0x74924–0x7494E and 0x74A3C–0x74A66. Thus copying a Civic raw gain value produces a 16-fold difference in gain-per-error-unit from the divisor alone, before considering signal units or sample time.

## 2. The legacy A030 endpoint is not reachable in this target function

The A030 legacy mod leaves the input limit at 1663. Its upper axis knots are 1552 and 1774, so the maximum permitted input lies exactly halfway between them.

For selectors 0–5:

- Stock upper values: 5760, 5760.
- Modified upper values: 8640, 14400.
- At the input limit 1663: stock target 5760, modified target 11520.
- Ratio at that limit: **2.0**, despite the final table endpoint being 2.5× stock.

For selector 6:

- Stock upper values: 4570, 4570.
- Modified upper values: 7484, 10796.
- At 1663: stock target 4570, modified target 9140.
- Ratio: **2.0** again.

These results were recomputed for all seven actual table selections. They concern this function's maximum target, not measured steering torque or the separately named C020 2.5x image. Earlier observations about a 2.5× A030 table endpoint were numerically correct but incomplete without the input clamp.

## 3. PTM adds a target-dependent term

The PTM hook at Civic 0x297D6 redirects to 0x4F1CC, then returns to 0x297E4. The added routine preserves the original negative-product rounding correction and computes:

```
new_controller_result = clamp(old_controller_result
                              + ((signed16(r8) * 45) >> 10),
                              -32767, 32767)
```

The right shift is arithmetic, without a truncation-toward-zero correction for this newly added product. At the enclosing function entry, r8 is loaded from the target structure's signed output at +6 (0x297A4–0x297A8), then passed as the target argument to 0x29A68 (0x297D0). That callee preserves r8. Consequently the injected term is target-dependent and feed-forward-like, added to the returned error-controller result before the existing downstream multiplication/clamp. This describes its arithmetic role; physical feedforward units and tuning intent remain unverified.

PTM also changes target curves, gain curves, a feedback-filter coefficient, and other code/scalars. It cannot be summarized as the legacy mod with a larger multiplier, and its hook must not be transplanted into Odyssey code.

## 4. Odyssey controller reaches assist combination through 0xFFF83074

A further trace resolves the consumer of the unscaled controller term:

1. 0x74C28 writes the clamped combined controller term to output state +112 = **0xFFF83074**.
2. 0x74C2C writes the separately scaled value to +114 = **0xFFF83076**.
3. Assist combiner 0x74C9C sets GBR to **0xFFF82F04** at 0x74CB0–0x74CB2.
4. 0x74CD4 loads `mov.w @(368,gbr),r0`, which is **0xFFF83074**, then retains it in r7.
5. 0x74CE4 loads the weight at GBR+96 = **0xFFF82F64** into r1.
6. 0x74D3A multiplies those signed words. Subsequent signed divisions total **16384** (32 × 32 × 16), producing the weighted controller contribution.
7. 0x74DDE–0x74DE6 adds it to the caller's main term and another weighted term. 0x74DEA onward clamps the sum using bank-selected 0x57C94 (8868 in the examined banks).
8. This function is called at 0x19E00, followed by the already identified filter and further conditional/dynamic caps.

Thus the relevant chain is:

```
accepted E4 command → command shaping → target curve → error controller
→ FFF83074 → weight FFF82F64 / 16384 → assist combination
→ subsequent filters and limits
```

The direct reference to **FFF83076** at 0x756CA is a byte serializer: it multiplies the value by four, clamps to ±25600, and writes two bytes to a caller-provided buffer. This supports a telemetry/diagnostic role for that identified consumer. It does not prove there are no other indirect consumers. The scaled value should not be described as the established main combiner input.

## Remaining work

The evidence now narrows the Odyssey candidate control roles to target shaping and gain scheduling with an explicit assist-combination connection. Still unresolved are the bank/checking path involving the 0x67xxx region, complete upstream conditions and weight scheduling, final motor-current demand and actuator protections, runtime units/sample times, and Odyssey RWD handling. A tested 2.5× physical-output modification cannot be inferred from these static comparisons.
