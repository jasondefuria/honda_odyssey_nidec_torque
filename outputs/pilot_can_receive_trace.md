# TG7-A060: CAN 0xE4 receive routing

This extends the Pilot modification trace by connecting its command parser to the CAN hardware descriptor and validation path. Analysis remains read-only.

## Table-base evidence

A ROM table base of `tp = 0x12000` consistently aligns the independently observed descriptor, validation-policy, parser-callback, and driver-callback accesses with valid data in the decoded image. The tp initialization itself has not been captured. Absolute ROM addresses below use that supported base interpretation; RAM remains expressed relative to gp.

## Hardware configuration to parser

The 12-byte descriptor at `0x10140` is slot 10 of the array at `0x100C8`:

`04000000 e4000000 00010100`

Its CAN identifier is `0xE4`; byte +10 gives logical receive index 1. Configuration function `0x4704E` walks the descriptor array, tests its enable mask, loads its ID, type and length fields, and passes them with the slot number to driver routine `0x4206C`.

The receive driver reads an identifier from hardware, masks it to either 11 or 29 bits, reads the length and eight payload bytes into a stack record, and checks hardware status before dispatch. The relevant window ends at `0x42368`; hardware accesses include the `0xFF489000` region. Callback load `0x42358` reads `tp-0x1DA8`, corresponding to ROM `0x10258`, containing `0x40FE4`.

`0x40FE4` uses the channel/slot arguments to index the same descriptor array. For channel zero, slot 10, it obtains logical index 1. It calls validator `0x40EAA`, copies payload bytes into a contiguous scratch buffer, and invokes `0x41530` with the logical index, validation status, and payload pointer.

Initialization at `0x412D2` builds a logical-index-to-callback-entry map at `gp-0x7E94`. Dispatcher `0x41530` uses that map to index eight-byte records at `tp+0x81C`. Logical index 1 selects the record at `0x12824`:

`01 00 01 00 34 05 04 00`

The enabled record's callback is `0x40534`. The dispatcher passes validation status in r6 and payload pointer in r7.

This descriptor/configuration/driver/dispatch chain supplies evidence beyond a coincidental payload-layout match. Slot enablement and active hardware state still depend on runtime configuration.

## Validation before command update

The four-byte policy entry for logical receive index 1 is at `0x10074`: `03 03 00 0A`. The first byte enables the checksum and repeated-counter checks used by `0x40EAA`.

Initialization at `0x40B50` onward derives the checksum seed from the descriptor identifier:

`8 + (ID & 15) + ((ID >> 4) & 15) + ((ID >> 8) & 7)`.

For `0xE4`, the seed is 26. Validation adds each received payload byte and its high nibble; taking the low four bits is equivalent to adding every nibble. It accepts the checksum when the low four bits of the total are zero. For a five-byte frame this is the familiar:

`(26 + sum(all ten payload nibbles)) & 15 == 0`.

The counter comparison uses bits 5:4 of the last received payload byte. A repeated counter sets per-message state at `gp-0x7F50 + index`; a checksum failure sets state at `gp-0x7F68 + index`. Successful validation returns zero, while the failure paths leave a nonzero result. The parser below only updates when that result is zero.

The validator uses the supplied length. This pass does not establish a separate minimum-DLC-five requirement in the Pilot driver or dispatcher; it must not be inferred merely because the parser accesses byte four. Nor does this trace yet establish how every validation flag affects later fault reporting or shutdown.

## Accepted payload into the modified control path

Parser `0x40534` tests its status argument, then constructs:

`raw = (payload[0] << 8) | payload[1]`.

It stores raw at `gp-0x7FB6`. It also stores `payload[2] | ((payload[4] & 0x40) >> 1)` at `gp-0x7F9F`.

The publication code at `0x408AA`–`0x408BC` copies raw to `gp-0x7AA8`. Getter `0x41A8A` reads it as a signed halfword. The already traced function `0x37568` consumes that getter, applies bank-dependent scaling and a signed offset, and clamps its intermediate result before the nonlinear target path.

Combined with the previous report, the supported chain is:

```text
configured CAN E4 slot 10
  -> driver callback 0x40FE4
  -> validation 0x40EAA
  -> logical receive index 1 / dispatcher 0x41530
  -> parser 0x40534
  -> gp-0x7FB6 -> gp-0x7AA8 -> getter 0x41A8A
  -> preprocessing 0x37568
  -> conditional target/controller pipeline
  -> 256-entry target reader 0x363DE
  -> bounded correction -> main-request combination
  -> later +/-2457 clamp and mode-dependent processing
```

This closes the earlier missing Pilot callback-to-CAN-ID connection, subject to the explicitly stated table-base and runtime-configuration limits. It does not prove physical torque units or a twofold hardware output.

## Motor-output follow-up

The limited request is published at `gp-0x4AA8` and exposed by getter `0x333F4`. Additional readers at `0x4B5C6` and `0x4EB8C` use its magnitude in status/monitor logic. Those readers are not, by themselves, proof of motor actuation. The final motor-controller and hardware-output path still needs separation from these monitoring consumers. No final-output mapping is claimed here.

[Verification](pilot_can_verification.json) · [Disassembly](pilot_can_disassembly.txt) · [Modified-region trace](pilot_modification_trace.md)
