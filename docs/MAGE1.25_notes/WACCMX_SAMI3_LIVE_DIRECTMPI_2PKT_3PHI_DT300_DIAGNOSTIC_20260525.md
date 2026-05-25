# WACCM-X/SAMI3 Live Neutral 2-Packet + Direct Voltron 3-Phi DT300 Diagnostic - 2026-05-25

## Result

This run was intentionally diagnostic and was cancelled after the useful
evidence was captured:

```text
jobid = 7670003
jobname = wxsami3_p2p3d300
state = CANCELLED by user
batch exit = 0:15
elapsed = 00:09:07
node = qhcn005
batch MaxRSS = 64891092K
archive = logs/waccmx_live_directmpi_2pkt_phi3_dt300_diag_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

The purpose was to test whether reducing `SAMI3_DT0` from 900 s to 300 s fixes
the previous `MAXSTEP=2` numerical abort while using an explicit 5-minute phi
metadata cadence.

## Runtime Parameters

```text
SAMI3_MAXSTEP = 2
SAMI3_HRMAX = .300000
SAMI3_TPHI = 1.
SAMI3_DT0 = 300.
VOLTRON_TFIN = 20.25
PHI_MAX_FRAMES = 3
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_FRAME_HOUR_OFFSET = 0.0
PHI_VALID_HOURS = 0.08333333333333333
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
MAX_PACKETS = 2
LIVE_DUMP_MAX = 2
SEND_EVERY_NSTEPS = 1
CESM_STOP_N = 600
```

## Positive Evidence

The previous `MAXSTEP=2, DT0=900` run aborted with SAMI3 `Time step too small`
and PRTE fatal markers.  This run did not show those numerical/fatal markers.

Voltron sent three changing direct-phi frames with the intended 5-minute
metadata cadence:

```text
frame 0: hour=0.00000000 valid_until=0.0833333358
frame 1: hour=0.0833333358 valid_until=0.166666672
frame 2: hour=0.166666672 valid_until=1.0e30
```

SAMI3 received the same three frames:

```text
WACCMX_PHI_RECV frame 0 of 3 hour=0.00000000 valid_until=0.0833333358
WACCMX_PHI_RECV frame 1 of 3 hour=0.0833333358 valid_until=0.166666672
WACCMX_PHI_RECV frame 2 of 3 hour=0.166666672 valid_until=1.0e30
MASTER: All Done!
```

Validators:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_wxsami3_time_axis_allow_incomplete = overall=ok
```

## Failure / Blocker

The run did not receive the second WACCM-X neutral packet before SAMI3
finalized:

```text
receiver_packet_counts:
  32 rows for packet 0 at hour 0.00000000
  0 rows for packet 1
```

Missing completion markers:

```text
WACCMX online done signal received
SAMI3 direct phi done signal received
WACCMX_SAMI3_PHI_DIRECT sent done
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

Interpretation:

```text
DT0=300 fixed the immediate SAMI3 numerical stability issue,
but it exposed a cadence-ordering problem: SAMI3 can outrun CESM/WACCM-X and
finish before the second live neutral packet is sent/received.
```

This means the next step should not be another blind `DT0` tweak.  The live
neutral cadence needs a synchronization policy:

```text
option A: SAMI3 waits at neutral coupling boundaries until the expected packet
          or done tag arrives;
option B: CESM/WACCM-X pre-sends enough startup packets before SAMI3 advances;
option C: the launcher starts CESM earlier and gates SAMI3 advance on packet
          availability;
option D: use a shared coupling clock so SAMI3 cannot run ahead of WACCM-X.
```

The clean base-step two-frame gate remains the current success baseline:

```text
docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_2PHI_BASESTEP_CLEAN_RESULT_20260525.md
```
