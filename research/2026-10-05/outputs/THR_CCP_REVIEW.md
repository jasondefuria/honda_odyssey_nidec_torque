# THR-A020 CCP archive review and offline validation

The supplied ZIP contains a Python CAN dumper and a README, not an ECU memory capture. Its instructions were reviewed as document content; the dumper was not executed, and no CAN messages were sent.

## Independently checked

Stock, R1, and R2 have identical bytes in the CAN descriptor table (0x3DA90–0x3DE8F), pointer table (0x5FC00–0x5FDB3), and address lookup routine (0x37844–0x3787D).

Descriptor entry 1 at 0x3DAA0 contains `00000000072100000000000008010000`; entry 33 at 0x3DCA0 contains `00000000072200000000000008020000`. The two-byte big-endian ID field at +4 gives 0x721/0x722; length is 8 and direction is 1/2.

The pointer table has 109 entries, beginning FFF819C0, FFF819C2 and ending FFF83830.

The SH-2A research interpreter executed the actual lookup routine without hooks for 898 cases per image, 2,694 total, with zero mismatches. Cases cover every byte address in the pointer table, selected range boundaries, and both states of bit 0 at FFF8429D.

- Addresses in [0x5FC00, 0x5FDB4) are rounded down to a four-byte boundary, then dereferenced. This includes unaligned requests; they resolve to the same variable pointer, not variable pointer plus the unaligned offset.
- Addresses in [0x10000, 0x40000) resolve to `0x50000 | (address & 0xFFFF)` when the flag is clear; they remain unchanged when it is set.
- Low addresses including 0 and 0x1FFF remain unchanged in both flag states.

This confirms address resolution only. It does not establish that a complete live CCP request can read the boot region, nor supply missing boot bytes. CONNECT station handling, upload authorization, command framing, transport, and full handler execution were not independently emulated in this review. The user's additional command-handler findings remain supplied evidence.

## Supplied dumper issues

1. Default CRO candidates are 0x727 and 0x646, omitting THR's 0x721. Default stations are 0 and 0x1117, omitting the supplied THR-specific 0x20F3 (wildcard 0 is present). The script exposes overrides, but its defaults do not establish THR compatibility.
2. A sequential dump is an address-mapped CCP view, not necessarily a raw flash image. With the mapping flag clear, 0x10000–0x3FFFF aliases another region; pointer-table addresses resolve to RAM. Five-byte requests crossing a mapping boundary need special handling. Such output must not be treated as a flashable ROM.
3. SET_MTA+UPLOAD fallback retries UPLOAD inside xfer without reissuing SET_MTA. If the ECU advances MTA and its reply is lost, a retry can return later bytes that get written at the original file offset. SHORT_UP avoids this particular state drift if supported.
4. Reply matching accepts any receive bus and only checks a minimum three-byte reply header. Error replies are ignored rather than surfaced. Discovery is not proof of ECU identity.
5. Resume uses existing file length alone, without binding it to ECU identity, start address, mapping state, or prior contents. Repeated successful reconnects with failed reads can loop indefinitely.
6. The mode named --sniff actively sends CONNECT requests after a passive phase. Initialization selects ALLOUTPUT. Constructor failure can occur before the caller's cleanup finally block, so the README's unconditional restoration claim is too strong.

No source changes or vehicle actions were made. A bounded, identity-checked low-region capture could provide missing evidence, but this archive alone does not close the decrypt/check-routine question or strengthen physical 2.5x torque validation.

Evidence: [lookup test results](THR_CCP_lookup_validation.json). Stock/R1/R2 hashes are recorded there.
