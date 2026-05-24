# WACCM-X/SAMI3 Voltron Phi Append Writer Two-Frame Result

Date: 2026-05-25

## Goal

Replace the prior two-frame smoke's Python duplicate-frame repack with a real
append-capable Voltron/REMIX writer:

```text
Voltron/REMIX time advance
  -> waccmx_stub_backend.F90 captures APEX POT
  -> writes/appends SAMI3 MPI phi payload frames
```

This validates the payload writer itself before the queued full
WACCM-X sender -> SAMI3 receiver end-to-end append2 run.

## Code Change

Updated:

```text
code/kaiju_sami3_moments/src/remix/waccmx_stub_backend.F90
```

`write_sami3_phi_payload` now:

```text
1. Creates a stream payload header with nframes=0 if the file does not exist.
2. Reopens existing payloads in readwrite mode.
3. Validates magic/version/dimensions before appending.
4. Uses the current header nframes as frame_index.
5. Appends frame_index, [frame_hour, valid_until], and phi_statv.
6. Updates header nframes in place.
```

New optional writer controls:

```text
WACCMX_SAMI3_PHI_VALID_HOURS
WACCMX_SAMI3_PHI_MAX_FRAMES
WACCMX_SAMI3_PHI_FINAL_VALID_UNTIL_HOUR
```

## Build

Built in the copied Kaiju tree, not the original checkout:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_phi_append_20260525/bin/voltron.x
```

The previous smoke executable remains available:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/bin/voltron.x
```

## Smoke Run

Launcher:

```text
slurm/run_voltron_phi_append_writer_2frame_20260525.sbatch
```

Slurm:

```text
jobid: 7659655
state: COMPLETED
exit: 0:0
elapsed: 00:01:06
node: qhcn118
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/voltron_phi_append_writer_2frame_20260525_0000
```

Archived evidence:

```text
logs/voltron_phi_append_writer_2frame_20260525/
```

## Payload Result

Payload:

```text
remix_sami3_phi_payload_append_writer_2frame.bin
```

Summary:

```text
size=97044
header=[20260524, 1, 125, 97, 2]
frame=0 frame_index=0 hour=0.0013888889 valid_until=0.0027777778 min=-36.930614 max=31.483816 finite=True nonzero=3492
frame=1 frame_index=1 hour=0.0027777778 valid_until=1e+30 min=-37.683018 max=31.891191 finite=True nonzero=3492
frame1_minus_frame0_max_abs=3.5858946
frame1_minus_frame0_rms=0.68732566
```

Interpretation:

```text
1. The payload contains two frames written by the Voltron/REMIX runtime writer.
2. The frame hours come from Voltron model time, not from a fixed override.
3. The second frame is not a duplicate of the first frame.
4. The final frame uses the configured sentinel valid_until=1e30.
```

## Remaining End-To-End Check

The full integrated smoke is queued as:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525.sbatch
jobid: 7659629
```

That queued run should verify:

```text
Voltron real append2 payload
  -> CESM/WACCM-X sender phi append
  -> SAMI3 WACCMX_PHI_RECV receives both frames
  -> SAMI3 switches frames by hrut/hrutw2 gate
  -> live neutral receiver QC remains clean
```
