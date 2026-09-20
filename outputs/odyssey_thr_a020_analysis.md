# Odyssey THR-A020 EPS: CAN torque, controller, and integrity analysis

## Scope and result

This analysis is specific to the supplied 524,288-byte `user.bin`, SHA-256 `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`. The original attachment was read and copied, never patched. `user.original.bin` is a read-only preserved copy. Addresses below are hexadecimal; ROM addresses are offsets in this image, while `FFF…` addresses are runtime RAM/MMIO. Instruction decoding uses big-endian SH-2A, with critical instructions cross-checked using Capstone and Ghidra SLEIGH through pypcode. Delay slots matter.

**The genuine CAN 0xE4 path is established through receive hardware configuration, receive extraction, packet decoding, acceptance, and downstream command processing. Its torque word reaches RAM `FFF85198`, then conditionally `FFF8500C`. The identified command path does not use `3A128` as a torque scaling table. `3A128` is an exact 2,049-entry arctangent table used by a separate sensor-side angle calculation.** This is a positive identification of both paths, not an exhaustive proof against every possible indirect alias or shared downstream state.

No Civic/CR-V calibration offsets were assumed. The previously tentative `3DA90` and `3DBF0` structures were re-established from this image's executable configuration and receive code.

## 1. Proving the CAN receive path

### Configuration and slot identity

Function `3216C` loads peripheral base `FF600000` at `3217C`. Its configuration loop runs over 64 slots, with 16-byte records at `3DA90` and a 16-byte hardware slot stride. Instructions `322B0–322B2` multiply the index by 16. The code reads record byte `+D` for direction/type; type 1 takes the receive setup, and type 2 the transmit setup. At `32328`, the record's word at `+4` is masked with `07FF`, shifted left 18, and inserted into the hardware ID word. At `32338`, record byte `+C`, masked with 15, is inserted into the hardware DLC field. Receive setup sets bit 6 in the slot status byte at `FF600500 + slot`.

Slot 22 is therefore established from code, not proximity to an apparent ID value:

```
3DA90 + 22*10 = 3DBF0
3DBF0: 00 00 00 00 00 E4 00 00 00 00 00 00 05 01 00 00
                       ^ ID                 ^  ^
                                            5  receive type 1
```

The arithmetic above uses hexadecimal `10` as the 16-byte stride and decimal 22 as the slot index. Record `+4` contains standard ID `00E4`; `+C` specifies five bytes.

### Hardware extraction

Receive helper `323B2` takes `r4 = slot`, `r5 = destination`. It checks status bit 0 at `FF600500 + slot` (`323C4`) and waits on bit 1 (`323CE`). It copies eight bytes from `FF600000 + slot*16 + 6` to the destination (`323E2–32402`), then clears the receive flag. For this ordinary slot, `32460–32472` extracts the received DLC and requires it to be at least the configured record length. Thus the configuration is five bytes, and the code accepts DLC >= 5; the copy itself always moves eight bytes.

Handler `14618` sets its receive scratch buffer to `FFF85214`, calls `323B2` with slot 22 at `1463C`, and decodes only on successful receive.

| Payload | Parsed RAM | Decode evidence |
|---|---|---|
| `b0:b1` | `FFF85198`, word | `(uint8(b0)<<8) + uint8(b1)`; store at `14664` |
| `b2[7]` | `FFF8519A` | request bit, store at `1466C` |
| `b2[6]` | `FFF8519B` | one-bit field |
| `b2[3:2]` | `FFF8519C` | two-bit field |
| `b2[1:0]` | `FFF8519D` | two-bit field |
| `b4[6]` | `FFF8519E` | one-bit field |
| `b4[5:4]` | `FFF8519F` | rolling counter |
| `b4[3:0]` | `FFF851A0` | checksum nibble |
| receive event | `FFF851A3` | set to 1 at `146AE` |

The raw torque store precedes validity/acceptance checks. Seeing the raw word change is therefore not evidence that the controller accepted a packet.

### Packet integrity and accepted command

Helper `1531A` compares the previously saved counter with the newly parsed counter. Equality sets mask `4042` in the status word at `FFF850DA`; inequality clears that mask. This helper tests a repeated counter, not strictly a +1 modulo-4 progression.

Helper `15394` invokes `152AA` with ID `E4`, length 5, and the receive buffer. The check is:

