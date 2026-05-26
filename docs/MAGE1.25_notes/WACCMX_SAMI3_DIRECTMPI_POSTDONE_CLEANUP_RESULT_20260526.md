# WACCM-X/SAMI3 Direct-MPI Post-Done Cleanup Result

Date: 2026-05-26 CST

## Purpose

The 24pkt/24phi f19 run reached all direct-phi, SAMI3, and CESM done markers,
but the Slurm script still waited on the Voltron timeout wrapper because
`PHI_STOP_AFTER_DONE=0`.  This checkpoint verifies the launcher-side fix that
terminates the Voltron wrapper only after the done markers are present.

## Launcher Change

Updated script:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

New controls:

```text
WXSAMI3_DIRECTMPI_STOP_VOLTRON_AFTER_DONE = 1
WXSAMI3_DIRECTMPI_VOLTRON_POST_DONE_TERM_GRACE_SECONDS = 30
```

The launcher records the Voltron timeout wrapper PID and, after CESM and SAMI3
finish, checks for:

```text
WACCMX_SAMI3_PHI_DIRECT sent done=
MASTER: All Done!
```

Only then does it terminate the Voltron timeout wrapper and let the existing
nonzero-exit acceptance gate handle the expected `status=143`.

## Smoke Result

```text
jobid = 7702222
jobname = wxsami3_pdclean
state = COMPLETED
exit = 0:0
elapsed = 00:06:26
node = qhcn301
batch MaxRSS = 63532504K
archive = logs/waccmx_live_directmpi_postdone_cleanup_1pkt_1phi_20260526/
run_dir = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_postdone_cleanup_1pkt_1phi_20260526_0000
```

Runtime settings:

```text
MAX_PACKETS = 1
PHI_MAX_FRAMES = 1
SAMI3_MAXSTEP = 2
SAMI3_HRMAX = .300000
SAMI3_DT0 = 300.
CESM_STOP_N = 600
PHI_STOP_AFTER_DONE = 0
STOP_VOLTRON_AFTER_DONE = 1
VOLTRON_POST_DONE_TERM_GRACE_SECONDS = 5
VOLTRON_TIMEOUT_SECONDS = 600
COMPONENT_TIMEOUT_SECONDS = 1200
```

Key launcher markers:

```text
INFO: terminating Voltron after verified direct phi/SAMI3 done markers: pid=797490
INFO: accepting Voltron nonzero exit after direct phi done and SAMI3 completion: status=143
```

Key model markers:

```text
WACCMX_SAMI3_PHI_DIRECT sent done=1
MASTER: All Done!
END OF MODEL RUN
```

All archive validators returned `overall=ok`:

```text
validate_sami3_direct_phi_run_strict
validate_remix_sami3_phi_payload
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

The live packet contract confirmed:

```text
sender_live_packet_count = 1
receiver_qc_line_count = 32
fatal_markers_absent = true
```

## Interpretation

The long-cadence launcher no longer requires manual intervention when Voltron
has sent the direct-phi done marker but remains alive under `PHI_STOP_AFTER_DONE=0`.
This preserves the existing safety condition: Voltron is cleaned up only after
both direct-phi done and SAMI3 completion are verified.
