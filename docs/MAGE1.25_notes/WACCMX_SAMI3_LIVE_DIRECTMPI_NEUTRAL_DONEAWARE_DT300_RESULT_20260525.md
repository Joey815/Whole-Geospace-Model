# WACCM-X/SAMI3 Direct-MPI Neutral Cadence Result - 2026-05-25

## Result

The direct-MPI WACCM-X/CESM + SAMI3 + Voltron cadence gate completed
successfully:

```text
jobid = 7670231
jobname = wxsami3_ndone
state = COMPLETED
exit = 0:0
elapsed = 00:08:52
node = qhcn119
batch MaxRSS = 64922552K
archive = logs/waccmx_live_directmpi_neutral_doneaware_dt300_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

Runtime parameters:

```text
SAMI3_MAXSTEP = 2
SAMI3_HRMAX = .300000
SAMI3_TPHI = 1.
SAMI3_DT0 = 300.
SAMI3_NEUTRAL_UPDATE_HOURS = 0.08333333333333333
SAMI3_NEUTRAL_SPAN_HOURS = 0.08333333333333333
VOLTRON_TFIN = 20.25
PHI_MAX_FRAMES = 3
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_VALID_HOURS = 0.08333333333333333
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
MAX_PACKETS = 2
LIVE_DUMP_MAX = 2
SEND_EVERY_NSTEPS = 1
CESM_STOP_N = 600
```

This is the first completed run in this goal pass where SAMI3 consumed more
than one live neutral packet while also consuming a multi-frame direct Voltron
phi stream.

## Code Change

Two runtime issues were addressed before this run:

```text
1. SAMI3 neutral update cadence is now configurable through:
   WXSAMI3_NEUTRAL_UPDATE_HOURS
   WXSAMI3_NEUTRAL_SPAN_HOURS

2. The SAMI3 neutral receiver now probes the incoming MPI tag before receiving
   a neutral header. If CESM has already sent the done tag, the worker stores
   the done value and returns instead of blocking or aborting while expecting a
   header.
```

The defaults remain compatible with the previous quarter-hour neutral cadence:

```text
default update_hours = 0.25
default span_hours = update_hours
```

The launcher now exports the cadence controls into the SAMI3 `prun`
environment.

## Runtime Chain

The job used one OpenMPI/PRTE DVM:

```text
33 SAMI3 ranks
16 CESM/WACCM-X ranks
1 OpenMPI-enabled serial voltron.x rank
```

CESM/WACCM-X sender:

```text
WXSAMI3 sent live neutral packet: nstep=0 packet_hour=0.00000000 count=0
WXSAMI3 sent live neutral packet: nstep=1 packet_hour=8.33333358E-02 count=1
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

Voltron direct phi sender:

```text
WACCMX_SAMI3_PHI_DIRECT sent frame=0 nframes=3 hour=0.00000000 valid_until=8.33333358E-02
WACCMX_SAMI3_PHI_DIRECT sent frame=1 nframes=3 hour=8.33333358E-02 valid_until=0.166666672
WACCMX_SAMI3_PHI_DIRECT sent frame=2 nframes=3 hour=0.166666672 valid_until=1.00000002E+30
WACCMX_SAMI3_PHI_DIRECT sent done=3
```

SAMI3 receiver:

```text
WACCMX neutral timing policy: update_hours,span_hours=8.33333358E-02,8.33333358E-02
WACCMX_PHI_RECV frame 0 of 3, hour=0.00000000, valid_until=8.33333358E-02
WACCMX_PHI_RECV frame 1 of 3, hour=8.33333358E-02, valid_until=0.166666672
WACCMX_PHI_RECV frame 2 of 3, hour=0.166666672, valid_until=1.00000002E+30
WACCMX online done signal received during neutral receive: taskid, done_value=2
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 3
```

## Validation

All archived validators returned `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

The time-axis validator confirmed:

```text
receiver_neutral_packet_count = 2
receiver_worker_coverage = 32 workers for packet 0 and packet 1
sender_receiver_neutral_hours_match = matched 2
phi_payload_frame_count = 3
phi_payload_hours_strictly_increasing = ok
phi_payload_covers_neutral_packets = ok
receiver_phi_frame_count = 3
receiver_phi_records_within_validity = ok
```

The strict direct-phi run validator confirmed:

```text
master_done = ok
neutral_done_received = ok
direct_phi_done_received = ok
phi_recv_frame_indices = [0, 1, 2]
phi_sender_sent_frames = 3
phi_sender_sent_done = ok
recv_qc_compare_ok = max_rel=4.83248e-13 for packet 0
```

The live-packet contract validator confirmed packet 1 replay:

```text
packet1_recv_compare_ok = true
packet1_recv_compare_ranks = 32
packet1_recv_compare_occurrence = 1
packet1_recv_compare_max_rel = 6.76502e-13
sender_live_packet_count = 2
receiver_qc_line_count = 64
sami3_done = true
waccmx_done = true
fatal_markers_absent = true
```

Phi payload summary:

```text
header = [20260524, 1, 125, 97, 3]
frame0 hour = 0.0        min/max = -36.972878, 31.504816
frame1 hour = 0.08333336 min/max = -37.706364, 31.759037
frame2 hour = 0.16666667 min/max = -38.223293, 32.193001
frame1_minus_frame0_max_abs = 3.4961066
frame2_minus_frame1_max_abs = 2.5031015
```

## Comparison With Previous Attempt

The preceding diagnostic run:

```text
jobid = 7670132
jobname = wxsami3_ns300
state = CANCELLED by user
elapsed = 00:10:54
```

already proved the cadence fix was effective:

```text
packet 0 received by 32 workers
packet 1 received by 32 workers
three phi frames received
no time-step-too-small abort
```

It was intentionally canceled before completion because the receive/finalize
ordering could still strand workers if a done tag arrived while a neutral
header was expected. Job `7670231` closes that hole with the done-aware probe
path and reaches clean shutdown.

## Interpretation

This closes the current online-control cadence gate:

```text
WACCM-X/CAM live neutral payload from phys_state(:)
two runtime neutral packets at the 300 s CESM cadence
SAMI3 online neutral receiver with configurable cadence
direct Voltron/REMIX phi stream with three changing frames
done-aware neutral receive/finalize ordering
full validator pass and clean shutdown
```

This is still a validated prototype physics path. It still uses the f19
development grid and the current smoke final-frame policies:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 1
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 1
```

The next production-facing work should remove those smoke final-frame policies,
exercise a longer continued neutral/phi cadence, and then return to the
SAMI3 -> RAIJU/GAMERA physical-moment blockers: traced flux-tube weighting,
L/MLT mapping, scalar-moment semantics, and runtime blending/floors.