```
(8 + 14 + 4 + sum(high_nibble(b[i]) + low_nibble(b[i]), i=0..4)) & 15 == 0
```

The initial ID contribution is from the low three nibbles of `ID | 0800`; the payload checksum nibble is included in the sum. Failure sets mask `2021` in `FFF850DA`; success clears it. Additional health-state handling, debounce, and timeouts surround these helpers. In particular, `153C4` can clear status under other health conditions, so the masks should not be treated as independently latched permanent faults.

Acceptance function `1113E` loads the word at `FFF85198` with signed extension (`11166`). It retains the previous accepted value when the checked health bit at status-block `+45` bit 2 is set, status word `+42 & 3` is nonzero, or either parsed two-bit field at `FFF8519C/9D` equals 3. On the acceptance branch, `111DE` stores the signed command to `FFF8500C`, with associated request/state fields nearby. These are identified gates; the report does not claim a complete semantic naming of every preceding state-machine branch.

Getter `1092C` returns `FFF8500C`. Scheduler code `1A262–1A272` conditionally invokes `72032`, which obtains that pointer at `72042`. Calls to `726DA` and the alternating `7276A` processing branch pass it onward. A separate consumer, `74C9C`, uses the accepted command magnitude for gain weighting.

```
CAN slot 22 / ID E4
  -> 323B2 -> FFF85214 scratch
  -> 14618 -> FFF85198 raw signed-word representation
  -> packet/status gates -> 1113E -> FFF8500C accepted command
  -> 72032 / 726DA / 7276A -> command shaping and controller
```

## 2. What `3A128` actually does

Every one of its 2,049 unsigned 16-bit entries matches:

```
T[i] = round(atan(i / 2048) * 8192 / pi),  i = 0..2048
```

The last entry is 2048 at `3B128`. The adjacent signed octant offsets at `3B12A` are `[0, -4096, -16384, 12288, -8192, 4096, 8192, -12288]`. The verifier reproduces the entire table, not just a few suggestive values.

The two identified direct table loads are `277E8` and `2786C`, both in function `27682`. That function operates relative to GBR `FFF854D4`, using four input words at `FFF85504`, `FFF85508`, `FFF85506`, and `FFF8550A`. Each is initially scaled by `1280/65536`. Pair differences, argument-supplied offsets, and correction words at `FFF86CCA` and `FFF86CC8` form X/Y quantities, with intermediate saturation to ±32767. Sign and relative magnitudes select an octant. The table index is:

```
index = min(abs(X), abs(Y)) * 2048 / max(abs(X), abs(Y))
```

with a zero-vector special case. The table result is combined with an octant offset, shifted left two bits, complemented, and stored as a word at `FFF854EC` (`2787A`). Further angle-related arithmetic produces other state, including `FFF85540`.

There is also positive evidence for a peripheral-fed input buffer: getter `275F0` returns `FFF85504`. Initializer `38FD8` stores that pointer at `FFF86AB0`, then programs transfer descriptors using peripheral source `FFFE8048` and destinations `FFF85508` and `FFF85504` (`39042–39056`). The descriptor base is `FF460000`, with another block at `+200`. This supports a sensor/peripheral acquisition interpretation; identifying the exact peripheral channel and physical sensor requires the correct MCU register documentation or hardware observations.

**Conclusion:** the earlier characterization of `3A128` as the incoming E4 torque normalization curve is contradicted by its mathematical contents and identified callers. No E4 command-to-table lookup was found. Shared control-system interaction between command and measured angle is not the same as the command indexing this table.

## 3. Command scaling, limits, and controller terms

All numbers below are firmware integer units. A physical Nm conversion or actuator-current unit has not been established.

### Calibration selection

`19366–193A0` derives a variant from byte `FFF81F68` (getter `2F8E8` returns its containing block at `FFF81F58`), with an override to variant 7 when `FFF85420` or `FFF85421` is 1. It stores `q = (variant-1)*180` at `FFF82F04`. Word-table addressing uses `2*q`, giving a `300`-byte stride across seven banks. Listed calibration addresses are bank-1 bases; add `(variant-1)*300`. The active runtime bank is unknown. The principal limits below agree across all seven banks in this binary; the verifier dumps them individually. Curve values quoted below are bank-1 values unless otherwise stated; do not assume every gain/filter calibration is identical across banks.

### Command shaping

