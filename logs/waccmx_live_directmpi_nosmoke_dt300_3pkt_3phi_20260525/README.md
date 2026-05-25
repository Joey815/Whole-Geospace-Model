# WACCM-X/SAMI3 Direct-MPI No-Smoke 3pkt/3phi Archive - 2026-05-25

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_nosmoke_dt300_3pkt_3phi_20260525_0000
```

Slurm:

```text
jobid = 7671766
jobname = wxsami3_3p3f
state = COMPLETED
exit = 0:0
elapsed = 00:15:39
node = qhcn169
batch MaxRSS = 64920656K
```

Purpose:

```text
Validate a longer f19 direct-MPI cadence gate with more than two WACCM-X
neutral packets and continued direct-MPI Voltron phi cadence, while keeping:
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL=0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE=0
```

Runtime result:

```text
neutral packet 0 hour 0.00000000       32/32 workers
neutral packet 1 hour 8.33333358E-02   32/32 workers
neutral packet 2 hour 0.166666672      32/32 workers

direct phi frame 0 hour 0.00000000      valid_until=8.33333358E-02
direct phi frame 1 hour 8.33333358E-02  valid_until=0.166666672
direct phi frame 2 hour 0.166666672     valid_until=1.00000002E+30

SAMI3 reached MASTER: All Done!
WACCM-X reached END OF MODEL RUN
SAMI3 direct phi done signal received: 3
skip_count = 0
bad_marker_count = 0
```

All standard validators returned `overall=ok`.

Archived files:

```text
slurm-7671766.out
slurm-7671766.err
sami3_online_receiver.out
waccmx_cesm.out
voltron_runtime_direct.out
phi_payload_summary.txt
validate_*.json
validate_*.txt
```
