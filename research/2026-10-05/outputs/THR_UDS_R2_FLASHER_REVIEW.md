# THR captured update path versus nrdr flasher and R2

Offline review of freshly downloaded `flash.py` and `eps-update.py` from the nrdr-clean branch, obtained 2026-09-26. Source hashes are in THR_UDS_flasher_crosscheck.json. Neither program was run. No SSH, CAN, security unlock or programming operation was performed.

## Evidence and outcome

The CCP capture's resident region 0x2000–0xBFFF matches the original analysis image exactly. The captured 0x0000–0x1FFF prefix supplies the previously missing boot routines. Analysis combines these with the existing R2 application, not the aliased CCP view as a raw ROM.

| Flasher behavior / assumption | THR / R2 evidence | Assessment |
|---|---|---|
| Uses the RWD identity and security-secret headers | R2 identity is THR-A020; header secret 011101121120 equals bytes at 0x51E4 | Static constants agree; full SecurityAccess exchange not emulated |
| Derives UDS target from header byte 30 | Produces 0x18DA30F1 | Header computation agrees; no live UDS routing verification. CCP 721/722 is a separate endpoint |
| Writes the RWD's three-byte decryption key | Key 010203; resident F101 code copies three request bytes to FFF80C51 and conditionally enables decrypt | Static handoff agrees; session/state gates remain relevant |
| Transfers encrypted payload bytes | TransferData path references 0x14CE at literal 0x34CC; captured full decrypt tested for all 256 byte values | Cipher agrees exactly with R2 encoder/decoder |
| Uses RWD download start/length | C000/74000 exactly matches resident table at 0x52B4 | Geometry agrees. Range helper alone tests overlap, not containment |
| Requests final programming-dependency check | Resident FF01 path invokes boot validation; direct 0x11C2 execution on a populated flag-2 record succeeds for R2 | Scoped execution pass, not complete UDS-handler/session emulation |
| Firmware checksum preflight | Fetched updater has only 6C000/4C000 SH-2A lengths; R2 is 74000 | **Gap: warns and returns without checking R2 firmware sums** |
| Guided image selection | Fixed curated list contains no THR-A020 R2 | R2 is not a supported guided-menu choice |

## Execution evidence rechecked

Full 20-million-block-limit runs were repeated sequentially and saved. R2 checksum routine 0x1306 returns 0 after 12,895,770 translated blocks; FF01 routine 0x11C2 returns 0 after 12,896,047. Full decrypt 0x14CE returns 0 with all 256 outputs matching the established mapping. Prior negative execution flips a bit at C010 and receives return 1 / NRC 72 from 0x11C2; pending record flag 1 gives NRC 22.

An earlier short trial had overwritten the saved positive JSON with instruction-limit results. That artifact is now corrected by a completed rerun. The instruction limit was a test budget issue, not an ECU rejection.

## Workflow limitations discovered in source

`flash.py` is a UI/orchestration wrapper; `eps-update.py` performs the protocol operations. Its dry-run boundary occurs after session changes and security exchange, including entry into programming session. It does not erase/program, but it is not passive.

The updater delegates CAN framing, request encodings, timeouts and response parsing to installed opendbc/Panda dependencies. Those exact installed versions and the vendored RWD parser were not validated here. A live bus found by CCP does not prove the UDS updater's target routing.

The source sends encrypted blocks using the ECU-advertised maximum block size minus two bytes. We have not executed its full block-counter/duplicate-block/retry behavior against THR's UDS dispatcher. Its erase/program/reset operations and power-loss recovery have not been exercised.

The updater has a mock-client fallback after connection exceptions, with a guard against real-flash mode using that mock. Consequently a tool-only workflow result must not be substituted for actual ECU evidence.

## Conclusion

R2's identity constants, cipher and payload range are consistent with the traced THR update components, and the captured boot checksum path accepts its bytes under synthetic state. The downloaded generic flasher does not provide complete R2 preflight coverage, and this review does not validate the entire live update state machine, erase/program hardware or recovery. It is not flash approval and does not establish physical torque or runtime steering behavior.

Sources: https://github.com/nrdr/openpilot/blob/nrdr-clean/openpilot/nrdr/tools/eps/flash.py and https://github.com/nrdr/openpilot/blob/nrdr-clean/openpilot/nrdr/tools/eps/eps-update.py .

Artifacts: THR_UDS_flasher_crosscheck.json, THR_UDS_resident_disassembly.txt, THR_boot_execution.json, THR_boot_negative_execution.json.
