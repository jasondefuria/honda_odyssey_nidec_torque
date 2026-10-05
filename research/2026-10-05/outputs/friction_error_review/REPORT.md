# Friction-error sensitivity at approximately 40 mph

Route 28, 429.65–439.65 s; 996 eligible samples. Frozen recorded trajectory; no closed-loop prediction and no settings changed.

The learned friction is approximately 0.1391, with a compensation transition threshold of 0.2 m/s². With multiplier A=1, the unsaturated error-compensation slope is approximately 0.696 normalized command per m/s². The main P correction has median effective slope 0.976 in the same units. Thus this nominally feedforward friction term adds approximately 71% of the P correction’s local slope, or about 42% of the combined P-plus-friction-error slope. These are local unsaturated slopes, not fractions of total steering output or universal gains.

Acceleration error ranges from -0.1041 to +0.0702 m/s². Compensation remains unsaturated. Jerk is zero on 986/996 samples. This supports examining the error-driven contribution separately from the direct jerk term.

| Error multiplier | Command-band RMS | Reduction vs 1.0 | Maximum command change |
|---|---:|---:|---:|
| 1.00 | 0.05173 | 0.0% | 0.00000 |
| 0.85 | 0.04925 | 4.8% | 0.01086 |
| 0.70 | 0.04680 | 9.5% | 0.02172 |
| 0.50 | 0.04358 | 15.8% | 0.03619 |
| 0.00 | 0.03589 | 30.6% | 0.07239 |

Band is 0.3–2 Hz after linear detrending. The command variants subtract only the change in reconstructed friction compensation from the original logged command, preserving the small original replay residual and all other contributions. No integrator, planner, physical response, or future error is recomputed. Lower command-band RMS here is a sensitivity result, not proof of better ride quality, damping or safety. Zero is an analytical ablation, not a proposed tune.

## Code finding

The exact revision initializes lat_accel_friction_factor to 0.7. update_calculations sets the stored member to 1.0 when lookahead_lateral_jerk equals zero, with no restoring assignment in this update path. Thus changing only the constructor value would not reliably change this window. Whether that persistent behavior is intentional has not been established.

## Interpretation

The friction-error term is substantial and acts like extra proportional correction here. Keeping an error multiplier of 0.7 in this recorded window would reduce combined command-band RMS by roughly 9.5%, not eliminate the oscillation. More reduction in the model is not automatically better: real steering response and tracking would change. This evidence prioritizes an explicit, independently controlled friction-error multiplier for further offline and controlled validation, rather than blindly lowering KI or total learned friction. Reducing the total friction parameter would also alter its maximum compensation and the jerk contribution.

The retained delay, changing requested path, model-derived actual acceleration and exact process scheduling remain limitations. This analysis does not identify the sole cause of the reported oscillation.
