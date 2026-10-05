# Odyssey feedforward: in-image assembly prototype

The controller and independent monitor helpers are now assembled at candidate addresses inside the original 0x80000-byte image. This is an offline prototype, not a selected PTM calibration or validated ECU release. No RWD file was written and v4 is unchanged.

## Placement and trampolines

- Controller helper:0x75800,100bytes; original entry replaced at0x74A98–0x74AA7; resumes0x74AA8.
- Monitor helper:0x75900,104bytes; original entry replaced at0x6B718–0x6B723; resumes0x6B724.
- Both helpers fit inside the FF run0x757F2–0x75FFF. Each requested span is asserted allFF before applying the in-memory patch.
- Entry and return trampolines now preserve r3 using push, PC-relative literal load, indirect jump and a pop in the jump delay slot. The emulator executes the delay-slot semantics. This removes the earlier prototype's intentional r3 clobber.
- Helper arithmetic preserves r0,r1,r4,r5,r6 and MACL except for documented original displaced-instruction effects. PR is unchanged. Maximum extra stack storage remains24bytes: trampoline4-byte saves do not overlap the24-byte arithmetic save set.

A scan of the original payload found no aligned32-bit address values or BRA/BSR encodings targeting0x75800–0x759FF. This is evidence supporting candidacy, NOT proof that the region is unowned. Computed jumps, indirect pointers, erase/program assumptions, omitted boot code and runtime ownership remain outside that scan.

## Verification

The900 integrated controller updates exactly match the preceding out-of-image prototype's complete result JSON, including output, scaled output and monitor flags. Zero gain remains baseline-compatible in these cases; matched8 and matched45 remain flag-free; gain mismatches still generate0x4 after debounce.

The375 boundary cases also pass after relocation. All375 controller sums and750 monitor-helper evaluations match expected results, including both saturation directions and one-count corruption residuals. r3 sentinels now survive both helper return paths, along with the other tested scratch state. Full entry stubs execute in the900 integrated tests; boundary tests enter helpers directly and stop at return destinations.

## Checksum and container trial

A gain8/gain8 in-memory assembly trial was repaired and round-tripped through the actual RWD parser:

- Payload remains0x74000bytes at0xC000; image remains0x80000bytes.
- Code-only patch changes226bytes in the two stubs and two helper spans.
- Runtime CRC0x60000–0x6FF5F changes because the monitor entry lies inside it; repaired stored value at0x6FF7C is0xB24C4DBB.
- The0x40000 block CRC remains valid.
- Application checksum A becomes0x82C6; C becomes0x42E8; downloaded BE16 word sum is zero.
- Container checksum is0x0454EBAF (stored little-endian).
- Encoding then decoding returns identical modified payload bytes; original header is retained.

These values identify only the gain8 serialization trial. No file was emitted, no release gain was selected, and they do not apply to arbitrary PTM settings.

## Remaining verification

Actual ECU memory ownership/execution permissions, interrupt stack margin and timing still need evidence. Current dynamic tests use the restricted schedule/rate/weight conditions documented in prior reports; wider schedules, transitions and combined P/D/filter changes remain to be exercised. A numerical PTM tune cannot be chosen from these instruction tests alone. Physical stability and torque are not verified.

## Artifacts

work/assemble_ff_inimage.py — relocated builder and integrated tests.
work/test_ff_inimage_boundaries.py — saturation/preservation tests.
work/audit_ff_inimage.py — placement scan and in-memory checksum/container trial.
results.json, boundary_results.json, helper_bytes.json, helper_disassembly.txt and placement_and_roundtrip.json — complete evidence.