| Function | Operation | Output / calibration |
|---|---|---|
| `73A28` | Read signed accepted command. If the examined flags at `FFF82F0F–FFF82F13` are active, clamp it to ±26; otherwise preserve it. Divide by 4, truncating toward zero. | raw `FFF82F84`; post-clamp `FFF82F8C`; divided `FFF82F8E`; limit `57CDA` |
| `750E8` | Monitor raw command against +4096 and -4096 with state/timing logic. | thresholds `57CD6/57CD8`; **not an immediate ±4096 command clamp** |
| `73AE0` | Use a context scalar and the mean of two other words to select a symmetric limit. Clamp lookup input to ±600; lookup axis is 0,50,…,400 and all nine limit values are 1024. Clamp the divided command to ±1024. | output `FFF82F96`; axis `57B2A`, values `57B3C` |
| `73D20` | Apply interpolated gains, persistent blend weights, attenuation, and state gating. Saturate to ±32767. | output `FFF82FEC`; tables around `57B54–57BA0` |
| `7415C` | Clamp that contribution to ±1024, map its magnitude through a nonlinear curve, then restore its sign. | target `FFF82FF6`; clamp `57BAC`; axis `57BAE`, values `57BC0` |

The nonlinear axis is `[0,128,256,384,512,640,768,896,1024]`; its values are `[0,2019,3230,3980,4345,4577,4721,4864,4864]`. The inlined interpolator also has an input bound of 1774, but the preceding ±1024 clamp is tighter for the banks examined.

Within `73D20`, the gain scheduling uses the magnitude of a context input passed from `FFF80016`, bounded at 2176, and table pairs `57B54/57B64` and `57B74/57B84`. Blends use persistent weights at `FFF82F60` and `FFF82F62` with a divisor of 16384. Another attenuation lookup around `57B94/57BA0` uses a magnitude bounded at 320 and divisor 256. The command product includes an arithmetic shift right 8. Additional status gating can zero the contribution. These are code-level scaling terms, not a recovered physical model of each input.

### Feedback and controller

`742C0` receives a signed word from `FFF8029C` through its caller. It invokes filter `300DA` with a bank-selected coefficient (`57BD2` plus bank offset) and 32-bit state `FFF86F60`. The coefficient is 410 in banks 1–3 and 30110 in banks 4–7, a substantial variant-dependent difference:

```
S_new = S + (signed16(input) - (S >> 15)) * signed16(coefficient)
filtered = S_new >> 15
```

These are arithmetic shifts and machine-width integer operations. It clamps the filtered result to ±32765 (`57BD4`) and writes `FFF83002`. Its physical meaning is not established; calling it a confirmed steering-rate signal would overstate the evidence.

Function `7435C` computes error at `74854`:

```
e = target[FFF82FF6] - feedback[FFF83002]
D = clamp(trunc0((e - selected_previous_error) * Kd / 64), -640, 640)
P = clamp(trunc0(e * Kp / 64), -1024, 1024)
C = clamp(trunc0((P + D) * scheduled_factor / 256), -1024, 1024)
output = clamp((C * 4011) >> 10, -32767, 32767)
```

`trunc0` means truncation toward zero. The actual code implements the /64 and /256 with successive signed divisions/shifts and sign corrections; the expressions describe the corresponding arithmetic absent overflow. History is indexed state, so “previous error” here means the selected saved error, not an asserted exact sample interval. This identifies a proportional term and a difference-of-error term; it does not establish a conventional continuous-time PID or physical gains.

| Term | Evidence | Calibration / state |
|---|---|---|
| Difference gain | magnitude schedule from command contribution | axis `57C4C`: 0,128,…,1024; values `57C5E`: 32,32,32,32,32,32,16,16,16 |
| Difference limit | `74950–7497E` | `57BD6` = 640; term stored at `FFF83050` |
| Proportional gain | magnitude schedule | axis `57C70`: 0,55,166,319,532,776,887,942,998; values `57C82`: 1,4,6,8,10,11,11,11,11 |
| Proportional limit | `74A68–74A96` | `57BD8` = 1024; term stored at `FFF83060` |
| Combined limit | `74AF6–74B24` | `57BDA` = 1024; pre-final-scale term at `FFF83074` |
| Final multiplier | signed word `500A6` | 4011, arithmetic right shift 10; output at `FFF83076` |

