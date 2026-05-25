# WACCM-X/SAMI3 Direct-MPI Cache-After-Done Archive - 2026-05-25

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_cache_after_done_1pkt_20260525_0000
```

Slurm:

```text
jobid = 7671608
jobname = wxsami3_cache
state = COMPLETED
exit = 0:0
elapsed = 00:14:12
node = qhcn005
batch MaxRSS = 61973.50M
```

Purpose:

```text
Force SAMI3 to request phi again after the direct-MPI sender has already sent
its done tag, then verify that SAMI3 returns the cached phi instead of using the
old SAMI3_PHI_SKIP_MADALA_AFTER_FINAL path.
```

Runtime result:

```text
neutral packet 0 hour 0.00000000 received by 32/32 workers
direct phi frame 0 of 1 received with valid_until=9.99999997E-07 h
SAMI3 direct phi done signal received during phi receive: 1
WACCMX_PHI_CACHE_AFTER_DONE at hrut=8.33333358E-02 h
SAMI3_PHI_SKIP count = 0
bad marker count = 0
```

Supplemental strict validator:

```text
validate_sami3_direct_phi_run_cache_strict.txt
  cache_after_done_used: count=1
  direct_phi_done_received_during_phi: marker
  overall=ok
```

Archived files:

```text
slurm-7671608.out
slurm-7671608.err
sami3_online_receiver.out
waccmx_cesm.out
voltron_runtime_direct.out
phi_payload_summary.txt
validate_*.json
validate_*.txt
```
