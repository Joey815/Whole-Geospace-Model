# WACCM-X/SAMI3 Direct-MPI No-Smoke 3pkt/3phi Result - 2026-05-25

## Result

The f19 direct-MPI no-smoke continued-cadence gate completed:

```text
jobid = 7671766
jobname = wxsami3_3p3f
state = COMPLETED
exit = 0:0
elapsed = 00:15:39
node = qhcn169
batch MaxRSS = 64920656K
archive = logs/waccmx_live_directmpi_nosmoke_dt300_3pkt_3phi_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

This is the first no-smoke direct-MPI run in this goal pass with more than two
WACCM-X neutral packets and multiple continued direct-phi frames.

## Runtime Parameters

```text
SAMI3_MAXSTEP = 3
SAMI3_HRMAX = .400000
SAMI3_TPHI = 1.
SAMI3_DT0 = 300.
SAMI3_NEUTRAL_UPDATE_HOURS = 0.08333333333333333
SAMI3_NEUTRAL_SPAN_HOURS = 0.08333333333333333
VOLTRON_TFIN = 20.25
VOLTRON_DTCOUPLE = 5.0
VOLTRON_TIMEOUT_SECONDS = 720
ALLOW_VOLTRON_TIMEOUT_AFTER_DONE = 1
PHI_MAX_FRAMES = 3
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_VALID_HOURS = 0.08333333333333333
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 0
MAX_PACKETS = 3
CESM_STOP_N = 900
```

## Runtime Evidence

CESM/WACCM-X sent three live neutral packets and then done:

```text
WXSAMI3 sent live neutral packet: nstep=0 packet_hour=0.00000000 count=0
WXSAMI3 sent live neutral packet: nstep=1 packet_hour=8.33333358E-02 count=1
WXSAMI3 sent live neutral packet: nstep=2 packet_hour=0.166666672 count=2
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

SAMI3 received all three neutral packets on all workers:

```text
packet 0 hour 0.00000000       32/32 workers
packet 1 hour 8.33333358E-02   32/32 workers
packet 2 hour 0.166666672      32/32 workers
```

Voltron direct-MPI sent three phi frames and direct done:

```text
frame 0 hour=0.00000000      valid_until=8.33333358E-02
frame 1 hour=8.33333358E-02  valid_until=0.166666672
frame 2 hour=0.166666672     valid_until=1.00000002E+30
WACCMX_SAMI3_PHI_DIRECT sent done=3
```

SAMI3 consumed the three direct phi frames:

```text
WACCMX_PHI_RECV frame 0 of 3 hrut=0.00000000
WACCMX_PHI_RECV frame 1 of 3 hrut=8.33333358E-02
WACCMX_PHI_RECV frame 2 of 3 hrut=0.166666672
MASTER: All Done!
WACCMX online done signal received: 3
SAMI3 direct phi done signal received: 3
SAMI3_PHI_SKIP count = 0
bad marker count = 0
```

## Validation

All validators returned `overall=ok`:

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
sender_neutral_packet_count = 3
receiver_neutral_packet_count = 3
receiver_worker_coverage = 32 workers for packets 0, 1, and 2
sender_receiver_neutral_hours_match = matched 3
phi_payload_frame_count = 3
receiver_phi_frame_count = 3
phi_payload_covers_neutral_packets = ok
```

## Interpretation

This is the current best f19 online-control baseline:

```text
WACCM-X/CAM live neutral extraction
  -> 3 runtime neutral packets at 300 s cadence
SAMI3 online neutral receiver
  -> 32/32 worker coverage for all packets
Voltron/REMIX direct-MPI phi
  -> 3 continued phi frames with matching 300 s validity windows
SAMI3 direct phi receiver/finalizer
  -> no skip path and no stop-after-done path
full validator pass
```

Next implementation work should move back to the physics blockers:

```text
SAMI3 -> RAIJU/GAMERA scalar moments
flux-tube-volume weighting
L/MLT or tube-geometry mapping
runtime blending/floors for Pavg/Davg/Pstd/Dstd/tiote
```
