from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];O=R/'outputs/dual_ecu_reconstruction';e=json.loads((O/'odyssey_evidence.json').read_text())
s='''# Clarity and Odyssey firmware reconstruction

Reconstructed 2026-10-05. Read-only analysis of decoded firmware and existing scoped emulation evidence. Addresses are ECU addresses, not offsets in the encrypted RWD container. This is a computational signal map; physical torque calibration remains unresolved.

## Main conclusions

Both firmwares contain mapped-target, feedback, scheduled P/D and saturation paths. Their fixed-point scales differ: the reconstructed Clarity P/D products divide by 1024; Odyssey divides by 64. Coefficients and clamp values cannot be transplanted numerically between them.

Odyssey v4 retains the original controller instructions in 0x7415C–0x74C9B. Its modified banks increase the target curve and P/combined limits, while P/D gain tables remain stock. Clarity PTM additionally changes feedback normalization, tracker gain, P/D coefficients, limits and executable feedforward/conditional-P logic.

Clarity's feedback now traces to a reconstructed cyclic angle and a difference estimator. This does not establish mechanical angle, electrical angle, Nm, amps or a physical sample period. The Odyssey upstream sensor-to-feedback chain has not been reconstructed to the same depth. Neither ECU has a complete physical calibration map.

## Input identities and reproducibility

'''
for n,f in e['files'].items():s+=f"- Odyssey {n}: `{f['path']}`; SHA256 `{f['sha256']}`.\n"
s+='''
Clarity stock SHA256: `d08a7f5c18ea6af9aaa1b366828fef226bb4ce192dc89a3d79d9c2661e1a7673`.
ClarityMax PTM: `d4fe903bcf347495f4321be65a3c650c8c931f1650c3bef6443721da0dd80f7d`.
Pminus5 variant: `1cff620c22e9d047cf1f3ca024688bdf578c5481d118fd4ee6438f54c13c7f7e`.

`odyssey_evidence.json` contains freshly decoded all-seven-bank curves, P/D gains, limits and PC-relative pointer values. `odyssey_controller_assembly.txt` contains SH-2A disassembly. Literal pools appear in linear disassembly and must not be interpreted as instructions. Reproduce with `work/dual_evidence.py` and `work/reconstruct_ody.py` (the latter requires pypcode).

## Odyssey signal path

Previously traced ingress: CAN 0x0E4 -> mailbox 0x16 -> 0x323B2 -> payload parser 0x14618 -> periodic 0x11D7E -> validity/fault selection 0x10DB4 -> signed controller input FFF8500C -> 0x72032/0x7276A preprocessing. Raw frame FFF85214, decoded state FFF85198, status FFF850DA. This ingress is carried forward from the earlier trace; the detailed arithmetic below was re-examined against v4.

| Stage | Evidence | Interpretation and boundary |
|---|---|---|
| Bank selection | FFF82F04 stores word offset; accesses multiply by 2 | For bank b, byte displacement (b-1)*0x300; live selected bank requires runtime evidence |
| Target curve | 0x7415C, raw signed word at input object +0x2C | Absolute magnitude, calibration clamp 0x57BAC+offset and hard ±1774 lookup bound; restores sign |
| Curve axes | X 0x57BAE, Y 0x57BC0, nine points, bank displacement | Interpolation uses cached slopes; output object +6 is signed target |
| Curve output object | Probe binding FFF82FF0 | +0 raw, +2 clamped, +4 magnitude, +6 signed mapped target |
| Feedback tracker | 0x742C0 calls 0x300DA | Alpha 0x57BD2+offset, state FFF86F60, clamp 0x57BD4+offset |
| Feedback input to PD | Third argument +0xA in 0x7435C | Probe binding FFF83002; physical origin is not established here |
| Error | 0x74854 subtracts feedback from target | Signed target-feedback, 32-bit intermediate |
| D schedule | X 0x57C4C, Y 0x57C5E, nine points per bank | Product of error difference and interpolated gain; signed truncation /64 |
| D clamp | 0x74950 onward, table 0x57BD6 | Symmetric internal-output clamp |
| P schedule | X 0x57C70, Y 0x57C82 | Current error times interpolated gain; signed truncation /64 |
| P clamp | 0x74A68 onward, table 0x57BD8 | Symmetric internal-output clamp |
| Combined output | 0x74A98 onward | P+D multiplied by earlier scheduled factor, signed truncation /256, then clamp 0x57BDA |
| Further scale | 0x74B26 onward | Multiply by signed word at 0x500A6, arithmetic shift right 10, saturation ±32767 |
| Later mixer | 0x74C9C | Additional weighted components, bounds 0x57B24/26 and clamp 0x57C94; not demonstrated motor current or torque |

The earlier portion of 0x7435C combines two eight-point schedules and two six-point schedules using weights with /16384 scaling. The later scheduling-factor product has /256 scaling. These extra factors are why the P clamp alone does not determine delivered output. Physical labels for these schedule inputs have not been proven.

### Odyssey tracker equation

For signed32 state S, signed16 input x and signed16 alpha:

    old = arithmetic_shift_right(S, 15)
    S_next = wrap32(S + alpha * (x - old))
    output = arithmetic_shift_right(S_next, 15)

0x300DA uses arithmetic shifts, including for negative states. The neighboring helper 0x300F8 adds a negative-value rounding correction, but it is NOT the target of the 0x742C0 call. This distinction matters for bit-exact emulation.

### Odyssey controller observation structure

0x7435C writes the following offsets relative to its output structure (the scoped emulator binds it to FFF83004):

| Offset | Value |
|---|---|
| +0x04 / +0x06 | Feedback / mapped target |
| +0x28 | Combined schedule factor |
| +0x3E / +0x40 | Interpolated D / P coefficients |
| +0x44 / +0x4C | D product after /64 / clamped D |
| +0x54 / +0x5C | P product after /64 / clamped P |
| +0x60 | P+D before schedule multiplication |
| +0x64 | Scheduled sum before combined clamp |
| +0x70 / +0x72 | Combined-clamped output / globally scaled saturated output |

History is stored through indexed structure fields, so the prior-error interpretation depends on the selected history index and normal calling sequence. Synthetic RAM probes alone do not establish real task timing.

## Odyssey stock versus v4, all banks

| Bank | Minimum field stock→v4 | P limit | D limit | Combined limit | Target endpoint |
|---|---|---|---|---|---|
'''
for b in e['banks']:
 a,z=b['stock'],b['v4']; vals=[str(b['bank'])]+[f"{a[k]} → {z[k]}" for k in ['minimum_field','P_limit','D_limit','combined_limit']]+[f"{a['curve'][-1]} → {z['curve'][-1]}"]
 s+='| '+' | '.join(vals)+' |\n'
