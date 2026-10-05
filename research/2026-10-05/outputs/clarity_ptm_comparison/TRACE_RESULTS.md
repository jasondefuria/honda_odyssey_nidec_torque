# Extended Clarity trace results

Read PHYSICAL_SIGNAL_MAP.md and SIGNAL_TRACE.md together with feedback_trace.txt, sensor_trace.txt, setup_trace.txt, and deep_trace.txt. All firmware inputs remained unchanged.

Confirmed additional results:
- Complete computational feedback chain from conditioned sample ingestion through adaptive difference estimation, normalization, first-order tracker, and feedback clamp.
- Tracker3200 is a Q15 first-order coefficient, replacing1999; it is not a maximum torque clamp.
- The normalization1650 scales the feedback estimate, replacing3429.
- Seventh-row override confirmed at2AD2E.
- Runtime mode-dependent pointer copying exists; full state binding remains unresolved.

Not complete: physical sensor identity/units, CAN origin, period, all runtime pointer bindings, and actuator/current conversion. Static tracing should continue from34EFE's upstream producer, the2AD2E callers, and controller initialization. A complete physical calibration additionally needs hardware or measurement evidence. No claim of complete physical verification or port readiness is made.
