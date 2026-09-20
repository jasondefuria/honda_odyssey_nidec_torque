# Pilot output-path follow-up: publication and diagnostic consumers

This pass identifies the exact publication path and separates verified diagnostic consumers from the still-unresolved motor path. It does not establish a new physical torque multiplier.

## Request publication

The previously traced limited request is stored at `gp-0x4AA8`. Getter `0x333F4` reads that signed halfword. Function `0x31898` calls the getter at `0x318EC`, saves the result at `gp-0x4CFC`, and writes it through the pointer stored at `gp-0x4458`.

That pointer is initialized at `0x3188A`–`0x31890` using getter `0x4176C`, which returns `gp-0x7DF8`. Thus the request is published as the first halfword of a two-word structure at **gp-0x7DF8**. The second halfword comes from getter `0x33406`; it must not be conflated with the request.

The scheduled caller path includes `0x454C4 -> 0x40030 -> 0x31898`. The next scheduled call is `0x45ED0`, whose first call is `0x41772`. This copies the published structure into two diagnostic-facing halfwords:

- first halfword: `gp-0x61AA`;
- second halfword: `gp-0x61A8`.

## Verified consumers of the copied request

Three direct reads of `gp-0x61AA` were found in the current linear listing:

| Reader | Observed use |
|---|---|
| `0x55796` | Stores the value into a larger collected state record at offset 0x64 from `gp-0x5C8C`. |
| `0x5BDDA` | Serializes its high and low bytes into an output buffer at offsets 0x10 and 0x11. |
| `0x5CCBE` | Serializes its high and low bytes into an output buffer at offsets 0x41 and 0x42. |

These accesses do not establish motor actuation. Other direct readers of getter `0x333F4`, at `0x4B5C6` and `0x4EB8C`, inspect request magnitude in conditional/status logic. The reader of `gp-0x4CFC` at `0x3E648` likewise forms a magnitude and compares thresholds.

The known request therefore reaches a published interface and observable diagnostic state. The actuator consumer could use an alias, an indirect pointer, or code outside the inspected application region; none of these possibilities is proven by this pass. An absence of additional literal-address references is not proof that the request has no actuator consumer.

## Integrity search result and coverage limit

The stock/modified RWD payload covers flash `[0x10000,0x60000)`. It does not supply bytes below `0x10000`. The generated padded ROM view uses zeros below that address for indexing only; those zeros are **not an actual boot-region dump**.

The searches in this pass did not establish an in-firmware consumer of the three verified cumulative checksum boundaries. Routines containing the upper address `0x5FFFF`, including `0x47C50` onward and `0x597CA` onward, perform bounded memory reads/copies; those constants alone must not be classified as checksum validation.

Consequently the distinction remains:

- **Verified:** container checksum, decoded payload checksums, and stock raw-dump equivalence.
- **Unresolved:** who checks those payload sums on-device, when checks run, the failure response, and any additional checks in unavailable regions.

A full flash dump including the lower region would improve coverage, but it would not by itself guarantee the remaining paths can be resolved without hardware context.

## Modification implications

The new publication trace does not remove the constraints already identified: nonlinear shaping, controller saturation, blending, the later ±2457 clamp, and mode-dependent processing. It also does not justify importing Pilot bytes into Odyssey. The Odyssey motor-output trace remains its own independent SH-2A analysis.

The next unresolved dependency is the actuator-side reader of the published request, rather than the diagnostic serialization path. Original Odyssey and Pilot input files remain unchanged.

[Evidence windows](pilot_output_boundary_disassembly.txt) · [CAN receive trace](pilot_can_receive_trace.md) · [Modification trace](pilot_modification_trace.md)
