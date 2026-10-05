# Honda Odyssey EPS `39990-THR-A020`: firmware findings and modification path

Status as of 2026-09-25. This document contains current findings only; claims that were later disproven have been
removed. The full dated audit trail, including every correction, is in `RUNNING_LOG.md`, which sits next to this
file.

**Evidence labels.**
- **FACT**: traced in the raw bytes and/or reproduced by running the unmodified ROM in an SH-2A emulator.
- **INFERENCE**: well supported, but not closed by a producer chain or a live test.
- **OPEN**: not known.

**Safety.** Nothing described here has been flashed to a THR ECU. This is the steering ECU, and the same platform
has a history of failed flashes (see §9.5). Treat §10 as a plan, not a recipe that has been proven on a car.

---

## 0. Summary

- **Image.** `39990-THR-A020user.bin` is a 512 KiB SH-2A big-endian image, SHA-256 `e2c3c5bb3746f417…c73ecf2`.
  - The platform matches the Acura RDX TJB (R5F72A08 class).
  - The flashable application is `0xC000–0x7FFFF`. The window comes from the updater's own range record.
- **Controller.** The LKAS controller is fully decoded and was verified **bit-exact by executing the ROM**. Its shape:
  - `0x0E4` torque command → driver-override fade → command curve (s);
  - a filtered feedback signal (ref) is subtracted to form an error;
  - PD on the error, with a gain product K;
  - a ±1024 clamp, then a ramped mix into a ±8868 total.
- **Clarity (TRW) comparison.** The design is the same as the Clarity controller: same stages, same order, many
  identical calibration values and axes. The code is a separate implementation.
  - THR has **no NORM constant**.
  - THR's stock limits are more conservative: final clamp 1024 vs 1774, override cut 768 vs 1536.
- **Stock LKAS ceiling.**
  - Normal (bank 1) steady output is **u = 836 counts**; the hard limit is 1024. That is at most **11.5%** of the
    ±8868 motor-command range.
  - The steady ceiling is set by curve × Kp, **not by the clamps**. Raising the clamps alone gives no steady-state
    gain.
- **Calibration banks.** Every stock profile selects banks 1–3, which are identical. Bank 7, the "Clarity row 6"
  profile, is used only under an override flag.
- **RWD.** A THR RWD can be built by borrowing the Honda container format and the RDX platform details (cipher,
  checksum slots, identity table). THR's own checksums are fully reproduced. What is **not** proven: the THR
  header's old-version list, and whether the post-flash dependency check (which failed on RDX) will pass.
- **CCP.** THR has a CCP 2.1 calibration endpoint on CAN `0x721/0x722`. It can read memory without a security
  unlock, which gives a way to read the car's actual flash and compare it with this image before any flash.

---

## 1. Image, tools and method

| Item | Value |
|---|---|
| File | `39990-THR-A020user.bin`, 524,288 B, SHA-256 `e2c3c5bb3746f417e70776967f8e1758bb3073fa551f553942a04e822c73ecf2` |
| CPU | Renesas SH-2A, big-endian (vector base `0x10000`; the reset vector area `0x0–0x3FF` is erased in this dump) |
| Erased extents | `0x0000–0x1FFF`, `0x6000–0x7FFF`, `0xB000–0xBFFF`, `0x5A000–0x5DFFF`, `0x7B000–0x7CFFF` |
| Flashable window | `0xC000`, length `0x74000` (FACT: updater range record at `0x52B2`: count 1, start `0x0000C000`, length `0x00074000`; `RequestDownload` rejects anything else) |
| Identical copies | `~/Downloads/odyssey-39990-THR-A020.bin` and `~/Downloads/(2018 Odyssey)39990-THR-A020user.bin` (same SHA-256) |

**Tools**, in `THR_A020_INDEPENDENT_TRACE_20260920/verify/`:
- `sh2a_emu.py`: a strict SH-2A interpreter. It raises on unknown opcodes and on any write to ROM.
- `verify_controller.py`: runs the firmware's own calibration init, then calls each controller stage with its real
  calling convention and compares the result with an independent model written from the formulas below.
- `sh2a_decode.py`: a disassembler.
- `ratetest.py`: the Clarity rlog fits.
- `xmatch.py`, `homolog.py`: TRW↔THR similarity search.

ROM patches are applied only to an in-memory copy; the BIN has never been modified.

**Emulator result (FACT).** With the firmware's own table lookup modelled, 3,000 random cases per stage in banks 1
and 4 were bit-exact for PD, curve, fade and mixer. Deliberately wrong variants of the model were all rejected:
- wrong shift;
- missing clamps;
- sign flipped;
- gains swapped;
- crossfade ignored.

**Interpolation quirk (FACT).** THR precomputes Q26 slopes at boot (`FUN_000720DC`) and splits the multiply into
two separately truncated halves. The result sits slightly below exact linear interpolation. For example, Kp at
|a| = 428 is 8, where exact interpolation gives 9.

---

## 2. Identity, profiles and calibration banks

### 2.1 Identity table (`0x5EB00`, 14 records, stride `0x46`) — FACT

