# WACCM-X/SAMI3 2-Packet + 2-Phi Controlled Cadence Diagnostic - 2026-05-25

## Result

The 2-packet + 2-direct-phi controlled cadence run failed as a full model run,
but it produced useful diagnostic evidence:

```text
jobid = 7669625
jobname = wxsami3_p2p2
state = FAILED
exit = 16:0
elapsed = 00:05:51
node = qhcn660
batch MaxRSS = 64907856K
archive = logs/waccmx_live_directmpi_2pkt_phi2_dt900_diag_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

## What Passed

The transport path advanced beyond the previous clean 1-phi gate:

```text
SAMI3 received WACCM-X packet 0 on 32 workers
SAMI3 received WACCM-X packet 1 on 32 workers
SAMI3 received direct phi frame 0 of 2
SAMI3 received direct phi frame 1 of 2
```

Post-run replay/QC, using the sender's `WXSAMI3_N2_NEGATIVE_MODE=invalid`
policy, matched receiver checksums:

```text
packet0 recv_qc_compare max_rel = 4.83248e-13
packet1 recv_qc_compare max_rel = 6.76502e-13
```

Phi payload validation passed:

```text
validate_remix_sami3_phi_payload = overall=ok
size = 97044 bytes
header = [20260524, 1, 125, 97, 2]
frame0 min/max = -36.972878, 31.504816
frame1 min/max = -37.706364, 31.759037
frame1_minus_frame0_max_abs = 3.4961066
frame1_minus_frame0_rms = 0.62902843
```

The incomplete-run time-axis validator also passed:

```text
validate_wxsami3_time_axis_allow_incomplete = overall=ok
receiver_neutral_packet_count = 2
receiver_worker_coverage = [32, 32]
receiver_phi_frame_count = 2
receiver_phi_records_within_validity = ok
```

## What Failed

The run did not reach normal SAMI3 finalization:

```text
MASTER: All Done! = missing
WACCMX online done signal = missing
SAMI3 direct phi done signal = missing
```

SAMI3 hit numerical time-step failure after the second phi receive and packet 1
application:

```text
Time step too small ...
vparallel ...
MPI_ERRORS_ARE_FATAL
```

This is not a failed MPI handoff.  The handoff itself delivered both neutral
packets and both phi frames before the numerical abort.

## Frame-Hour Finding

This run also exposed an important Voltron sender metadata issue.  The launcher
was run with:

```text
PHI_FRAME_HOUR_OFFSET = 0.25
PHI_VALID_HOURS = 0.25
PHI_MAX_FRAMES = 2
```

but the Voltron sender computes:

```text
frame_hour = voltron_time / 3600 - WACCMX_SAMI3_PHI_FRAME_HOUR_OFFSET
```

So `PHI_FRAME_HOUR_OFFSET` is not a frame interval.  It is subtracted from the
current Voltron time.  The actual frame metadata was:

```text
frame0 hour = -0.248611107, valid_until = 0.0013888889
frame1 hour = -0.247222215, valid_until = 1.0e30
```

That is acceptable only as a diagnostic transport smoke.  It is not a
production time-axis representation.

## Next Fix

Add an explicit diagnostic frame-hour override to the Voltron sender, separate
from the existing `FRAME_HOUR_OFFSET` behavior:

```text
WACCMX_SAMI3_PHI_FRAME_HOUR_BASE
WACCMX_SAMI3_PHI_FRAME_HOUR_STEP
```

When present, the direct/payload writer should emit:

```text
frame_hour = base + frame_index * step
```

This will let the next controlled cadence gate test SAMI3 neutral and phi
transport using intended frame metadata, without confusing the existing Voltron
runtime-time path.
