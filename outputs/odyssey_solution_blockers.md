# Odyssey: missing coding source and boot-marker discrepancy

The original remains unchanged: SHA-256 `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`. This follow-up resolves two previously vague integrity/configuration questions. It does **not** establish a flashable 2.5× torque modification.

## The live coding resides outside this image

The 28-byte descriptor at `0x39450` contains:

| Field | Value |
|---|---|
| Record identifier | `02` |
| Primary RAM | `FFF83F1C` |
| Shadow RAM | `FFF83F34` |
| Storage address | `80106800` |
| Length | `0018` = 24 bytes |
| Completion callback | `000169B6` |

The initialization manager at `0x155AA–0x155B4` passes the shadow destination, storage address and length to `0x31624`. That routine finds the address in row 9 of the storage-region table at `0x3D9D8`. The row covers offsets `6800–6FFF`, with a single slot; this record does not use the multi-slot offset adjustment used by other rows.

In the successful-read path, `0x3177E–0x31786` configures the transfer registers with source `80106800`, destination `FFF83F34`, count 24 and control `01010100`. Original-code execution with explicitly modeled status registers confirmed these writes. This was an offline IO dictionary: no actual transfer, flash command or vehicle interaction occurred.

After the read routine reports completion, `0x155C4–0x155E8` copies the shadow bytes to primary RAM. The manager invokes callback `0x169B6`, which selects the previously tested `0x17704` coding validator/loader. Consequently, searching the code-ROM dump for one particular valid coding record cannot establish the live coding.

The required address range is **`80106800–80106817`**, inclusive. It is outside the supplied `user.bin`, whose analyzed address range is `00000000–0007FFFF`. A captured live RAM record at `FFF83F1C–FFF83F33` could also show the loader input, but may already have been replaced by a default following a marker failure. The storage record is therefore the clearer source evidence. This report provides address interpretation, not a procedure for changing or acquiring ECU memory.

Evidence: [transfer execution](odyssey_nvm_coding_transfer.json), [focused disassembly](odyssey_solution_blocker_disassembly.txt).

## A boot-side marker check was previously missed

The image contains a vector value `00008804` at `0x8000`. Code beginning at that target includes:

```
8814: r5 = 0x7FFF8
8818: r4 = 0xC000
881C: r13 = unsigned_word_at(r4)
8820: r14 = unsigned_word_at(r5)
... hardware initialization helper ...
8828: r13 += r14
... further initialization / flash-request check ...
8836: compare r13 with 0xFFFF
883C: mismatch routes to 0x8898
```

Both Capstone disassembly and SLEIGH translation identify **16-bit unsigned loads**, at precisely the addresses shown. The actual bytes are:

| Address | Contents / interpretation |
|---|---|
| `C000` | `4837` |
| `7FFF8` | `0000` — the word actually read by this check |
| `7FFFA` | `B7C8` — complements `4837`, but is two bytes later |
| `7FFFC` | `FFFFA6E0` — meaning still unresolved |

Thus this comparison sees `4837 + 0000`, not `FFFF`. A bounded execution of the original branch segment, with hardware initialization replaced by register-preserving returns and the flash-request result supplied as either 0 or 1, selected `0x8898` in both cases. The relevant initialization helpers save/restore the involved callee-saved registers or do not alter them.

The successful continuation later obtains the application's entry from the vector at `0x10000`; the alternative route calls boot-support routines and reaches sleep. This is evidence of a **conditional boot-path discrepancy in the supplied image**, not proof of how the physical ECU currently boots. Bytes below `0x2000` are `FF` in this file, so its lower boot routing cannot be reconstructed. The file's acquisition/reconstruction history also is not established here. Do not “repair” the two-byte discrepancy by assumption or treat the nearby complement as proof of a safe patch location.

This finding supersedes the earlier blanket statement that the tail has no established reader: the first 16-bit word at `7FFF8` now has a reader. The purpose of `FFFFA6E0` and the complete programming acceptance path remain unresolved. The known startup sum and periodic CRCs still match; passing those checks alone is insufficient.

Evidence: [boot-marker execution](odyssey_boot_marker_execution.json).

## Read-only coding decoder

[inspect_odyssey_coding.py](inspect_odyssey_coding.py) accepts an already acquired record or memory dump and reports the selected table record, mode, bank and coding-derived CAN-assist enable flag. It makes no connection to an ECU and performs no firmware or coding writes. It checks the exact original ROM hash.

For an existing 24-byte record:

```
python3 inspect_odyssey_coding.py coding-record.bin
```

For an existing larger dump, explicitly supply the memory address represented by its first byte:

```
python3 inspect_odyssey_coding.py memory-dump.bin --base 0x80100000
```

Keep the decoder alongside `user.original.bin`, or supply its path with `--rom`. Output is JSON on stdout. Its decoded coding/enable results matched all 193 original-code record tests. A decoded table bank still does not establish runtime overrides or physical torque.

## Why the torque solution is not yet determined

Two different storage records can select different CAN-assist behavior while using this identical `user.bin`. Physical motor/rack torque also is not measured by this ROM file. Finally, the boot-marker discrepancy and missing boot region prevent treating a mathematically corrected checksum as a complete acceptance test.

The remaining evidence is specific:

- The target unit's coding record, plus runtime override state if present.
- A complete, trustworthy boot/programming image or equivalent evidence that explains the entry routing and tail format.
- Bench measurements linking commands, current/torque and controller limits on this EPS; offline arithmetic tests cannot establish a safe physical 2.5× result.

No candidate modified firmware has been emitted. The CAN path, scaling routines, monitor behavior and integrity primitives already identified remain useful, but none supplies those missing observations.