s+='''
Minimum fields are raw calibration values, not a claim that the complete ECU will engage at a particular mph. Other validity and fault conditions still exist. Banks 4–7 are unchanged for every field and curve listed here; this is not a claim that every byte of those entire memory regions was compared.

Banks 1–3 target Y stock: `[0,2019,3230,3980,4345,4577,4721,4864,4864]`.
V4: `[0,3968,7936,9950,10863,11443,11803,12160,12160]`.
The first nonzero ratio is approximately 1.9653, the second 2.4570, and later points approximately 2.5. This is not a uniform 2.5 multiplier and is not evidence of 2.5x physical steering torque.

Banks 1–3 P gain table remains `[1,4,6,8,10,11,11,11,11]`; D remains `[32,32,32,32,32,32,16,16,16]`.
Banks 4–7 P remains `[2,6,8,9,9,9,9,9,9]`; D remains `[10,16,16,16,16,16,16,16,16]`.

## Clarity reconstruction and PTM differences

The detailed evidence-bounded Clarity map is appended below. Its dated additions supersede earlier unresolved descriptions where stronger evidence was obtained.

| Feature | Stock | Clarity PTM |
|---|---|---|
| P clamp, 0x1390C | 1774 | 7373 |
| D clamp, 0x1390E | 333 | 1774 |
| Later output clamp, 0x13910 | 1774 | 9000 |
| Feedback normalization multiplier | 3429/256 | 1650/256 |
| Tracker alpha, 0x1380A | 1999/32768 | 3200/32768 |
| Added target feedforward | Absent | (45*target) arithmetic-shift-right 10, saturating addition |
| Conditional P logic | Original | Patch at 0x1B864, path-dependent interpolator register use |

Pminus5 differs from ClarityMax in only 13 payload bytes: ten first-P-row bytes and three checksum bytes. Executable logic is identical. Its first P row is `[117,148,184,220,245,257,263,265,265]`, versus ClarityMax `[123,156,194,232,258,270,277,279,279]`. A forced seventh row bypasses that first-row change.

## Validation scope

Fresh checks in this reconstruction: RWD parsing, hashes, all-seven-bank extraction, literal-pointer resolution, controller-region stock/v4 byte equality and SH-2A static disassembly. Existing R2 scoped emulator results cover original instructions with synthetic RAM, curve sweeps and controller/monitor probes. Their image hashes differ from v4; they are supporting algorithm evidence, not a new full-v4 or physical-plant validation.

Previously recorded v4 integrity audit reports CRC32/BZIP2 0x134AE5B1 at 0x4FF7C and 0xDA5B0744 at 0x6FF7C, application A=0x5E6D, C=0x8B9A, full downloaded BE16 word sum zero, container sum 0x045554EA. See ../mod25xv4_audit/analysis.json and previous checksum reports. These checks establish consistency of those checksums, not correctness of the calibration or ECU acceptance.

## What remains unresolved for both files

- Engineering-unit conversion from controller targets and outputs to Nm or motor current.
- Complete downstream current regulation, PWM and power-stage limits.
- Actual task periods, live operating-mode/bank selection and complete pointer initialization.
- Clarity CAN-to-target origin and exact angle-sensor identity; Odyssey upstream sensor/estimator chain to the same depth as Clarity.
- Measured closed-loop stability and response under mechanical load.

Accordingly, Clarity and Odyssey now have documented computational maps, but not equally complete sensor provenance or physical calibration. No firmware was modified by this reconstruction.

---

'''
s+=(R/'outputs/clarity_ptm_comparison/PHYSICAL_SIGNAL_MAP.md').read_text()
(O/'RECONSTRUCTION.md').write_text(s)
print(O/'RECONSTRUCTION.md')
