# Odyssey THR-A020: extended original-ROM analysis

This report extends the prior CAN, controller, monitor and integrity traces. It analyzes the original 524,288-byte SH-2A image, SHA-256 `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`. The original is preserved. No modified image or flash operation was produced.

## Findings that change the modification assessment

The genuine CAN `0xE4` receive path remains established: slot 22 → `0x14618` → raw word `FFF85198` → acceptance logic at `0x1113E` → accepted command `FFF8500C`. `0x3DA90` and `0x3DBF0` are supported by the initialization and receive code, not inferred from another vehicle. The command conversion does not use `0x3A128`: that table belongs to the separately traced sensor-angle calculation.

The requested “2.5× torque” cannot be equated to a 2.5× curve endpoint. This image has several stages with independent limits, an independently calculated monitor, CAN-assist blend states, and actuator control. Physical torque units and the complete programming acceptance requirements remain unresolved.

New original-code execution confirms two different curve families and a direct fault path that removes the tested CAN-controller contribution. It also confirms an additional reflected CRC primitive and a wrapper that checks a selected-range CRC. These results strengthen the trace; they do not validate a torque-increase patch.

## Offline execution method and limits

The test harness translates original instructions with Ghidra SLEIGH through `pypcode 4.0.0`, language `SuperH:BE:32:SH-2A`, and interprets the resulting p-code. It models integer operations, branches, calls, delay slots and explicitly allocated RAM. ROM writes and unsupported operations fail. This is an independently implemented execution model, not a real ECU, a certified emulator or a vehicle simulation. It does not model interrupts, scheduling, timing, electrical interfaces, mechanical loads or all startup conditions.

The curve and monitor tests execute the original slope initializer and original routines. CAN tests replace the hardware receive call with an explicit slot-22 payload provider and execute bounded parser/acceptance segments. Fault scenarios initialize original calibration RAM, then apply stated synthetic state and input values. CRC tests use either the original no-op callback or a modeled successful memory-read callback. Individual JSON files record the exact scopes.

## Exhaustive CAN parser and acceptance checks

**2,097,152 cases passed**: every 16-bit raw word × both request-bit values × four counter values × four validity conditions (good, repeated counter, bad checksum, both). Original parser segment `14618..146CA` and acceptance segment `1113E..111E0` were executed; the hardware receive callback supplied an eight-byte slot-22 payload.

The raw word, request bit and counter reached the expected receive RAM. The repeated-counter flag mask was `4042`; the deliberately invalid-checksum mask was `2021`; simultaneous faults produced their union. In these test conditions good data replaced the accepted word and request bit, while invalid data retained the prior accepted word and cleared the accepted request bit.

The earlier status postprocessing at `153C4`, timeout debounce, actual mailbox hardware, and surrounding scheduler were outside this bounded experiment. “Exhaustive” applies to the dimensions above, not all CAN payloads, health states, counter histories or real-time behavior. The test sets a previous different counter for the good condition and an equal counter for the repeated condition. Other unused payload bits are held fixed.

An additional 4,096 parser cases covered every old/new counter pair, all checksum-nibble values, both request values and eight representative raw words, with nonzero remaining payload bits. Only an equal old/new counter set the repeated-counter mask: this helper does not require a strict +1 sequence. That observation remains bounded to the parser segment. Evidence: `odyssey_can_counter_transition_execution.json`.

Evidence: `odyssey_can_execution_verification.json`. Together, CAN, main-curve and monitor sweeps cover **3,014,656 cases**; the directed fault, CRC and coding cases are additional.

## Main curve and independent monitor

Both `0x7415C` and the monitor `0x6ACC4` were exercised across every signed 16-bit input in every bank: **458,752 cases per routine**, all passing the corrected fixed-point oracle. The main routine's eight-byte mirror also matched. Monitor mismatch counters and flags stayed clear when provided matching snapshots.

| Banks | Axis at `57BAE + bank_offset` | Curve at `57BC0 + bank_offset` | Initial magnitude limit | Maximum resulting magnitude |
|---|---|---|---:|---:|
| 1–3 | 0,128,256,384,512,640,768,896,1024 | 0,2019,3230,3980,4345,4577,4721,4864,4864 | 1024 | 4864 |
| 4–7 | 0,222,443,665,887,1109,1330,1552,1774 | 0,1715,2842,3277,3738,4173,4506,4570,4570 | 1024 | 4006 |

Here `bank_offset = (bank_number - 1) × 0x300`. The high-end knots in banks 4–7 are unreachable after this routine's initial 1024 clamp. Calling the final table value 4570 the usable maximum would therefore be incorrect.

Interpolation is fixed-point, with separately truncated products. For a positive segment width `dx`, signed ordinate difference `dy`, and distance `d` into that segment:

