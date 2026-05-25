# WACCM-X/SAMI3 Live Neutral 2-Packet + Direct Voltron 2-Phi Base/Step Clean Result - 2026-05-25

## Result

The controlled two-neutral-packet plus two-direct-Voltron-phi cadence smoke
completed cleanly after adding explicit direct-phi frame-hour control:

```text
jobid = 7669815
jobname = wxsami3_p2p2b
state = COMPLETED
exit = 0:0
elapsed = 00:07:42
node = qhcn005
batch MaxRSS = 64922812K
archive = logs/waccmx_live_directmpi_2pkt_phi2_basestep_clean_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

This is the clean rerun of the failed diagnostic gate documented in
`WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_2PHI_DIAGNOSTIC_20260525.md`.

## Code Change

The Voltron direct-phi sender now accepts:

```text
WACCMX_SAMI3_PHI_FRAME_HOUR_BASE
WACCMX_SAMI3_PHI_FRAME_HOUR_STEP
```

When both are set, the direct-phi metadata is:

```text
frame_hour = base + frame_index * step
```

If they are not set, the previous runtime-hour plus optional offset behavior is
unchanged.  The launcher exposes these as:

```text
WXSAMI3_DIRECTMPI_PHI_FRAME_HOUR_BASE
WXSAMI3_DIRECTMPI_PHI_FRAME_HOUR_STEP
```

The launcher also defaults `PHI_FRAME_HOUR_OFFSET=0.0` when base/step mode is
used, so the old offset is not accidentally applied to the diagnostic cadence.

Two validators were hardened for the live path:

```text
validate_sami3_direct_phi_run.py
  accepts WXSAMI3 sent done signal to SAMI3 as the live neutral done marker

validate_wxsami3_source_flag_balance.py
  only applies wxsami3_live_meta.json numerical closure when the selected
  packet index matches the metadata packet index
```

## Runtime Parameters

```text
SAMI3_MAXSTEP = 1
SAMI3_HRMAX = .300000
SAMI3_TPHI = 1.
SAMI3_DT0 = 900.
VOLTRON_TFIN = 10.25
PHI_MAX_FRAMES = 2
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.25
PHI_FRAME_HOUR_OFFSET = 0.0
PHI_VALID_HOURS = 0.25
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
MAX_PACKETS = 2
LIVE_DUMP_MAX = 2
SEND_EVERY_NSTEPS = 1
CESM_STOP_N = 600
```

## Runtime Chain

CESM/WACCM-X sender:

```text
WXSAMI3 sent live neutral packet: nstep=0 packet_hour=0.00000000 count=0
WXSAMI3 sent live neutral packet: nstep=1 packet_hour=0.0833333358 count=1
WXSAMI3 sent done signal to SAMI3
WXSAMI3 disconnected from SAMI3
```

Voltron direct phi sender:

```text
WACCMX_SAMI3_PHI_DIRECT sent frame=0 nframes=2 hour=0.00000000 valid_until=0.25
WACCMX_SAMI3_PHI_DIRECT sent frame=1 nframes=2 hour=0.25000000 valid_until=1.0e30
WACCMX_SAMI3_PHI_DIRECT sent done=2
WACCMX_SAMI3_PHI_DIRECT stop after done requested
```

SAMI3 receiver:

```text
WACCM-X packet 0 received on 32 workers
WACCM-X packet 1 received on 32 workers
WACCMX_PHI_RECV frame 0 of 2 hour=0.0 valid_until=0.25
WACCMX_PHI_RECV frame 1 of 2 hour=0.25 valid_until=1.0e30
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 2
```

## Validation

All archived validators returned `overall=ok`:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance_packet0 = overall=ok
validate_wxsami3_source_flag_balance_packet1 = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

Important numeric checks:

```text
phi payload hours = [0.0, 0.25]
phi payload valid_until = [0.25, 1.000000015e30]
phi frame max_abs_diff = 3.4961066
packet0 recv_qc_compare max_rel = 4.83248e-13
packet1 recv_qc_compare max_rel = 6.76502e-13
```

Grid contract:

```text
WACCM-X source grid = f19 = 144 x 96 = 13824 CAM columns
SAMI3 neutral payload header = nz=304, nf=124, nl=5, nneut=7
runtime map source columns = 13824
```

## Interpretation

This closes the controlled 2-packet + 2-phi direct-MPI cadence smoke.  It
proves that the same-stack online chain can run with:

```text
two live WACCM-X/CAM phys_state(:) neutral packets
two runtime Voltron/REMIX phi frames sent directly over MPI
SAMI3 receiving both streams and finalizing cleanly
neutral replay/QC matching receiver diagnostics
non-overlapping phi validity windows covering the neutral apply hours
```

This is still a prototype cadence, not production physics coupling, because it
uses a short controlled run and a final-valid phi frame cache:

```text
SAMI3_MAXSTEP = 1
SAMI3_DT0 = 900.
SAMI3_PHI_SKIP_AFTER_FINAL = 1
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 1
```

The next production-hardening step is to move away from this forced short
cadence toward a longer repeated cadence where SAMI3 consumes repeated neutral
packets and repeated Voltron/REMIX phi frames without relying on a final-frame
cache.
