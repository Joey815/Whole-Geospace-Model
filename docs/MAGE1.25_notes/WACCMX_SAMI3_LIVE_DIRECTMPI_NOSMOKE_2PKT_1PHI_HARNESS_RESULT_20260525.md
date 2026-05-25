# WACCM-X/SAMI3 Direct-MPI No-Smoke Harness Result - 2026-05-25

## Result

The direct-MPI WACCM-X/CESM + SAMI3 + Voltron no-smoke harness gate completed:

```text
jobid = 7671470
jobname = wxsami3_nc1h
state = COMPLETED
exit = 0:0
elapsed = 00:14:55
node = qhcn660
batch MaxRSS = 64873580K
archive = logs/waccmx_live_directmpi_nosmoke_2pkt_1phi_harness_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

This run removes the old direct-phi smoke controls from the SAMI3 side and the
Voltron direct sender:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 0
```

The online chain still reached clean batch completion and all validators passed.

## Runtime Parameters

```text
SAMI3_MAXSTEP = 2
SAMI3_HRMAX = .200000
SAMI3_TPHI = 1.
SAMI3_DT0 = 300.
SAMI3_NEUTRAL_UPDATE_HOURS = 0.08333333333333333
SAMI3_NEUTRAL_SPAN_HOURS = 0.08333333333333333
VOLTRON_TFIN = 5.25
VOLTRON_DTCOUPLE = 5.0
VOLTRON_TIMEOUT_SECONDS = 720
ALLOW_VOLTRON_TIMEOUT_AFTER_DONE = 1
PHI_MAX_FRAMES = 1
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_VALID_HOURS = 0.08333333333333333
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
MAX_PACKETS = 2
LIVE_DUMP_MAX = 2
SEND_EVERY_NSTEPS = 1
CESM_STOP_N = 600
```

## Runtime Evidence

CESM/WACCM-X sent two live neutral packets and then sent done:

```text
WXSAMI3 sent live neutral packet: nstep=0 packet_hour=0.00000000 count=0
WXSAMI3 sent live neutral packet: nstep=1 packet_hour=8.33333358E-02 count=1
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

SAMI3 received both neutral packets on all workers:

```text
packet 0 hour 0.00000000       32/32 workers
packet 1 hour 8.33333358E-02   32/32 workers
```

Voltron direct-MPI phi sent one frame and then direct done:

```text
WACCMX_SAMI3_PHI_DIRECT sent frame=0 nframes=1 hour=0.00000000 valid_until=1.00000002E+30
WACCMX_SAMI3_PHI_DIRECT sent done=1
```

SAMI3 consumed the direct-phi frame and finalized without using the old skip
path:

```text
WACCMX_PHI_RECV frame=0 of 1 hour=0.00000000 valid_until=1.00000002E+30
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 1
SAMI3_PHI_SKIP count = 0
bad marker count = 0
```

## Harness Policy

With `WACCMX_SAMI3_PHI_STOP_AFTER_DONE=0`, Voltron continues after the direct
sender has sent done. For this short gate, the launcher now accepts a Voltron
timeout only after both of these markers are present:

```text
WACCMX_SAMI3_PHI_DIRECT sent done=
MASTER: All Done!
```

The accepted marker in this run was:

```text
INFO: accepting Voltron nonzero exit after direct phi done and SAMI3 completion: status=124
```

This is a test-harness completion policy. It does not mean production Voltron
physics should be stopped after direct-phi done; it only prevents a validated
SAMI3/WACCM-X communication gate from failing because Voltron keeps integrating
after the SAMI3 consumer has completed.

## Validation

All archived validators returned `ok=True` and printed `overall=ok` in the
Slurm log:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

The strict direct-phi validator confirmed:

```text
master_done = ok
neutral_done_received = ok
direct_phi_done_received = ok
phi_sender_sent_done = ok
fatal markers absent = ok
```

The time-axis validator confirmed:

```text
sender_neutral_packet_count = 2
receiver_neutral_packet_count = 2
receiver_worker_coverage = 32 workers for packet 0 and packet 1
phi_payload_frame_count = 1
receiver_phi_frame_count = 1
```

## Interpretation

This closes the immediate "remove smoke final-frame controls" gate for the
direct-MPI path:

```text
WACCM-X live neutral packets from CAM phys_state(:)
  -> SAMI3 online neutral receiver
Voltron/REMIX direct-MPI phi frame + direct done
  -> SAMI3 direct phi receiver/finalizer
no SAMI3_PHI_SKIP_MADALA_AFTER_FINAL
no WACCMX_SAMI3_PHI_STOP_AFTER_DONE
full validator pass
```

The direct-phi cache-after-done receive branch is implemented in
`waccmx_neutral_mod.f90`, but this particular run did not exercise it because
the only direct-phi frame used `valid_until=1.0e30`. A separate short gate should
force a second phi request after direct done to validate the cache branch.
