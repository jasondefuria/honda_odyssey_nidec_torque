# Extended offline zero-speed experiment

Real dispatcher 72A44 and ramp 73852 with synthetic RAM and call cadence; only bank1 minimum changed in memory. No full boot, peripherals, monitor production or physical plant. Bank changes directly inject selector, without running a bank selection policy.

24 directed scenarios completed without interpreter errors. This is observed behavior, not a blanket safety pass. Prior isolated tests covered 384 engagement inputs and 16 follow-up cases.

| Variant | Test | Bank/speed | Observed result |
|---|---|---|---|
| baseline | engage_release | 1 / 0 | `{'state': 1, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}` |
| baseline | engage_release | 1 / 10 | `{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}` |
| baseline | engage_release | 2 / 0 | `{'state': 1, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}` |
| baseline | engage_release | 2 / 10 | `{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}` |
| baseline | engage_release | 7 / 0 | `{'state': 1, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}` |
| baseline | engage_release | 7 / 70 | `{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}` |
| baseline | system |  / 10 | `[{'state': 4, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}]` |
| baseline | monitor3 |  / 10 | `[{'state': 4, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}]` |
| baseline | inhibit |  / 10 | `[{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}, {'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}, {'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}, {'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}]` |
| baseline | config_off |  / 10 | `[{'state': 3, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 3, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 3, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 3, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}]` |
| baseline | synthetic_bank_switch | 2 / 10 | `{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}` |
| baseline | synthetic_bank_switch | 7 / 10 | `{'state': 2, 'path': 2, 'R': 16320, 'W': 16320, 'marker': 0}` |
| bank1_zero_only | engage_release | 1 / 0 | `{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}` |
| bank1_zero_only | engage_release | 1 / 10 | `{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}` |
| bank1_zero_only | engage_release | 2 / 0 | `{'state': 1, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}` |
| bank1_zero_only | engage_release | 2 / 10 | `{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}` |
| bank1_zero_only | engage_release | 7 / 0 | `{'state': 1, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}` |
| bank1_zero_only | engage_release | 7 / 70 | `{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}` |
| bank1_zero_only | system |  / 0 | `[{'state': 4, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}]` |
| bank1_zero_only | monitor3 |  / 0 | `[{'state': 4, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 5, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}]` |
| bank1_zero_only | inhibit |  / 0 | `[{'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}, {'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}, {'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}, {'state': 3, 'path': 0, 'R': 16384, 'W': 16384, 'marker': 0}]` |
| bank1_zero_only | config_off |  / 0 | `[{'state': 3, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 3, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 3, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}, {'state': 3, 'path': 0, 'R': 0, 'W': 0, 'marker': 0}]` |
| bank1_zero_only | synthetic_bank_switch | 2 / 0 | `{'state': 2, 'path': 2, 'R': 16320, 'W': 16320, 'marker': 0}` |
| bank1_zero_only | synthetic_bank_switch | 7 / 0 | `{'state': 2, 'path': 2, 'R': 16320, 'W': 16320, 'marker': 0}` |

## Conclusions and limits

The bank-1 zero-threshold variant reaches ACTIVE with R=W=16384 at zero speed, without a standstill marker. Full authority is reached after 1024 ramp updates; ACTIVE is observed on the subsequent dispatcher iteration. Request removal returns every engaged test to IDLE with zero authority after the allotted 1030 calls. These are call counts, not measured ECU timing.

The zero-speed variant was fault-tested at speed zero; baseline fault tests used speed 10. System-fault and injected monitor-severity-3 fields produce ABORT with zero authority, then LOCKOUT. Configuration disable zeros authority while the state remains ACTIVE in this isolated model. Command-inhibit alone leaves the authority ramp unchanged; downstream command/fade behavior was not tested here, so this does not prove torque remains applied or that inhibition fails.

The variant’s synthetic switch from bank 1 to bank 2 or 7 at speed zero initiates ramp-out. Baseline bank 1 to bank 2 at speed 10 remains active; baseline bank 1 to bank 7 at speed 10 initiates ramp-out. The real bank-selection logic and reinitialization policy were not executed.

No full ECU boot, peripherals, live CAN decoding, monitor generation/debounce, motor plant, physical torque, or closed-loop stability is included. Fault fields are injected directly. The experiment does not resolve U3000-49. Input ROM is the previously tested R2 base, with the threshold change only in host memory; published mod25xv2 identity/container packaging is not exercised. No patched BIN or RWD was saved and no vehicle connection was used.