Every record carries the hardware role `THR-A010` and the software role `39990-THR-A020`. There are 8 keyed
profiles; the rest are unkeyed fallback records.

| Key (5 B) | Assembly | Calibration | Selector (+0x10) |
|---|---|---|---|
| THRA0 | 53600THRA020M1 | 5360YTHRA000 | 1 |
| THRC0 | Q53600THRA020M1 | 5360YTHRC000 | 1 |
| THRA1 | 53600THRA020M1 | 5360YTHRA100 | 2 |
| THRA2 | Q53600THRA020M1 | 5360YTHRA200 | 2 |
| THRA3 | q53600THRA020M1 | 5360YTHRA300 | 2 |
| THRA4 | q53600THRA020M1 | 5360YTHRA400 | 3 |
| THRX0 | 53600THRA020M1 | 5360YTHRX000 | 3 |
| THRY0 | Q53600THRA020M1 | 5360YTHRY000 | 3 |
| (6 unkeyed) | 53600000000000 | 5360Y0000000 | 1 |

`THR-A010` (hardware/base) and `39990-THR-A020` (software) are **distinct roles**. RDX has exactly the same
structure. This matters for flashing (§9.5).

### 2.2 Bank selection — FACT

- `FUN_0002F8FC` matches the 5-byte key.
- At `0x19358–0x19370`: **if either byte of `FFF85420` is 1, mode = 7**; otherwise mode = the record's selector byte.
- `FFF82F04 = (mode−1)·0x180`, so tables are read at `base + (mode−1)·0x300`. The same code also sets the bank
  offsets of other EPS subsystems, so mode 7 is an EPS-wide alternate calibration.

The LKAS calibration base is `0x57B00`; bank k is at `0x57B00 + 0x300·(k−1)`.

| Bank | Used by | Content |
|---|---|---|
| 1, 2, 3 | every stock profile | byte-identical ("normal"). **These values run in normal driving.** |
| 4, 5, 6 | no stock profile | identical to bank 7 |
| 7 | only when `FFF85420` override = 1 | the "Clarity row 6" family (§7) |
| 8 (`0x59000`) | — | differs in 375 of 384 words; role OPEN |

OPEN: which key the car's EPS is configured with (it doesn't change the result, since banks 1–3 are identical), and
what sets `FFF85420`.

### 2.3 Checksums — FACT (both slots reproduced)

| Word | Address | Rule | Stock |
|---|---|---|---|
| A | `0x7FF80` | BE u16 word sum over `[0xC000, 0x7FF80)` | `d0ca` |
| B | `0x7FFFA` | fixed family magic (same on RDX and Civic); not computed | `b7c8` |
| C | `0x7FFFE` | −(BE u16 word sum over `[0xC000, 0x7FFFE)`), so the whole payload sums to 0 | `a6e0` |

- On THR both slots reproduce with a **zero seed**; there is no bootloader constant.
- On RDX the same scheme needed K = 0xE863 added to both slots.
- Recompute A first, then C, because C covers A.
- This is the same sum/negative-sum pair Honda uses on Civic/CR-V/Clarity (`eps_tool.py` `checksum_by_sum` /
  `checksum_by_negative_sum`). A modified Civic C120 flash that recomputed only these two slots passed the ECU's
  check on a real car.

---

## 3. Diagnostics and calibration protocols

### 3.1 UDS — FACT

- **Security access.** THR has the Honda seed/key cluster:
  - seed generator `0x4F2E`;
  - multiply `0x4EF4`;
  - transform `0x4F6A`: `((seed·0x0112) % 0x1120) ^ ((seed + 0x0111) & 0xFFFF)`;
  - check `0x4F98`;
  - constant `01 11 01 12 11 20` at `0x51E4` (and `0x3E2E4`).

  The code body and constants are identical to the CR-V (TLA-A040) cluster. The `0x27` dispatch pointers
  (`0x13FE`/`0x1486`) land in the erased prefix of this dump. The resident call edge is therefore not visible, but
  the algorithm is.
- **`2E F101`** (flash decryption key) accepts exactly 3 data bytes and stores them at `0xFFF80C51`.
- **`34 RequestDownload`** accepts only start `0xC000`, length `0x74000`. Transfers are written in `0x100`-byte
  blocks.
- **`31` RoutineControl `0xFF00`** loads an updater code overlay from ROM `0x52D0` (XOR `0xCC`) into
  `FFF80000–FFF803C7`. `11 ECUReset` or session timeout zero-fills `FFF80000–FFF8067F`. These are reprogramming
  paths, not normal operation.

### 3.2 CCP 2.1 endpoint on CAN `0x721` (RX) / `0x722` (TX) — FACT (static; no traffic sent)

- **Wiring.** Descriptor #1 = RX `0x721` DLC 8; #33 = TX `0x722` DLC 8. Both are programmed by the CAN init.
  `FUN_00038152` polls mailbox 1 → dispatcher `FUN_00037CB2`.
