# WACCM-X/SAMI3 Direct-MPI No-Smoke Harness Archive - 2026-05-25

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_neutral_nosmoke_dt300_2pkt_1phi_harness_20260525_0000
```

Slurm:

```text
jobid = 7671470
jobname = wxsami3_nc1h
state = COMPLETED
exit = 0:0
elapsed = 00:14:55
node = qhcn660
batch MaxRSS = 64873580K
```

Purpose:

```text
Validate the direct-MPI path without the old smoke final-frame controls:
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL=0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE=0
```

Runtime result:

```text
neutral packets received by SAMI3 workers:
  packet 0 hour 0.00000000         32/32 workers
  packet 1 hour 8.33333358E-02     32/32 workers

direct phi:
  frame 0 of 1 received
  sender sent direct phi done=1
  SAMI3 finalized with direct phi done=1
  skip_count=0
  bad_marker_count=0
```

The launcher accepted the Voltron side `timeout` only after both conditions
were already true:

```text
WACCMX_SAMI3_PHI_DIRECT sent done=1
MASTER: All Done!
```

This keeps the harness from treating post-SAMI3 Voltron continuation as a
communication failure. It is a test-harness completion policy, not a production
physics stop policy.

Archived files:

```text
slurm-7671470.out
slurm-7671470.err
sami3_online_receiver.out
waccmx_cesm.out
voltron_runtime_direct.out
phi_payload_summary.txt
validate_*.json
```
