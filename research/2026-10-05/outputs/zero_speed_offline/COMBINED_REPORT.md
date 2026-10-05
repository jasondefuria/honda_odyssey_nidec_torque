# Combined zero-speed offline tests

Synthetic speed=0, bank1 baseline versus in-memory minimum zero. Dispatcher/ramp + preprocessing/fade/PD/mixer + four consistency monitors and aggregation. Zero feedback/base assist. No full boot, CAN parsing, hardware, actual bank-selection policy or motor plant. Injected flags do not test fault detection generation.

Completed 26 directed scenarios and 8384 combined ticks. No consistency-monitor mismatches were observed in the monitored snapshot bytes or aggregation output. This is not a full ECU validation or a safety pass.

## Zero-threshold variant observations

| Scenario | Sampled mixer output (internal counts) |
|---|---|
| engagement | 2, 4, 6, 204, 1038, 2090, 2090, 2090 |
| inhibit | -640, 0, 0, 0, 0, 0, 0, 0 |
| driver767 | -7, 52, 52, 52, 52, 52, 52, 52 |
| driver768 | -57, 0, 0, 0, 0, 0, 0, 0 |
| driver_negative768 | -57, 0, 0, 0, 0, 0, 0, 0 |
| system_fault | 0, 0, 2, 4, 6, 8, 10, 12 |
| monitor3 | 0, 0, 0, 0, 0, 0, 0, 0 |
| config_off | 0, 0, 0, 0, 0, 0, 0, 0 |
| request_off | 2070, 2068, 2066, 2081, 2062, 2060, 2058, 2073, 0 |
| bank2 | 2070, 2068, 2066, 2081, 2062, 2060, 2058, 2073, 0 |
| bank7 | -26, 605, 605, 609, 604, 603, 602, 607, 0 |
| reverse_command | -2560, -2090, -2090, -2090, -2090, -2090, -2090, -2090 |
| zero_command | -640, 0, 0, 0, 0, 0, 0, 0 |

Engagement samples are ticks 0, 1, 2, 100, 512, 1023, 1024 and 1029. For other tests the first eight calls and final call are saved (final is not duplicated for eight-call tests). Mixer counts are not physical torque measurements.

## Findings

- With no standstill permit, the unchanged baseline stays idle at speed zero and its tested mixer outputs remain zero. The zero-threshold variant ramps to 2090 internal mixer counts under maximum positive command and synthetic zero feedback/base assist.
- Request removal and injected bank-selector transitions to banks 2 and 7 ramp down to zero by the final sampled call. Bank selection was injected; actual bank-policy and reinitialization logic were not executed.
- Inhibit and zero-command steps produce a one-call -640-count transient, then zero. Driver input at either +768 or -768 produces a one-call -57-count transient, then zero. These are observations with retained controller history, not instantaneous zero-output proofs.
- Configuration disable and the injected severity-3 monitor yield zero mixer output in all eight recorded calls. Configuration disable may leave a nonzero intermediate controller result, which is suppressed at the mixer by zero authority.
- The one-shot system-fault-summary injection cuts output initially but then allows re-engagement. That summary is not held as a persistent input and can be recomputed by the called firmware. Underlying fault-producing records and diagnostics were not modeled. This case therefore does not establish persistent system-fault containment, nor prove that a real persistent fault would re-engage.
- A sign reversal produces -2560 on the first call, then -2090. Abrupt command changes and derivative history matter.

## Scope limits

This combines manually sequenced actual ROM routines for dispatch/ramp, preprocessing, driver fade, PD, mixer, four consistency checks and aggregation. It is not the whole scheduled ECU application: no full boot, interrupts, CAN parsing, sensor acquisition, independent monitor production, final motor/current control or physical plant. Calling order/cadence is a harness choice. Clean synthetic RAM and zero feedback/base assist are supplied. A zero threshold is changed only in host memory, without recalculating ROM checksums because boot checksum routines are not exercised. No patched ROM/RWD is emitted, and no vehicle or GitHub access occurs. The existing firmware file is unchanged.

The prior statement that all injected faults produce sustained zero output was too broad: the combined one-shot system-summary test demonstrates why underlying fault sources and their lifecycle must be modeled before drawing that conclusion. U3000-49 remains outside the validated scope.