```
s = sign(dy) * min(abs(dy), 31*dx) * floor(2^26 / dx)
step = floor((abs(s) >> 16) * d / 1024)
     + floor((abs(s) & 65535) * d / 2^26)
magnitude = y_start + sign(s) * step
```

The input sign is restored afterward. A naive exact-rational interpolation oracle initially disagreed at bank 4, input -1010: original execution gives -3978, while ideal linear interpolation gives -3979. Resolving that discrepancy exposed the split-product truncation. Each of banks 4–7 differs from ideal interpolation at 130 signed inputs, by at most one count. Banks 1–3 have power-of-two segment widths and matched the ideal oracle in the exhaustive pass.

Evidence: `odyssey_curve_execution_verification.json`, `odyssey_monitor_execution_verification.json`.

## Direct monitor-fault effect on CAN assist

The earlier fault report established selector `EF`, original flag word `FFF89362` bit 15, and its conditionally published processed counterpart at `FFF89378`. A more direct downstream path is now identified:

1. `0x7541E` includes the complete processed word at offset 18 in its predicate and writes the Boolean result to `FFF830EC`. `0x7276A` calls this before the CAN-assist calculations.
2. With the feature enabled, status routine `0x754B0` assigns status 7 on this fault path. A disabled feature takes an earlier status-6 path.
3. Dispatcher `0x72A44` uses the fault flag to leave active states. The paths through `0x72DA4`/`0x7356C` select state 5; the paths through `0x72F54`/`0x73554` select state 4. Activation paths also test that this fault flag is clear.
4. Blend updater `0x73852` drives weights `FFF82F60` and `FFF82F64` to their minimum in state 5. State 4 subtracts the step at `FFF82F74`. In the tested original calibrations that step spans the entire 0–16384 weight range in one update.
5. Combiner `0x74C9C` multiplies the controller correction `FFF83074` by weight `FFF82F64`, effectively dividing the product by 16384 with the original truncation sequence. A zero weight removes this contribution; baseline and other terms still exist.

Directed tests used all seven banks, starting states 1–5, full initial CAN blend weights, a zero-filled command structure and the stated dispatcher arguments. After the first tested blend update the weights were `[0,16384,0]` in all 35 scenarios. This is evidence of CAN-assist disengagement under those inputs, **not evidence that all power steering assistance vanishes**, and not an exhaustive state-machine proof.

The original-to-processed flag publication gate described in the preceding report still matters. A separate execution test now covers all 256 values of `FFF861ED` with only the original EF flag injected: bits 6 and 7 both clear publishes `8000` to `FFF89378` and sets the CAN fault; either bit set publishes zero and leaves this predicate clear. This tests the original publication segment and predicate, but not all diagnostic RAM states or timing. A direct setter for gate bit 6 remains unidentified; the confirmed direct references besides initialization write bits 2, 3 or 7.

A further 448 directed monitor tests flipped each of the 16 bits in each of four snapshot words, across all seven banks, at raw input 400. Three bad snapshots followed by two correct snapshots produced the expected `86 → 172 → 255` affected counters, with flags set on the third bad snapshot. The first correct snapshot reset the counters to zero; flags remained set through both correct snapshots. This routine therefore does not itself clear those latched flags. Evidence: `odyssey_fault_publication_execution.json` and `odyssey_monitor_fault_injection.json`.

Evidence: `odyssey_fault_state_execution.json` and the earlier `odyssey_fault_effect_trace.md`.

## Variant-mode correction

The previous trace through `0x77260` and state `FFF83488` must be interpreted conditionally. At `0x765DE`, mode 0/1 uses one dispatcher, mode 2 another, and other modes—including 3—take `0x76648`, which assigns several state flags unconditionally. Those assignments alone cannot establish a fault-specific effect for a mode-3 configuration. The direct CAN-assist path above avoids relying on that inference.

The variant loader `0x2F95A` uses a 14-record table at `0x5EB00`, with 70 bytes per record. It matches the first five coding bytes through `0x2F8FC`, validates the bank byte, then copies the chosen record into RAM. The table contains mode 1 and mode 3 records, but no mode 2 record. Examples are `THRA0` → mode 3/bank 1; `THRA1` and `THRA2` → mode 3/bank 2; `THRA3` → mode 1/bank 2; `THRA4` → mode 1/bank 3. Default records use mode 3/bank 1.

The coding input comes through RAM `FFF83F1C`, with marker, duplicate and complement checks in the caller at `0x17704`; a ROM default is used on one invalid-marker path. The actual vehicle coding is not established by this dump. A part-number label alone is insufficient to identify the live bank/mode.

The full original loader was also executed for every unique table ID and two unmatched IDs. It sets CAN-assist enable byte `FFF86E83` from record byte 11. `THRA0`, `THRA1`, `THRX0` and the default set it to 0; `THRC0`, `THRA2`, `THRA3`, `THRA4`, and `THRY0` set it to 1. For example, `THRA0` and `THRC0` share bank 1/mode 3 but differ in this enable flag. All these records contain the same `39990-THR-A020` firmware identification string. Auxiliary calibration RAM was zero in these directed loader tests; live coding and overrides remain unproven. Evidence: `odyssey_variant_loader_execution.json`.