- **Commands.** Classic CCP set, version response 2.1:
  - CONNECT `0x01` (station address `0x20F3` or 0), TEST `0x05`, DISCONNECT `0x07`;
  - SET_MTA `0x02`, DOWNLOAD `0x03` / `0x23`, UPLOAD `0x04`, SHORT_UPLOAD `0x0F`;
  - GET_SEED `0x12`, UNLOCK `0x13`;
  - DAQ `0x14–0x16`, START_STOP `0x06` / `0x08`, EXCHANGE_ID `0x17`.
- **Reads need no unlock.** UPLOAD requires only CONNECT; there is no unlock check. SET_MTA → UPLOAD reads memory
  by address, 5 bytes per frame.
  - Caveat 1: while `FFF8429D.bit0` is clear, addresses `0x10000–0x3FFFF` are remapped to `0x50000 | (addr & 0xFFFF)`.
  - Caveat 2: `0x5FC00–0x5FDB3` is read through a 109-entry pointer table.
- **Writes need unlock.** DOWNLOAD requires the unlock bit `FFF8429D.bit0`, which is set by GET_SEED/UNLOCK
  (level 1).
- **Use.** This is a way to read the car's real flash (and RAM) and compare it with this image before any flash.
  OPEN: live reachability, and which ranges production firmware allows.

---

## 4. CAN map (THR descriptor table `0x3DA90`, 16 B/entry, ID at +4, DLC +0xC, direction +0xD) — FACT

| Mailbox | ID / DLC | Direction | Odyssey OpenDBC message | Use in the EPS |
|---|---|---|---|---|
| 22 | `0x0E4`/5 | RX | STEERING_CONTROL | LKAS torque command → `FFF8500C` |
| 13 | `0x156`/6 | RX | STEERING_SENSORS | STEER_ANGLE → `FFF85148` → `FFF85032` (×1.6). **Bytes 2–3 (STEER_ANGLE_RATE) are never read** |
| 2 | `0x158`/8 | RX | ENGINE_DATA | XMISSION_SPEED → `FFF8500A`, vehicle speed at 0.5 kph/count, slew-limited |
| 7 | `0x1D0`/8 | RX | WHEEL_SPEEDS | `FFF85018/1A` (speed-limiter index) |
| 6, 14, 3, 4, 8, 9, 12, 18 | 0x1B0, 0x1EA, 0x17C, 0x324, 0x1A4, 0x130, 0x094, 0x13C | RX | STANDSTILL, VEHICLE_DYNAMICS, … | chassis-message health (`FFF82F15`) and other uses |
| 37 | `0x18F`/7 | **TX** | STEER_STATUS | B0–1 STEER_TORQUE_SENSOR = `FFF80016`·250>>6; B2–3 STEER_ANGLE_RATE = `FFF8005E`; B4 STEER_STATUS / CONTROL_ACTIVE |
| 34 | `0x1AB`/3 | **TX** | STEER_MOTOR_TORQUE | MOTOR_TORQUE, OUTPUT_DISABLED |
| 38–40 | 0x64D, 0x6B2, 0x6B3 | TX | — | not in DBC |
| 1 / 33 | 0x721 / 0x722 | RX / TX | — | CCP (§3.2) |

**Difference from Clarity.** The Clarity EPS **transmits** `0x14A` STEERING_SENSORS: it is the steering-angle sensor,
with angle and rate derived from its motor resolver. The Odyssey EPS does **not** transmit `0x156`; it **receives**
it from another node and ignores its rate field. Both publish `0x18F` STEER_STATUS.

---

## 5. The LKAS controller, stage by stage (FACT; bank 1 = normal, bank 7 = override)

**Call structure.**
- `FUN_00072032` runs `FUN_000726DA` every call: monitors, state machine, ramps, both trackers, STEER_STATUS.
- `FUN_0007276A` runs every second call: limiter, fade, curve, PD.
- The DMA-completion callback alternates between the controller and the output mixer `FUN_00019D92`.
- Timing INFERENCE: `0x18F` goes out every 20 callbacks. If that is 100 Hz, as openpilot sees on Honda:
  - callback = 2 kHz;
  - `726DA` and the mixer = **1 kHz**;
  - `7276A` (PD) = **500 Hz**.

### 5.1 Pipeline

