# 40 mph delay and command trace

Route 00000028--c139047a03, 429.65–439.65 seconds after first carState. Source revision 580e0fe584f82ba8726f1d0331249b25c4bfb55a. Read-only analysis; no settings changed.

## Delay

controlsd.py:159 passes lateralDelay.lateralDelay + LAT_SMOOTH_SECONDS to LaC.update. modeld.py uses the same expression for planning. LAT_SMOOTH_SECONDS is 0.0 in this revision. The recorded lateralDelay is 0.29064885 s. The extension separately receives self.lat_delay from get_lat_delay; initData has LagdToggle=1, so it also selects the published live delay. LagdValueCache is 0.29064885, so either branch would initially agree. The 0.10 s CarParams delay is not the direct value used by these control/planning expressions. The source trail and recorded values establish the initial selection; parameter changes after startup are not independently audited here.

## Logged command decomposition

In this window output = -(P+I+feedforward), with maximum raw-sample residual 3.08e-8. This confirms the logged terms can reconstruct the command here despite the extension updating the controller output. Torque-control version 0 and the jerk-aware extension are active. The extension uses the controller PID passed into its update, including the speed-dependent proportional schedule; the extension constructor's fixed initial PID constants alone do not establish final active gains.

Over the detrended 0.3–2 Hz band, normalized-command RMS contributions are P 0.02495, I 0.00210, feedforward 0.02982; combined command 0.05155. Contributions are correlated and must not be summed as independent power fractions. Both negative-P and negative-feedforward track command swings strongly (correlations 0.913 and 0.948). I is comparatively steady, approximately 0.241–0.259. A steady integral offset is not proof of windup.

The 1.3 Hz figure is the strongest tracking-error frequency in this short window within the selected band, not a proved vehicle natural frequency. Desired acceleration is also varying. Measured/model-derived actual acceleration has band RMS 0.03574 vs desired 0.02736 m/s². These observations are consistent with response overshoot but cannot isolate road/planner/feedback causation.

## Tuning implication

Rapid correction activity is associated with both P and feedforward, not primarily a rapidly oscillating integral term. Reducing KI alone is therefore not the best-supported first experiment. Raising torque limits is not supported: commands peak around 21% here. Blindly setting delay to 0.10 s is also unsupported.

The next discriminating analysis is an offline replay of the exact jerk-aware feedforward calculation, separating nominal lateral-acceleration feedforward from friction/jerk contributions while holding the recorded trajectory fixed, followed by delay-estimator review. The current log's f term combines those pieces; it does not label them separately. Such replay can test command sensitivity but cannot simulate the physical response to new commands without a validated plant. No numeric gain changes or claims of stability validation are made.

Files: 40mph_terms.json, 40mph_decomposition.png, and archived source excerpts.