The gain schedules use the absolute command contribution at `FFF82FEC`. The scheduled combined factor is assembled earlier in the function; not all of its contextual inputs have physical names. Error history is written back in the output-state block at indexed offsets around `+30/+34`.

### Later assist combination and limits

`74C9C`, called at `19E00`, receives a main term from `FFF80198` and a weight from `FFF823F2`. It also reads the accepted command through `1092C`; its magnitude influences gain tables around `57C96/57CA6` and `57CB6/57CC6`. Persistent weights at `FFF82F60/62/64` are updated through `73852`. Its returned combination has a symmetric limit of 8868 from `57C94` (`74DEA–74E10`).

The caller subsequently invokes filter `300F8`, applies a conditional ±388 bound (`19E64–19E82`), a dynamic magnitude cap derived from the 32-bit value at `FFF8541C / 4096`, and later limits involving words at `FFF83488` and `FFF85460` and status flags. Therefore **the controller's ±1024 bound is not established as the final motor-command limit**. This analysis reaches these downstream constraints but does not assign every final actuator-stage state a physical meaning.

## 4. Firmware integrity

### Startup additive checksum

Function `EE10`, called at `EFDE` in startup function `EFB8`, sums unsigned big-endian 16-bit words over `[C000,7FF80)` modulo 65536 and compares against the word at `7FF80`. A mismatch loops back to recompute instead of returning. In this original image:

```
computed = D0CA
stored at 7FF80 = D0CA
```

The covered range includes both CRC trailers discussed below. A future authorized modification inside one of those CRC regions would therefore have an integrity dependency: its CRC trailer contributes to this outer additive checksum. No modification or checksum rewrite is included here.

### Periodic CRC checks

The 256-entry big-endian table at `F05C` exactly matches polynomial `04C11DB7`, non-reflected, left-shifting CRC arithmetic. Function `E226` incrementally processes two regions, 32 bytes per invocation. The stored accumulator is complemented between chunks; a reset stored value of zero corresponds to internal initial state `FFFFFFFF`.

| Data region (end exclusive) | Stored trailer | Raw CRC of data | Trailer value | Raw residue after trailer |
|---|---|---|---|---|
| `[40000,4FF60)` | `4FF7C–4FF7F` | `ECB51A4E` | `134AE5B1` | `C704DD7B` |
| `[60000,6FF60)` | `6FF7C–6FF7F` | `65CFAEDD` | `9A305122` | `C704DD7B` |

The trailer is the big-endian complement of the raw CRC. Bytes between the data endpoint and trailer are skipped by this CRC calculation. Residue checks at `E2F2` and `E3E4` increment a saturating diagnostic counter (up to 32767) on mismatch; they are not the startup checksum's recompute loop. Related single-region routines appear at `E420` and `E4D6`. Generic helper `4E2FC` uses the same table and complement convention, but no additional protected region is inferred merely from its existence.

An apparent reflected-polynomial table around `5698` includes `EDB88320`, but its executable use has not been established. Tail words `7FFF8 = 0000B7C8` and `7FFFC = FFFFA6E0` remain unexplained. The report does not claim exhaustive bootloader, external RWD/container, or flashing-tool integrity coverage. CAN's nibble checksum is separate from firmware integrity.

## 5. Reproduction and remaining uncertainty

Run without third-party dependencies:

```
python3 verify_user_bin.py user.original.bin
```

The script reads only. It requires the exact image hash, verifies the slot record, all 2,049 arctangent entries, all 256 CRC table entries, the additive checksum, both CRC trailers and residues, and emits limits for each of the seven calibration banks. `verification.json` is its saved output. `evidence_disassembly.txt` provides address-labelled supporting instruction windows, including literal annotations. Such windows may contain inline literal pools; instruction decoding alone does not prove reachability. The report's conclusions are based on traced branches/calls and the separately verified data.

What remains unresolved:

- Active calibration variant and actual branch/gating states on a running EPS.
- Physical units and full provenance of every context, feedback, and gain-scheduling input.
- Complete timeout/debounce state-machine semantics and exact error-history sampling interval.
- Exhaustive indirect-alias analysis and final motor/PWM-stage behavior.
- Additional bootloader/container integrity beyond the reproduced checks.

There was no on-vehicle or bench execution, and no modified firmware was produced. The decisive corrections are the proven E4 receive-to-RAM chain, the distinction between raw and accepted command, the arctangent identity of `3A128`, and separately identified command/controller/integrity limits.