| # | Stage | Function → output | Math | Bank 1 (normal) | Bank 7 (override) |
|---|---|---|---|---|---|
| 1 | Command input | `0x0E4` parser `FUN_00014618` → combiner `FUN_00010DB4` → `FFF8500C` | STEER_TORQUE s16. Also parsed: B2.7 REQUEST, B2.6 gain-profile select (W crossfade), B2.3:2 ramp/abort code, B2.1:0 inhibit, B4.6 standstill permit. openpilot sends only torque + request | — | — |
| 2 | Pre-limit | `FUN_00073A28` → `FFF82F84` | a = cmd/4 (toward zero). Clamp cmd to ±26 if any `0x0E4`/range monitor flag is set | ±26 (`0x57CDA`) | same |
| 3 | Speed limiter | `FUN_00073AE0` → `FFF82F90` | index = max(speed `FFF8500A`, mean(`FFF85018`,`FFF8501A`)); \|a\| ≤ L(index) | BP 0…400 step 50 (0–200 kph), **L = 1024 flat** | same |
| 4 | Driver-override fade | `FUN_00073D20` → `FFF82FC0+0x2C` | g = [W·A(\|T\|) + (1−W)·B(\|T\|)] ≫ 14 · C(\|E0rate\|) ≫ 8; out = g·a ≫ 8. **Zero if \|T\| ≥ 768** (`0x57B52`), any monitor flag, or inhibit. T = `FFF80016`, clipped to 2176 | A = B: BP `0,341,518,623,735,826,889,1281` → `256,256,166,117,62,20,0,0`. C flat 256 | A = B: BP `0,256,…,1792` → `256,256,169,44,0,0,0,0` |
| 5 | Command curve | `FUN_0007415C` → s at `FFF82FF0+6` | \|a\| clamped to 1024 (`0x57BAC`), then table, sign restored | BP `0,128,…,1024` → `0,2019,3230,3980,4345,4577,4721,4864,4864` | BP `0,222,…,1774` → `0,1715,2842,3277,3738,4173,4506,4570,4570` (≈ 4006 at 1024) |
| 6 | Tracker-1 (feedback) | `FUN_000742C0` → ref at `FFF82FF8+0xA` | ref = one-pole(`FFF8029C`): `state += (x − state≫15)·k`, α = k/32768; clamp ±32765 | k = 410 (α 0.0125, τ ≈ 80 calls) | k = 30110 (α 0.92, almost none) |
| 7 | Tracker-2 (rate) | `FUN_00073BCC` → E0rate at `FFF82FA0+0x18` | first difference of `FFF802E0` ×1000≫4, ±32767; **two cascaded** one-poles (k `0x57B4E`); clamp ±320 (`0x57B50`) | k = 546 | k = 25951 |
| 8 | PD | `FUN_0007435C` → **u = `FFF83074`** | err = s − ref. P = clamp(Kp(\|a\|)·err ≫ 6, ±`0x57BD8`). D = clamp(Kd(\|a\|)·Δerr ≫ 6, ±`0x57BD6`). K = [W·E(\|T\|) + (1−W)·F(\|T\|)]≫14 · [W·G(\|E0rate\|) + (1−W)·H(\|E0rate\|)]≫14 ≫ 8. **u = clamp(K·(P+D) ≫ 8, ±`0x57BDA`)**. `FFF83076` = u·4011≫10 (not read by the mixer). The G/H key is also clamped to ±320 in code | Kp BP `0,55,166,319,532,776,887,942,998` → `1,4,6,8,10,11,11,11,11`; Kd BP `0…1024/128` → `32,32,32,32,32,32,16,16,16`; E = F BP `0,182,259,301,385,567,714,812` → `256,256,256,247,214,126,51,0`; G BP `0,24,272,288,304,320` → `256,256,102,102,102,102`; H BP `0,16,160,192,256,320` → `256,256,102,77,77,77`; **clamps D 640 / P 1024 / u 1024** | Kp `2,6,8,9,9,9,9,9,9`; Kd `10,16×8`; E = F BP `0,256,…,1792` → `256,256,169,90,49,49,49,49`; G = H BP `0,64,…,320` → `256,256,230,200,169,148`; same clamps |
| 9 | Output mixer | `FUN_00074C9C` (from `FUN_00019D92`) | total = clamp(`FFF80198` + R·u≫14 + (1−W)·(A·`FFF823F2`≫14)≫14, **±8868** at `0x57C94`). u enters 1:1 at R = 16384 (emulator-verified) | — | — |
| 10 | Hand-off | `0x19DF0–0x19E5A` | optional LPF → stored to `FFF83484`/`FFF834C4`/`FFF85422`/`FFF8543C`; **conditional ±388 clamp** if `(@r12 & 0x200)` (trigger OPEN) | — | — |

`FFF80198` is the non-LKAS (base assist) term. The ±8868 limit bounds the **sum**; it is not an LKAS-only limit.

### 5.2 Table-slope rule — FACT (emulator)

Boot-time slopes saturate at 31 per input count.
- Any table segment with |ΔV|/ΔBP ≤ 31 interpolates exactly.
- Steeper segments undershoot between breakpoints (values at the breakpoints themselves stay exact).
- For the bank-1 curve (ΔBP = 128), this means **≤ 3968 per segment**. A linear 0 → 30000 curve is fine;
  0 → 32767 is not.

### 5.3 State machine, ramps, engage conditions — FACT

- **State byte `FFF82F35`:**
  - 1 IDLE;
  - 2 RAMP_IN / RAMP_OUT;
  - 3 ACTIVE (with crossfade sub-states);
  - 4 ABORT_CUT;
  - 5 LOCKOUT.
- **STEER_CONTROL_ACTIVE** is `FFF82F36`.
- **Engage (IDLE → RAMP_IN)** requires all of:
  - REQUEST = 1;
  - speed within `[0x57B00 = 10, 0x57B02 = 400]` (5–200 kph), **or** the standstill path (speed ≤ `0x57B04` = 0
    with B4.6 set);
  - assist-limit minimum ≥ 8868 (`0x57B06`);
  - \|cmd\| ≤ 4096;
  - all monitors clear, inhibit = 0, and the config flag `FFF86E83` set.
