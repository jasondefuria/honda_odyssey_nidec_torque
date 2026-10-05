# Oscillation-focused development analysis

Scope: downloaded October 4 routes 23, 24 and 28; no new drive was fetched for this analysis. User reports oscillation. No device settings, controller code or firmware changed.

## Recorded controller and settings

The exact logged commit is 580e0fe584f82ba8726f1d0331249b25c4bfb55a. The torqueState version is 0, matching the legacy torque controller in sunnypilot/selfdrive/controls/lib/latcontrol_torque_v0.py. This is not the Honda angle-PID tune using kpV/kiV. Its base source has a speed-dependent P schedule, KI 0.3 and KD 0; the jerk-aware extension recalculates output in torque space. Do not infer final applied gains solely from these constants or use the logged P/I as a complete decomposition of that final output.

Startup parameters on all three drives: LateralJerkTorqueController=1; NeuralNetworkLateralControl=0; TorqueParamsOverrideEnabled=0; LiveTorqueParamsToggle=1. Stored manual factor 2.5 and friction 0.1 are not active overrides. The existence of an Odyssey NN model in carParamsSP does not mean NNLC was enabled.

LateralDelay messages report 0.29064885 s, status estimated, 23 valid blocks, with identical first/last values on all three drives. This suggests retained delay calibration rather than a newly established post-flash estimate. Configured steerActuatorDelay is 0.10 s. The exact final delay supplied to control was not traced in this analysis; do not substitute one for the other. Zero reported estimate standard deviation is not evidence of zero real-world uncertainty.

Torque learning also starts at 100%; the modified route ends at factor 1.90573, friction 0.14115, offset -0.26509. These are model parameters, not motor torque measurements.

## Oscillation screening

84 overlapping 10-second windows across the three drives passed continuous active/valid/no-intervention/no-fault filtering at >=10 m/s. Windows step by five seconds and are not independent samples. Signals were interpolated at 50 Hz, linearly detrended, and screened for 0.3–2 Hz error activity. This band selection can include ordinary curve transitions and excludes slower/faster oscillation. It is a screening method, not an instability detector.

The three largest qualifying modified-route windows are plotted in largest_latest_windows.png. Times are relative to first carState:

- Around 570–580 s, 27.9 mph: a curve transition dominates. Actual lateral acceleration exceeds the requested magnitude near the end; this does not look like a clean sustained periodic oscillation.
- Around 430–440 s, 39.7 mph: repeated steering-command corrections and small actual-response overshoots are visible. Requested acceleration also changes repeatedly; driver-independent closed-loop instability is not established.
- Around 245–255 s, 37.5 mph: repeated command reversals at low lateral acceleration. Again, the request is not constant.

These windows show corrections well below maximum command, so raising the torque limit is not a supported response to the reported oscillation. Logged actual lateral acceleration is derived from steering/vehicle-model signals, not an independent accelerometer reference. Angle quantization contributes to step-like traces.

The modified drive has lower overall tracking error than the two morning drives, but mean error does not capture comfort or prove damping. Road geometry, requests and operating conditions differ. No safe new gain or physical torque multiplier was identified.

## Tuning priorities

1. Keep the firmware fixed while investigating this symptom. Changing curve shape, gains and delay together would prevent attribution.
2. Verify which delay is actually consumed by the controller and planner, and compare its estimate quality under the current EPS response. Do not blindly replace 0.291 s with 0.10 s or interpret unchanged learned values as fresh calibration.
3. Review jerk-aware/friction feedforward around the repeated corrections. Its enabled state is confirmed, making it a useful target for an offline controller replay with one component changed at a time. A replay using the original measured trajectory can compare commands, but cannot prove how the physical vehicle would respond to different commands.
4. If repeated error sign reversals persist under a steady requested path, evaluate damping/gain changes in the active torque-controller branch, not the dormant Honda angle-PID kpV/kiV block. No numeric replacement gains are justified by this dataset alone.
5. Obtain the approximate time and speed at which the driver felt oscillation to align the subjective symptom with these candidate windows. Existing screening excludes lower-speed and driver-intervention periods and therefore cannot rule out symptoms there.

Evidence: settings.json, windows.json, archived exact-revision source excerpts and largest_latest_windows.png. Source https://github.com/jasondefuria/openpilot/tree/580e0fe584f82ba8726f1d0331249b25c4bfb55a/openpilot/sunnypilot/selfdrive/controls/lib
