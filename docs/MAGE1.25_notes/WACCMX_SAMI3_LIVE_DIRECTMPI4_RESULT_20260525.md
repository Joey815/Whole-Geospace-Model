# WACCM-X/SAMI3 Live Neutral + Direct Voltron Phi 4-Frame Result - 2026-05-25

## Result

The four-frame integrated online smoke completed successfully:

```text
jobid = 7668967
jobname = wxsami3_dm4t1
state = COMPLETED
exit = 0:0
elapsed = 00:10:06
node = qhcn182
batch MaxRSS = 63607068K
archive = logs/waccmx_live_directmpi4_tphi1_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

Runtime parameters:

```text
SAMI3_MAXSTEP = 80
SAMI3_HRMAX = .070000
SAMI3_TPHI = 1.
VOLTRON_TFIN = 28.0
PHI_MAX_FRAMES = 4
PHI_FRAME_HOUR_OFFSET = 0.0013888889
PHI_VALID_HOURS = 0.0013888889
PAYLOAD_MODE = live
LIVE_DUMP_MAX = 1
MAX_PACKETS = 1
```

This extends the two-frame same-stack smoke by validating four changing
REMIX/Voltron potential frames in the same run as the live WACCM-X/CESM neutral
packet.

## Runtime Chain

The job used one OpenMPI/PRTE DVM:

```text
33 SAMI3 ranks
16 CESM/WACCM-X ranks
1 OpenMPI-enabled serial voltron.x rank
```

CESM/WACCM-X sender:

```text
WXSAMI3 phi payload enabled: F
WXSAMI3 sent live neutral packet: nstep=0 packet_hour=0 count=0
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

Voltron direct phi sender:

```text
WACCMX_SAMI3_PHI_DIRECT sent frame=0 nframes=4 hour=0          valid_until=0.0013888889
WACCMX_SAMI3_PHI_DIRECT sent frame=1 nframes=4 hour=0.00138889 valid_until=0.0027777778
WACCMX_SAMI3_PHI_DIRECT sent frame=2 nframes=4 hour=0.00277778 valid_until=0.0041666669
WACCMX_SAMI3_PHI_DIRECT sent frame=3 nframes=4 hour=0.00416667 valid_until=1.0e30
WACCMX_SAMI3_PHI_DIRECT sent done=4
```

SAMI3 receiver:

```text
WACCMX_PHI_RECV frame 0 of 4, hrut=0.00000000, hour=0.00000000, valid_until=0.0013888889
WACCMX_PHI_RECV frame 1 of 4, hrut=0.00222222, hour=0.00138889, valid_until=0.0027777778
WACCMX_PHI_RECV frame 2 of 4, hrut=0.00304196, hour=0.00277778, valid_until=0.0041666669
WACCMX_PHI_RECV frame 3 of 4, hrut=0.00468144, hour=0.00416667, valid_until=1.0e30
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 4
```

## Validation

All standard validators passed:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

The time-axis gate confirmed:

```text
sender_neutral_packet_count = 1
receiver_neutral_packet_count = 1
receiver_worker_coverage = 32 workers
phi_payload_frame_count = 4
phi_payload_hours_strictly_increasing = ok
receiver_phi_frame_count = 4
receiver_phi_records_within_validity = ok
```

Neutral replay/QC:

```text
WACCMX_RECV_QC compare ok:
  ranks = 32
  occurrence = 0
  step_set = [0]
  packet_hour_set = [0.0]
  max_abs = 2.08794e+06
  max_rel = 4.83248e-13
```

Phi payload contract:

```text
size = 194068 bytes
header = [20260524, 1, 125, 97, 4]
frame0 min/max = -36.972878, 31.504816
frame1 min/max = -37.706364, 31.759037
frame2 min/max = -38.223293, 32.193001
frame3 min/max = -37.708565, 31.654135
frame1_minus_frame0_max_abs = 3.4961066
frame2_minus_frame1_max_abs = 2.5031015
frame3_minus_frame2_max_abs = 2.3759155
```

## Cadence Finding

Two intermediate four-frame attempts isolated the cadence issue:

```text
jobid = 7668732
SAMI3_TPHI = 7.
PHI_VALID_HOURS = 0.003
result = FAILED only at validate_wxsami3_time_axis
reason = frame 1/2 were pulled after their valid_until windows

jobid = 7668869
SAMI3_TPHI = 7.
PHI_VALID_HOURS = 0.006
result = FAILED only at validate_wxsami3_time_axis
reason = increasing validity delayed subsequent reads; Voltron frames remained 5 s apart
```

The root cause is not direct MPI transport.  SAMI3 calls `potpphi` when
`tpot >= tphi`; with `tphi=7.` the actual phi-read cadence is slower than the
5 second Voltron direct-phi frame cadence.  Restoring `SAMI3_TPHI=1.` makes
SAMI3 poll often enough to consume each five-second frame before expiration.

## Interpretation

This closes the current four-frame online control-path gate:

```text
WACCM-X/CESM live neutral from CAM phys_state(:)
OpenMPI Voltron runtime phi through direct MPI
SAMI3 online neutral receiver
SAMI3 direct phi receiver
four changing potential frames
time-axis validation across neutral and phi streams
```

The path is still a prototype physics coupling.  It still uses:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 1
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 1
```

The next production-facing step is to replace the smoke final-frame stop/cache
policy with a continued cadence policy, then move from one live neutral packet
to multiple neutral packets synchronized with the direct Voltron phi stream.