A separate full `0x17704` execution used a valid synthetic `THRC0` coding record, then each of its 192 individual bit flips. Any single-bit change in the first 19 checked bytes fell back to the default ID and cleared the CAN-assist enable flag; changes in the final five bytes did not affect selection in this routine. A marker failure also replaced the coding RAM with the ROM default and set `FFF85349`. The routine returned 1 for both a valid record and an invalid-marker case, so its return value alone is not a validity test. These are offline RAM experiments, not EEPROM modifications. Evidence: `odyssey_coding_record_execution.json`.

## Additional reflected CRC and range wrapper

The table at `0x5698` is **16 big-endian 32-bit entries**, generated by four reflected rounds per entry using polynomial `0xEDB88320`. Reader `0x4E20` processes each byte in two nibble steps. Wrapper `0x4E86` initializes to `FFFFFFFF`, updates, and complements the result according to its operation byte. Original-code tests matched `zlib.crc32` on an empty input, `123456789` (`CBF43926`), bytes 0–255 (`29058C73`), and a deterministic 4096-byte sample.

Higher wrapper `0x4FE8` maintains two CRC contexts. Under the tested sorted, non-overlapping descriptors, one covers the whole requested range and is written to input-structure offset 20. The other covers the concatenation of selected ranges and is compared to the four big-endian bytes pointed to by offset 16. The wrapper returns 2 on mismatch and 0 on a matching value in these tests. Reads are chunked to at most 64 bytes.

The tested structure is:

| Offset | Observed use |
|---:|---|
| 0 | First byte is selected-range count; remaining bytes not used as count |
| 4 | Pointer to 12-byte selected-range descriptors |
| 8 | Whole-range start address |
| 12 | Whole-range length |
| 16 | Pointer to expected selected-range CRC, four big-endian bytes |
| 20 | Output whole-range CRC value |
| 24 | Callback invoked during processing |
| 28 | Read callback: source, destination, requested length; returned length feeds CRC |

Each selected-range descriptor supplies its start at +4 and length at +8. The test used a count of zero, one interior range, two separated ranges, and the complete range, with matching and deliberately mismatching expected CRCs: eight passing cases. These tests cover successful full reads; short reads, callback errors and malformed descriptor behavior are not comprehensively characterized.

ROM descriptor `0x52B4` contains start `0xC000`, length `0x74000`, and callback pointer `0x4FE8`. Low diagnostic code references this descriptor. However, several helpers needed to connect programming requests to complete acceptance—including targets below `0x2000`—contain only `FF` bytes in the supplied image. The source and exact interpretation of the live expected CRC and selected-range list remain unresolved.

A further execution ran `0x4FE8` across the complete `[C000,80000)` original-ROM range: 475,136 bytes in 7,424 full reads, resulting in `BD19F157`, matching zlib. The selected-range descriptor and expected CRC were synthetic; this verifies full-range arithmetic and chunking, not the actual programming request. Evidence: `odyssey_crc_rom_range_execution.json`.

This reflected CRC is separate from the already verified startup big-endian 16-bit sum over `[C000,7FF80)` and the periodic non-reflected CRCs over the two previously documented ranges. The tail fields at `0x7FFF8` and `0x7FFFC` are still unexplained. A bounded search over common byte/word/dword sums and CRC32 ranges did not establish their meaning; that is not proof that they are unused.

Evidence: `odyssey_reflected_crc_verification.json`, `odyssey_crc_range_execution.json`.

## Remaining gaps before any torque-increase claim

- Actual coding and active bank/mode on the target EPS.
- Physical units and measured relationship between accepted command, internal target, current regulation and rack torque.
- Complete runtime behavior of the health gates, monitor publication and state transitions under real operating conditions.
- Complete programming integrity/acceptance path, including unresolved tail metadata and absent low-address code.
- Validation of the combined controller, limits and hardware response; matching a reference vehicle's nominal gain does not supply this evidence.

The Pilot comparison remains useful architectural evidence, but its V850 implementation and offsets are not substituted for this SH-2A image. The Civic curve endpoint increase likewise does not establish a uniform 2.5× output or an Odyssey modification recipe.

## Reproducibility and evidence

The companion `offline_validation/` folder contains the execution harness, fixed-point oracle and test sources, with an exact-image hash guard and separate rerun result paths. `odyssey_extended_disassembly.txt` contains focused original-ROM instruction listings. Literal pools may appear as apparent instructions in disassembly; the prose and execution tests identify the relevant paths. `odyssey_extended_manifest.json` records hashes of the new evidence files.
