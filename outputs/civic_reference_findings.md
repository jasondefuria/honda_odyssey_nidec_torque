# Civic reference comparison for Odyssey THR-A020 research

Repository: https://github.com/nrdr/openpilot/tree/b3366b5b56512805be8f0bf832b4981bfd958072

The complete recursive branch tree was inspected (not truncated). It contains Civic stock/modified pairs and an explicit TBA-C020 `2.5x-mod` file. No THR-A020 firmware artifact was found. The repository distinguishes legacy modifications from Proper Torque Mod (PTM/PTC).

## Provenance

The user-supplied `/Users/jasondefuria/Downloads/39990-TBA,A030-PTM.rwd` was readable. Its SHA-256 is `3694903e9ffa242097b4f649c61acf6df77d4b76c4f5d97f67194613731e8520`, identical to the repository PTM copy.

Access to the supplied Downloads subfolder was blocked and the requested read permission was not granted. The stock, legacy mod, and linear-max A030 files analyzed are therefore repository copies with the corresponding names, not verified copies of those three local attachments. All analyzed RWD hashes match the repository SHA256SUMS catalog. Exact filenames and hashes are in `civic_reference_comparison.json`.

No repository executable or flashing tool was run. The decoder's literal byte-substitution dictionary was extracted using Python AST literal evaluation and used by a separate read-only parser. All files are x5A containers with flash start 0x4000 and decoded length 0x4C000. Their outer little-endian byte-sum checksum, decoded BE16 sum at ROM 0x4FF80, and decoded BE16 negative sum at ROM 0x4FFFE pass. These checks validate the inspected format/data, not hardware compatibility.

## Byte-level findings

Addresses below are **Civic ROM addresses**, not Odyssey addresses. They are the container's flash start plus decoded payload offset.

| A030 variant versus stock | Changed decoded bytes | Principal differences |
|---|---:|---|
| Legacy `mod-39990-TBA,A030.rwd` | 74 | Selected repeated table entries, one scalar, firmware-identification punctuation, two checksum words |
| `39990-TBA,A030-linear-max.rwd` | 84 | Same broad table regions with different endpoint values, one scalar, identification and checksums |
| `39990-TBA,A030-PTM.rwd` | 429 | Broader table changes, scalars, executable redirection/new routine, identification and checksums |

For the A030 legacy mod, the adjacent words at 0x137A8/0x137AA change from 5760/5760 to 8640/14400, respectively: factors of 1.5 and 2.5 at those particular entries. Related repeated entries change as well. Adjacent values at 0x139FA/0x139FC change from 264/264 to 1024/1152. This demonstrates selective calibration changes, not a uniform multiplication of the entire firmware or all torque commands.

For A030 linear-max, those first endpoint words become 29887/32767, and the second pair becomes 1500/1500. The filename alone does not establish physical linearity.

PTM changes larger regions beginning around 0x1379C, 0x139EC, and 0x13AE8. It replaces six bytes at 0x297D6 and adds a routine in formerly FF-filled space starting at 0x4F1CC. Its original six-byte sequence is reproduced at the start of the added routine. Additional scalar differences occur at 0x13544, 0x13716, and 0x2A6C0. This is evidence of an executable hook as well as recalibration; the hook's full semantics have not been reconstructed in this comparison.

The explicitly named **TBA-C020 2.5x** image differs from its matching stock file in 67 decoded bytes. At 0x13880/0x13882, values change from 4608/4608 to 8064/11520 (1.75x and 2.5x). The second repeated table region changes 264/264 to 1024/1152. Its remaining differences include one scalar, identification punctuation, and checksum words. Again, the 2.5x label corresponds to selected endpoint values, not a demonstrated constant physical-output multiplier.

## What this resolves for Odyssey research

We now have actual stock/modified Civic reference pairs, including a file expressly labelled 2.5x and a distinct PTM implementation. This resolves the earlier absence of comparison material. Next, the changed Civic table consumers can be traced and matched by function/data flow to the Odyssey consumers already identified. Raw address transplantation or matching a few constants is insufficient.

The comparison does not alter the established identification of Odyssey 0x3A128 as an arctangent table. It does not establish the Odyssey RWD cipher, active calibration bank, final current-demand limit, or a validated 2.5x patch. Internal checksums and RWD encoding are separate concerns.

The original Odyssey image remains unchanged with SHA-256 `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2`. No firmware was patched or flashed.
