# WACCM-X/SAMI3 Direct-MPI Cache-After-Done Result - 2026-05-25

## Result

The direct-MPI cache-after-done gate completed:

```text
jobid = 7671608
jobname = wxsami3_cache
state = COMPLETED
exit = 0:0
elapsed = 00:14:12
node = qhcn005
batch MaxRSS = 61973.50M
archive = logs/waccmx_live_directmpi_cache_after_done_1pkt_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

This run directly validates the new SAMI3 receiver branch that handles a direct
phi done tag during a phi receive and returns the cached frame.

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
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e-6
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 0
MAX_PACKETS = 1
CESM_STOP_N = 300
```

The intentionally short final `valid_until` forces this sequence:

```text
1. SAMI3 receives direct phi frame 0.
2. Voltron sends direct phi done=1.
3. SAMI3 advances to hrut=8.33333358E-02 h.
4. SAMI3 requests phi again, probes a done tag, and returns the cached frame.
```

## Runtime Evidence

SAMI3 first received the direct phi frame:

```text
WACCMX_PHI_RECV 0 1 hrut=0.00000000 frame_hour=0.00000000 valid_until=9.99999997E-07
```

The second phi request received direct done during the receive path and used the
cache:

```text
SAMI3 direct phi done signal received during phi receive: 1
WACCMX_PHI_CACHE_AFTER_DONE 8.33333358E-02 1.00000002E+30 -36.9728775 31.5048161
```

The run still finalized normally:

```text
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 1
SAMI3_PHI_SKIP count = 0
bad marker count = 0
```

## Validation

All standard validators returned `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

A supplemental strict validator was run after adding
`--require-cache-after-done`:

```text
validate_sami3_direct_phi_run_cache_strict
  cache_after_done_used = ok, count=1
  direct_phi_done_received_during_phi = ok
  overall = ok
```

## Interpretation

Together with the previous no-smoke harness run, this closes both direct-phi
post-final-frame paths:

```text
direct done consumed during SAMI3 finalize
direct done consumed during a later SAMI3 phi receive
cached phi returned after direct done
no SAMI3_PHI_SKIP_MADALA_AFTER_FINAL
no WACCMX_SAMI3_PHI_STOP_AFTER_DONE
```

The next direct-MPI hardening target is a longer f19 cadence run with more than
two neutral packets and continued phi cadence, followed by the f09/distributed
neutral remap design.
