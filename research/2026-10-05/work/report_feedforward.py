from pathlib import Path
import numpy as np,json,os
os.environ['MPLCONFIGDIR']='/tmp/tor-matplotlib'
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path('outputs/feedforward_replay');a=np.load(O/'replay.npz');m=a['window'];t=a['t'][m];grid=np.arange(t[0],t[-1],.02)
def band(y):
 x=np.interp(grid,t,y[m]);x-=np.polyval(np.polyfit(grid-grid[0],x,1),grid-grid[0]);f=np.fft.rfftfreq(len(x),.02);s=np.fft.rfft(x);return float(np.std(np.fft.irfft(s*((f>=.3)&(f<=2)),n=len(x))))
r=json.loads((O/'summary.json').read_text());r['window_components']={k:{'band_rms':band(a[k]),'min':float(a[k][m].min()),'max':float(a[k][m].max())} for k in ['nominal','friction_without_jerk','jerk_increment','logged','replayed']};r['no_jerk_command_delta_max']=float(abs(a['jerk_increment'][m]).max());r['window_fraction_residual_below_1e_4']=float(np.mean(abs(a['replayed'][m]-a['logged'][m])<1e-4));(O/'summary.json').write_text(json.dumps(r,indent=2));print(json.dumps(r['window_components'],indent=2));print('max jerk',r['no_jerk_command_delta_max'])
fig,axs=plt.subplots(3,1,figsize=(12,9),sharex=True)
axs[0].plot(t,a['logged'][m],label='Logged feedforward');axs[0].plot(t,a['replayed'][m],'--',label='Replayed');axs[0].set_ylabel('Normalized feedforward')
for k,label in [('nominal','Nominal demand incl. roll'),('friction_without_jerk','Error-based friction'),('jerk_increment','Marginal jerk contribution')]:axs[1].plot(t,a[k][m],label=label)
axs[1].set_ylabel('Feedforward components');axs[2].plot(t,a['desired'][m]-a['actual'][m],label='Lateral-acceleration error');axs[2].plot(t,a['lookahead_jerk'][m],label='Look-ahead jerk');axs[2].set_ylabel('m/s² or m/s³');axs[2].set_xlabel('Seconds from first carState')
for ax in axs:ax.grid(alpha=.3);ax.legend()
fig.tight_layout();fig.savefig(O/'feedforward_components.png',dpi=140)
(O/'REPORT.md').write_text(f'''# Feedforward replay: 40 mph window

Route 00000028--c139047a03, 429.65–439.65 s. No settings, firmware or vehicle interaction changed.

## Method

Reconstructed nominal feedforward and nonlinear friction compensation using the exact recorded application revision 580e0fe and its opendbc submodule 1fe4521373494ae56c9870761914214a45029051. Used recorded desired/actual acceleration, causal latest roll/torque-parameter/model/carState messages, and the traced 0.29064885 s look-ahead delay. This is a formula replay, not the original processes with exact message-consumption scheduling.

Nominal = (desired acceleration − 9.81 × roll) / learned factor.
Combined compensation = learned friction × clip((A × acceleration error + 0.4 × look-ahead jerk) / 0.2, −1, 1).
A is initialized to 0.7, but the stateful code sets it to 1.0 when look-ahead jerk is zero and does not restore it in this update path. Replaying from route start yielded A=1.0 throughout the qualified active samples.

Friction and jerk enter one saturating function, so they are not independent additive physical quantities. Here, 'error-based friction' is the function evaluated with jerk set to zero; 'jerk contribution' is the difference between full and zero-jerk compensation. This allocation reproduces their combined value but is a marginal attribution, not a separate motor force measurement. The learned offset is not applied by this exact extension's linear nominal conversion; roll is included.

## Agreement

Target window: 996 eligible samples. Absolute feedforward residual mean 0.0001163, P95 0.00000118, maximum 0.01079 normalized command units. Across 67,989 eligible active samples, mean 0.0001809 and maximum 0.14521. Outliers remain unaccounted for; asynchronous publication/consumption is one possible explanation, not established. This is not bit-exact replay.

## Findings

Look-ahead jerk is nonzero for only 1.00% of the target window. Compensation never saturates there. Band-limited RMS (0.3–2 Hz):

| Component | RMS normalized command |
|---|---:|
| Nominal | {r['window_components']['nominal']['band_rms']:.6f} |
| Error-based friction | {r['window_components']['friction_without_jerk']['band_rms']:.6f} |
| Marginal jerk contribution | {r['window_components']['jerk_increment']['band_rms']:.6f} |
| Logged total feedforward | {r['window_components']['logged']['band_rms']:.6f} |

These correlated RMS quantities cannot be summed as independent powers. The result does not support blaming a large direct jerk contribution for the 1.3 Hz correction activity in this window. Error-based friction acts like additional proportional correction near zero error because it is unsaturated here. It combines with the main P correction and changing nominal demand.

## Tuning implications

The better-targeted next sensitivity study is the acceleration-error contribution inside friction compensation, including the persistent 1.0 multiplier, while holding other settings fixed. Simply disabling the entire jerk-aware extension would change more than the jerk term, so it would not isolate this finding. No numerical gain change is validated here. Changing a replayed command while holding actual vehicle motion fixed cannot predict closed-loop stability. The existing learned delay is still a separate uncertainty.

See replay.npz, summary.json, feedforward_components.png, and archived source. No firmware or tuning changes made.
''')
for name in ['interfaces','friction','lateral','honda','constants']:
 p=Path('/tmp/replay_'+name+'.py')
 if p.exists():(O/(name+'_source.py.txt')).write_bytes(p.read_bytes())