- **Authority ramp** R (`FFF82F64`, Q14). Step = 16384/N, with N from `0x57B18` = `[1024,1024,1,100,500,1024]`.
  - openpilot's bits give **ramp-in +16 per tick and ramp-out −16 per tick (1024 ticks, ≈ 1 s at 1 kHz)**.
  - Abort drops R to zero in one tick.
- **Bank-7 difference:** minimum engage speed is 70 (35 kph) instead of 10.

### 5.4 STEER_STATUS arbiter (`FUN_000754B0` → `FFF82F14`) and monitors — FACT

STEER_STATUS values, in priority order:

| Value | Name | Condition |
|---|---|---|
| 6 | tmp_fault | LKAS config off |
| 7 | permanent_fault | system fault |
| 5 | fault_1 | any latched level-3 monitor |
| 3 | low_speed_lockout | **any** level-2 degradation, not only low speed |
| 4 | no_torque_alert_2 | E0 plausibility |
| 2 | no_torque_alert_1 | \|E0\| > 768 |
| 1 | driver_steering | B4.6 set |
| 0 | normal | — |

Monitors:
- **F0F, command range:** \|cmd\| > 4096. Level 2 after 50 ticks; latched after 59,950 ticks.
- **F10, commanding against the driver:** \|E0\| ≥ 768 and \|cmd\| > 26.
- **F4E/F4F, E0 level/rate plausibility.**
- **`0x0E4` COUNTER / CHECKSUM / TIMEOUT** families, severities at `FFF82F0C/0D/0E`.

### 5.5 Stock output limits — FACT (firmware executed; T = 0, E0rate = 0, W = R = 16384)

| Bank | Max curve s | u at ref = 0 | u at ref = s/2 | u when ref opposes s |
|---|---|---|---|---|
| 1 | 4864 (a ≥ 896) | **836** | 418 | 1024 (ref ≲ −1100) |
| 7 | 4006 | **563** | 281 | 1024 (ref ≲ −3300) |

- In steady state the ceiling is **curve × Kp/64**, not a clamp.
- The absolute ceiling is 1024, which is 11.5% of ±8868.
- E4 beyond ±4099 is clipped; beyond ±4096 it trips the range monitor.

**Clamps-only test (FACT, emulator):** D/P/u raised to 1774/7373/8868.

| Bank 1 case | Stock clamps | Raised clamps |
|---|---|---|
| ref = 0 | 836 | **836** (unchanged) |
| ref = −8000 | 1024 | 2211 |
| ref = −32765 | 1024 | 6467 |
| D kick (Δerr 20000) | 1024 | 2610 |

**Raising clamps alone gives no steady-state authority**; it only affects feedback-opposed and transient cases.
Clarity worked the same way: stock TRW P peaks at about 960, under its own 1774 clamp.

---

## 6. The feedback and sensor signals

**`FFF80000–FFF802EB` is a foreign-producer interface block (FACT census).** About 50 words there are read by the
application but never written in normal operation. The candidates for their producer are the erased regions or
code outside this dump. This covers `FFF80016`, `FFF8005E`, `FFF80198`, `FFF8029C` and `FFF802E0`.

| Signal | What is proven | Best reading |
|---|---|---|
| `FFF80016` (T) | FACT: published as 0x18F **STEER_TORQUE_SENSOR** (×250≫6), which openpilot reads as driver torque | driver torque |
| `FFF8029C` (ref) | FACT: its only literal reference is `0x726FA`; it is one-pole filtered and subtracted from the command curve; clamp ±32765 = the Clarity R6 clamp | INFERENCE (strong): an **EPS-internal, resolver-derived steering rate in Clarity-R6 units** (≈ 296 counts per deg/s at Clarity stock scaling). Evidence: bank 7's curve equals Clarity target row 6; the Clarity estimator code is present (`0x27422` → `FFF85538`); the 0x156 rate field is ignored. Producer OPEN |
| `FFF8005E` | FACT: published as 0x18F STEER_ANGLE_RATE | on Clarity the 0x18F rate is R6's input ÷ 32 (proven, below). Whether `FFF8029C` = 32 × `FFF8005E` on THR is OPEN |
| `FFF802E0` (E0) | FACT role: the **driver-intervention detector input**. It drives STEER_STATUS 2/4, the F10 fault, the plausibility monitor and tracker-2 (G/H gain). Its thresholds share the 768 constant with T | INFERENCE: torque-class (Clarity tracker-2 differentiates the torque sensor and uses the same G/H values). Not labelled without a producer chain |

**Clarity reference (FACT, proven on two routes).** Clarity R6's input equals clamp(estimator·NORM/256), which equals
**32 × STEER_STATUS.STEER_ANGLE_RATE raw**:

| Route | NORM | Measured 0x18F slope | Predicted | Correlation |
|---|---|---|---|---|
| 154 | 1650 | 0.20116 | 0.20142 | 0.9989 |
| 51 | 3300 | 0.39976 | 0.40283 | 0.9909 |

