# WACCM-X/SAMI3 Live Neutral 2-Packet + Direct Voltron Phi Post-Fix Result - 2026-05-25

## Result

The 2-packet live-neutral plus direct-Voltron-phi smoke completed the runtime
coupling path, but the Slurm batch exited with `FAILED` because the first
source-flag validator version filtered apply diagnostics by the WACCM-X packet
hour instead of the SAMI3 apply hour.

```text
jobid = 7669353
jobname = wxsami3_p2p1
state = FAILED
exit = 1:0
elapsed = 00:06:50
node = qhcn005
batch MaxRSS = 64896740K
archive = logs/waccmx_live_directmpi_2pkt_phi1_postfix_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

The failed pre-fix validator output is preserved as:

```text
validate_wxsami3_source_flag_balance.prefix_failed.txt
validate_wxsami3_source_flag_balance.prefix_failed.json
```

After fixing `validate_wxsami3_source_flag_balance.py`, the same run logs pass
the full validation matrix without rerunning the model.

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

This was a controlled cadence test: one final-valid phi frame, two WACCM-X
live neutral packets, and a short SAMI3 run with `dt0=900.` so packet 1 is
actually consumed and applied.

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
WACCMX_RECV_SOURCE_FLAGS packet 1: 32 worker rows
WACCMX_RECV_QC packet 1: 32 worker rows
WACCMX_PHI_RECV frame 0 of 1, hrut=0.00000000, hour=0.00000000, valid_until=1.0e30
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 1
```

## Validator Fix

The bug was in validator semantics, not model communication.  Receiver rows
encode the source packet hour:

```text
packet 0 -> receiver hour 0.00000000
packet 1 -> receiver hour 0.0833333358
```

Apply rows encode the SAMI3 apply hour:

```text
packet 0 apply block -> apply hour 0.00000000
packet 1 apply block -> apply hour 0.25000000
```

The fixed validator now selects the packet-index-th distinct apply-hour block,
unless `--apply-hour` is provided explicitly.  For this run it selects:

```text
packet_index = 1
selected_apply_hour = 0.25
```

and obtains the expected final packet apply diagnostics:

```text
apply_source_flag_lines = 160
apply_qc_lines = 160
apply_blend_lines = 160
```

## Validation

Post-fix validators:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

Neutral packet contract:

```text
sender_live_packet_count = 2
receiver_qc_line_count = 64
packet0 recv_qc_compare max_rel = 4.83248e-13
packet1 recv_qc_compare max_rel = 6.76502e-13
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

Top-blend/source flags:

```text
topblend_policy = linear, 600 km -> 720 km
packet1 recv_samples = 6031360
packet1 recv_valid = 4211458
packet1 recv_above_top = 1642002
packet1 recv_n2_invalid = 177900
packet1 blend_i + blend_f = 2494
unknown source flags = 0
He native retention = ok
W zero policy = ok
```

## Interpretation

This closes the first controlled 2-packet coexistence gate:

```text
WACCM-X/CESM live neutral packet 0
WACCM-X/CESM live neutral packet 1
SAMI3 receiver/worker distribution for both packets
SAMI3 neutral apply diagnostics for both packets
OpenMPI Voltron direct phi frame
SAMI3 direct phi receiver
time-axis validation over neutral + phi streams
```

It is still a cadence-smoke result, not a production cadence policy.  The run
uses one final-valid phi frame and `SAMI3_DT0=900.` to force a short controlled
multi-packet apply sequence.  A clean rerun with the fixed validator was
submitted as the next gate to remove the Slurm `FAILED` artifact from the
record.
