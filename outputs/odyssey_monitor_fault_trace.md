# Odyssey THR-A020: curve monitor into fault reporting

This continues the original Odyssey modification analysis. The Pilot motor-side consumer remains unresolved; this pass instead closes a concrete part of the Odyssey monitor-to-fault path using the preserved SH-2A image.

## Mismatch flags reach the aggregate fault callback

The earlier trace established three mismatch flags in bits 0–2 of byte `0xFFF8A5DB`, set by `0x6ACC4` after their counters reach threshold. In big-endian memory these are the low three bits of the word at `0xFFF8A5DA`.

Function `0x4D358` loads aggregate base `0xFFF8A5CC`. At `0x4D38C` it loads word base +14, which is exactly `0xFFF8A5DA`; at `0x4D38E` it masks with 7 and ORs the result into an aggregate containing other monitor flags. If the aggregate is nonzero, it writes callback state **2** to the byte pointed to by r6 (`0x4D3AE`–`0x4D3B0`). On an all-zero aggregate this function returns without writing that byte. This distinction matters: it is not an automatic clear operation.

## Descriptor and generic fault engine

The 16-byte record at `0x6FC00` contains:

| Field | Value |
|---|---|
| +0 | null |
| +4, evaluation callback | `0x4D358` |
| +8, response callback | `0x4BCDA` |
| +12, packed fault selector | `0xEF` |
| +13..15 | zero |

The surrounding callback array begins at `0x6F250`; this record is zero-based index 155. Its count at `0x6FC20` is 157. The generic loop at `0x4B310` onward forms a 16-byte ROM-record address and an eight-byte runtime-record address per index.

At `0x4B342`–`0x4B358`, it invokes the evaluation callback with the destination pointer at runtime record +4. At `0x4B35A`–`0x4B36E`, it invokes the response callback with current state, previous state, and runtime record +6. Response callback `0x4BCDA` writes **0x80** to that latter byte when current state equals 2.

The generic engine tests state 2, decodes selector 0xEF as group E / bit 15, and sets **bit 15 of the word at `0xFFF89362`**. The group-E store is at `0x4B46A`–`0x4B472`, using aggregate base `0xFFF89350` +18. This word update is distinct from the original three fine-grained mismatch bits.

The engine then writes the selector and an associated record byte to `0xFFF88B42`/`0xFFF88B43` and calls `0x2D41C` at `0x4B488`. The callee begins gathering multiple state blocks under status-bit gates. That supports describing it as an event/state-capture path; the entire persistence format and any external diagnostic-code encoding have not been established here.

`0xEF` is a packed internal selector. It must not be presented as a standardized OBD diagnostic trouble code without the diagnostic translation layer.

## Supported causal chain

```text
main and independently recomputed curve disagree
  -> debounced mismatch flags at 0xFFF8A5DB
  -> aggregate callback 0x4D358 writes state 2
  -> response callback 0x4BCDA writes runtime status 0x80
  -> generic engine sets 0xFFF89362 bit 15
  -> event/state-capture call 0x2D41C
```

All of the arrows above have identified instructions. This is stronger than merely observing a duplicate calibration table: a main-only curve change can propagate into the central fault machinery when it creates a sustained evaluated mismatch.

The precise resulting assist-disable, derating, reset, or latching behavior remains to be traced. The aggregate also includes other monitors, so this fault selector is not uniquely attributable to the nonlinear curve. This pass does not justify bypassing the monitor or predict the exact vehicle response.

## Modification consequence

Any proposed Odyssey calibration change needs to remain consistent with independent recomputation and the downstream controller/limits. Correct additive and CRC checksums alone do not prevent this runtime fault path. No modified firmware or bypass was produced; the original image remains unchanged.

[Verification](odyssey_monitor_fault_verification.json) · [Disassembly](odyssey_monitor_fault_disassembly.txt)
