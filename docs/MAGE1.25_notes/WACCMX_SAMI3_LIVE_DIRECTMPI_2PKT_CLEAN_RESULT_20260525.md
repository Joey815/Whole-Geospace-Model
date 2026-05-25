# WACCM-X/SAMI3 Live Neutral 2-Packet + Direct Voltron Phi Clean Result - 2026-05-25

## Result

The clean 2-packet live-neutral plus direct-Voltron-phi smoke completed with
the fixed validator:

```text
jobid = 7669527
jobname = wxsami3_p2p1c
state = COMPLETED
exit = 0:0
elapsed = 00:06:54
node = qhcn660
batch MaxRSS = 64901032K
archive = logs/waccmx_live_directmpi_2pkt_phi1_clean_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

This is the clean Slurm-completed repeat of the post-fix gate documented in
`WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_POSTFIX_RESULT_20260525.md`.

## Runtime Parameters

```text
SAMI3_MAXSTEP = 1
SAMI3_HRMAX = .300000
SAMI3_TPHI = 1.
SAMI3_DT0 = 900.
VOLTRON_TFIN = 10.25
PHI_MAX_FRAMES = 1
PHI_FRAME_HOUR_OFFSET = 0.0013888889
PHI_VALID_HOURS = 0.0013888889
CESM_STOP_N = 600
MAX_PACKETS = 2
LIVE_DUMP_MAX = 2
SEND_EVERY_NSTEPS = 1
```

## Runtime Chain

CESM/WACCM-X sender:

```text
WXSAMI3 sent live neutral packet: nstep=0 packet_hour=0.00000000 count=0
WXSAMI3 sent live neutral packet: nstep=1 packet_hour=0.0833333358 count=1
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

Voltron direct phi sender:

```text
WACCMX_SAMI3_PHI_DIRECT sent frame=0 nframes=1 hour=0.00000000 valid_until=1.0e30
WACCMX_SAMI3_PHI_DIRECT sent done=1
```

SAMI3 receiver:

```text
WACCMX_RECV_SOURCE_FLAGS packet 0: 32 worker rows
WACCMX_RECV_QC packet 0: 32 worker rows
WACCMX_PHI_RECV frame 0 of 1, hrut=0.00000000, hour=0.00000000, valid_until=1.0e30
WACCMX_RECV_SOURCE_FLAGS packet 1: 32 worker rows
WACCMX_RECV_QC packet 1: 32 worker rows
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 1
```

## Validation

All standard validators passed in the batch:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

Neutral replay/QC:

```text
packet0 recv_qc_compare max_rel = 4.83248e-13
packet1 recv_qc_compare max_rel = 6.76502e-13
receiver_qc_line_count = 64
sender_live_packet_count = 2
```

Time-axis validator:

```text
sender_neutral_packet_count = 2
receiver_neutral_packet_count = 2
receiver_worker_coverage = [32, 32]
sender_receiver_neutral_hours_match = ok
phi_payload_covers_neutral_packets = ok
receiver_phi_records_within_validity = ok
```

Source-flag/topblend validator:

```text
selected packet = 1
selected apply hour = 0.25
apply_source_flag_lines = 160
apply_qc_lines = 160
apply_blend_lines = 160
blend_i + blend_f = 2494
unknown source flags = 0
He native retention = ok
W zero policy = ok
```

## Interpretation

This closes the first clean 2-packet coexistence gate:

```text
live WACCM-X/CESM neutral packet 0
live WACCM-X/CESM neutral packet 1
SAMI3 online neutral receiver and worker distribution for both packets
SAMI3 top-blend and source-flag apply diagnostics
OpenMPI Voltron direct phi sender
SAMI3 direct phi receiver
time-axis validation across neutral and phi streams
```

The result is still a controlled cadence smoke, not the final production
cadence policy.  It uses:

```text
PHI_MAX_FRAMES = 1
final-valid direct phi cache
SAMI3_DT0 = 900.
SAMI3_MAXSTEP = 1
```

The next implementation step is to move from this forced short 2-packet gate to
a production-style cadence where SAMI3 consumes repeated neutral packets and
Voltron/REMIX supplies repeated phi frames without relying on a final-frame
cache.