`0x14A` is NORM-independent. Side effect: a NORM change also rescales the published 0x18F rate.

---

## 7. Odyssey vs Clarity: stage-by-stage

| Stage | Clarity TRW | Odyssey THR |
|---|---|---|
| Speed envelope | `FUN_29C14`: clamp to ±L; row 0 L = 1774 to 100 kph → 1330 at ≥ 130 kph (0.5 kph/count) | `FUN_00073AE0`: same axis, **flat 1024** (no speed limiting) |
| Speed window | `0x13638` = 10/400/0 | `0x57B00` = **10/400/0** (bank 7: 70) |
| Override fade | `FUN_29CAE`, hard cut at 1536 | `FUN_00073D20`, hard cut at **768** (≈ the same physical torque by unit fit, INFERENCE) |
| Target map → R5 | `FUN_29FB4`, 7 rows, input ≤ 1663, stock peak 5120 | curve → s, input ≤ 1024, peak 4864 (bank 7 = **TRW row 6 exactly**) |
| Feedback → R6 | estimator × **NORM** (`0x2AF9C`) → tracker-1 α 1999 | `FFF8029C` (no NORM) → tracker-1 α 410 (bank 7: 30110) |
| Tracker-2 | `FUN_29E3E`: torque diff ×500/32, 2 poles, k 3869, clamp 32767 | `FUN_00073BCC`: E0 diff ×1000/16, 2 poles, k 546/25951, clamp **320** |
| P / D | gain/1024, clamps 1774 / 333 | gain/64, clamps **1024 / 640** |
| Gain product | A (helper-A, torque) × B (A280, tracker-2) | E/F (torque) × G/H (tracker-2); bank 7 values identical to TRW |
| Final clamp | `0x13910` = 1774 | `0x57BDA` = **1024** |
| To motor | blend → motor interface (path to the 8868 sum not fully traced) | mixer, ±8868, 1:1 (proven) |
| Calibration selection | 7 rows, row byte (row 0 normal, row 6 override) | 8 banks (1–3 normal, 7 override) |

**Shared platform material (FACT).** 188 byte-identical runs (37 KB) between the two images:
- the sine, atan and √ tables;
- the one-pole helper;
- flash/boot support;
- CAN mailbox config;
- the library in the same link order.

The LKAS application code itself is a separate implementation (≤ 9% masked identity).

---

## 8. What the Clarity Tracker3200 build changed, mapped to THR

TRW stock (`e21f980d…`) vs the latest driven build (`…Tracker3200_Norm1650…COMPAT.bin`, `92cde599…`). The diff is
782 bytes, all classified.

| # | Clarity change | Ratio to stock | THR target (bank 1; repeat for banks 2–3) | Type |
|---|---|---|---|---|
| 1 | target map, 5120 → 30000 | ×5.86 | curve V `0x57BC0` (≤ 3968 per segment) | table |
| 2 | clamps P / D / final, 1774/333/1774 → 7373/1774/9000 | — | `0x57BD8` / `0x57BD6` / `0x57BDA` | table |
| 3 | P row 0, 77…192 → 117…265 | ×1.34–1.52 | Kp V `0x57C82` | table |
| 4 | D row 0, 512 → 737 | ×1.44 | Kd V `0x57C5E` | table |
| 5 | tracker-1, 1999 → 3200 | α ×1.6 | `0x57BD2` 410 → 656 (**bank 7 cannot take ×1.6**) | table |
| 6 | NORM 3429 → 1650 | feedback ×0.481 | **no constant on THR**: code patch at `0x726FE` (the ref load) | code |
| 7 | A280 knees 160/240/320 → 200/320/480 | — | G/H: THR's key is hard-clamped at 320, so only stretch within 0–320 | table |
| 8 | speed-window min 10 → 0 | — | `0x57B00` | table |
| 9 | feedforward: + (45·R5)≫10 before the final clamp | — | new code before the u clamp in `0x7435C` | code |
| 10 | "P pocket" windup limiter | — | new code | code |
| 11–12 | telemetry `0x6A0–0x6A3` via a packer hook + spare descriptors | — | spare descriptors #41–63 (dir byte = 2) + TX hook; free space e.g. `0x594F0` (0x4D10 B, candidate) | code |
| 13 | part number comma form `39990-TRW,A020` | — | **do not copy into a first THR build** (§9.5) | identity |
| 14 | checksums | — | `0x7FF80`, `0x7FFFE` | — |

**Port the ratios, not the absolute numbers.** THR's feedback scale isn't known, but THR's stock curve and ref
agree with each other.

With no NORM, there are two routes:
- **Route A, code patch:** ref ×0.481 at `0x726FE`. The curve and gains then port directly:
  - Kp ≈ Clarity P/16 = `7,9,12,14,15,16,16,17,17`;
  - Kd ≈ ×1.44.
- **Route B, tables only:** the curve would need about 12× stock (≈ 59,000), which is over the 16-bit and slope
  limits. It caps near 31,700, giving about half of Clarity's authority at matched loop gain.

