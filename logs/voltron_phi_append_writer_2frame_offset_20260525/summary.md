# Voltron Phi Append Writer Two-Frame Offset Smoke

- Date: 2026-05-25
- Job: 7659705
- State: COMPLETED, exit 0:0
- Launcher: `slurm/run_voltron_phi_append_writer_2frame_20260525.sbatch`
- Executable: `/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_phi_append_20260525/bin/voltron.x`
- Time offset: `WACCMX_SAMI3_PHI_FRAME_HOUR_OFFSET=0.0013888889`

Result:

```text
header=[20260524, 1, 125, 97, 2]
size=97044
frame=0 hour=0 valid_until=0.0013888889 min=-36.930614 max=31.483816
frame=1 hour=0.0013888889 valid_until=1e+30 min=-37.683018 max=31.891191
frame1_minus_frame0_max_abs=3.5858946
frame1_minus_frame0_rms=0.68732566
```

Conclusion:

```text
The append-capable Voltron/REMIX writer now produces a two-frame SAMI3 MPI phi
payload whose first valid interval starts at hrut=0. This avoids an initial
SAMI3 time-gating gap while preserving real Voltron frame-to-frame evolution.
```