**Clamp units.**
- The clamp roles match (P/D before the ≤ 1.0 gain product, final after).
- P and D counts match within about 10%: the error units are equal (row-6 identity) and the stock gains are
  equal (0.1875 vs 0.172; D 0.5 on both). So 7373 and 1774 carry over as absolute values.
- Clarity's 9000 means "no controller cap" only if TRW's output is 1:1 into its 8868 sum, which is unproven.
  The THR equivalent with a proven meaning is **u = 8868**.

---

## 9. Building a THR RWD, and why the recipe is borrowed

### 9.1 Honda container grammar — FACT (TRW, TLA, RDX files parsed)

```
"Z\r\n"
6 headers, each: count byte, then for each item a length byte + bytes
  h0 = 00
  h1 = (empty)
  h2 = 30                          ← EPS diagnostic address (0x18DA30F1)
  h3 = list of accepted current-software versions, each "39990-XXX-Annn\0\0"
  h4 = one security-key record per h3 entry: 01 11 01 12 11 20
  h5 = 01 02 03                    ← encryption key (sent with 2E F101)
start address (u32 BE), payload length (u32 BE)
encrypted payload
trailer = u32 LE additive sum of every preceding byte of the file
```

Examples. Comma-form entries were added by the community so that modified ECUs (which report a comma part number)
can be reflashed.
- Clarity stock-based file: h3 = `39990-TRW-A010`, `39990-TRW-A020`, `39990-TRW,A020`, `39990,TRW,A020`;
  start/length `0x4000`/`0x4C000`.
- CR-V: h3 = `39990-TLA-A030`, `39990-TLA-A040`, `39990-TLA,A040`; `0x4000`/`0x6C000`.
- RDX: h3 = `39990-TJB-A010`, `39990-TJB-A030`, `39990-TJB,A030`; **`0xC000`/`0x74000`**.

### 9.2 Why RDX is the donor, not Clarity/Civic/CR-V

| Property | Clarity / Civic / CR-V | RDX TJB-A030 | THR-A020 |
|---|---|---|---|
| Flash window | `0x4000`… | `0xC000` / `0x74000` | **`0xC000` / `0x74000`** (FACT, updater record) |
| Identity records | 6 part-number copies, stride 0x59 (TRW) | `0x5EB00`, 14 × 0x46, hw + sw roles | **`0x5EB00`, 14 × 0x46, hw + sw roles** |
| Checksum slots | `…F80` / `…FFE` of the payload | `0x7FF80` / `0x7FFFE`, B7C8 at `0x7FFFA` | **same addresses and magic** |
| Security constant / algorithm | `01 11 01 12 11 20` | same | **same** (FACT, THR code = TLA code) |
| Payload cipher (from key 01 02 03) | Civic 256-entry table (FACT: fits TRW stock exactly; no +/−/^ formula of 1,2,3 does) | `plain = ((((c+1)&0xFF)^2)−3)&0xFF` | **INFERENCE: RDX formula** (same platform) |

Using the wrong cipher family produces garbage. That was one of the causes of the earlier RDX failures.

### 9.3 Proposed THR container

| Field | Value | Basis |
|---|---|---|
| h0 / h1 / h2 | `00` / empty / `30` | identical across every Honda EPS RWD seen |
| h3 | must include the car's **F181** (expected `39990-THR-A020`). Honda's earlier THR versions are unknown | OPEN: no genuine THR RWD. On the other files, h3 = previous + current version (+ comma forms) |
| h4 | `01 11 01 12 11 20` for every h3 entry | FACT (THR security constant) |
| h5 | `01 02 03` | family precedent. THR's F101 handler takes 3 bytes (FACT); the value is INFERENCE |
| start / length | `0x0000C000` / `0x00074000` | FACT |
| payload | THR `[0xC000, 0x80000)`, **untruncated**, checksum A then C recomputed with seed 0, B7C8 left alone, then encrypted with the RDX transform | FACT (checksums) / INFERENCE (cipher) |
| trailer | LE u32 sum of the file | FACT (format) |

### 9.4 Flasher

Use the EPS flasher flow from the RDX work (`eps-update-rdx.py`). It needs the gregjhogan/sunnypilot opendbc fork
that defines `FLASH_DECRYPTION_KEY` / `ERASE_MEMORY` / `CHECK_PROGRAMMING_DEPENDENCIES`. Sequence:

```
3E → 10 03 → 22 F181 → 27 seed/key → 10 02 → 31 ERASE → 2E FLASH_DECRYPTION_KEY
→ 34 → 36 ×N → 37 → 31 CHECK_PROGRAMMING_DEPENDENCIES
```

Its `validate_fw` must use the BE-u16 slot model (§2.3), not the Civic LE-u32 host check.

### 9.5 The RDX lesson (same platform) — read before flashing

- **What happened.** RDX flashes passed the container check and the full download, then got **NRC 0x72 at
  CHECK_PROGRAMMING_DEPENDENCIES**, with no DTC. The car was running software **A010**; the images carried
  **A030**.
- **Leading explanation:** a hardware/software identity check against the `0x5EB00` table. The check lives in the
  read-protected bootloader, so this is INFERENCE.
- **Unresolved.** It is still not proven what the check reads.

**Rules for THR:**
1. Modify **only the software version the car already reports** (read `22 F181` first; it should be
   `39990-THR-A020`).
2. **Keep all 14 identity records byte-stock.** Never do a global part-number substitution; that collapses the
   hardware (`THR-A010`) and software roles.
3. **No comma part-number marker** in early builds. Test it later, on its own.
4. Keep the full, untruncated payload. Don't touch erased gaps. Write only the real slots.
5. Have a stock-content RWD ready as the recovery image. The bootloader is not rewritten, so an aborted download
   can be retried.

**Before any flash**, verify that the car's flash matches this BIN. A CCP UPLOAD read (§3.2) or a UDS read would
do; mind the remap caveat.

---

## 10. Modification plan, in priority order

Change one thing per build. Normal driving uses banks 1–3, so edit **banks 1, 2 and 3 identically**. Bank 7 matters
only under the `FFF85420` override.

0. **Gate.** Prove the container first:
   - a genuine THR RWD, or a first flash whose content is **unmodified stock** built with this recipe;
   - F181/F191 read from the car;
   - the recovery image ready.
1. **Telemetry-only build.** Stock tables plus a TX message carrying `FFF8029C`, `FFF8005E`, `FFF802E0`,
   `FFF80016`, the E0rate output, s, err, u, `FFF80198` and `FFF82F04`. This settles:
   - the feedback scale and sign;
   - the E0 identity (E0 ≈ k·T or not);
   - the active bank;
   - the ±388 clamp trigger;
   - the real call rates.
2. **Clamps.** P `0x57BD8`, D `0x57BD6`, u `0x57BDA`. This is a pipeline check, not an authority gain. Raise u in
   steps (2048 → 4096 → 8868) rather than all at once.
   - *Or* start with a conservative combined authority build: curve ×1.5 (bank 1 peak 7296, steady u ≈ 1254), P and
     u clamps 2048, D left at 640.
3. **Command curve** `0x57BC0`, in steps (×1.5, ×2, …), staying within 3968 per segment.
4. **Kp `0x57C82` / Kd `0x57C5E`** (×1.4 / ×1.44 per Clarity; how far depends on route A or B).
5. **Tracker-1** `0x57BD2` 410 → 656 (banks 1–3), only if telemetry shows lag or oscillation. Never change it in
   the same build as a G/H change.
6. **Feedback-scale code patch** (route A, NORM equivalent at `0x726FE`), if the curve hits the 16-bit limit first.
7. **Feedforward** (code), if telemetry shows a steady tracking error.
8. **G/H stretch within 0–320** (the A280 equivalent).
9. **Minimum engage speed** `0x57B00` → 0. This is a behaviour change: engage from standstill.
10. **P pocket** (code), only if the same windup shows up.
11. **Part-number comma marker.** Optional, on its own, and last.

**Do not touch:**
- the override fade `FUN_00073D20` and its 768 cut;
- E/F;
- the tracker-2 coefficient and clamp (`0x57B4E` / `0x57B50`);
- the E4 monitors;
- `0x57B06` (8868 engage threshold) and `0x57C94` (8868 total clamp);
- bank 8;
- the identity table.

---

## 11. Open items

1. The producer and units of the `FFF80000–FFF802EB` block (`FFF8029C`, `FFF802E0`, `FFF80198`, `FFF80016`). The
   telemetry build is the practical way to close this.
2. The THR RWD h3 version list and the THR cipher. Only a genuine THR RWD, or a successful stock-content flash,
   closes these.
3. Whether the NRC 0x72 dependency check applies on THR, and what it reads.
4. What sets `FFF85420` (the mode-7 override); which profile key the car uses; bank 8.
5. The ±388 hand-off clamp trigger (`@r12 & 0x200`).
6. Absolute timing. The chain above is inferred from a 100 Hz `0x18F` rate.
7. The consumer of `FFF83076` (u·4011≫10) and of W / `FFF830C6` in `0x70000–0x71FFF`.
8. The motor-side path after `FFF83484` / `FFF85422`.

---

## 12. Superseded statements in older notes

If you've read earlier THR notes, these points are now known to be wrong:

- "`0x57B52` = 3." It is **768** (`03 00` big-endian).
- "Calibration index `FFF82F04` is always 0." Banks exist; see §2.2.
- "`FFF86F24` ≠ 0 enters the controller." It is a self-toggle that alternates the controller and the output mixer.
- "`FUN_000742C0` filters an E4-derived value." Its input is `FFF8029C`.
- "DMA3 targets `FFF85554`." It targets `FFF85564`.
- "`0x156` is sent by the EPS." On THR it is received; the EPS sends `0x18F` / `0x1AB`.
- "The tracker-1 gain is 410 in every bank." Banks 4–7 are 30110.
- "TLA/Clarity cipher or offsets can be used for THR." They can't; THR is the RDX-platform layout.
- "Timing 726DA 2 kHz / 7276A 1 kHz." Once the self-toggle is accounted for, the leading model is 1 kHz / 500 Hz.
