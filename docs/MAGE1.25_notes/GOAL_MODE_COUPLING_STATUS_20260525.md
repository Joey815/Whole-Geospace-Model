# Goal-Mode Coupling Status

Date: 2026-05-25 CST

## Goal

Drive the current MAGE1.25 / WACCM-X / SAMI3 coupling prototype toward a
single verifiable online chain:

```text
WACCM-X/CAM runtime phys_state(:)
  -> SAMI3 online neutral receiver
REMIX/Voltron runtime potential payload
  -> SAMI3 online phi_weimer receiver
SAMI3 scalar moments
  -> RAIJU/GAMERA runtime ingest with conservative blending
```

The target remains a validated prototype, not a production physics coupling.

## Active Acceptance Gates

Status refreshed: 2026-05-25 04:42:02 CST.

### WACCM-X/CESM -> SAMI3 Direct-Wait Phi Integration

Slurm:

```text
jobid = 7661005
jobname = wxsami3_ap2w
state = PENDING
reason = Priority
requested = 1 intel node, 49 tasks, 296G
```

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000
```

Completion gate:

```bash
python3 scripts/archive_current_goal_mode_runs.py --target directwait
```

This must show:

```text
Voltron append2 phi payload starts at hour=0
WACCM-X sender reports two phi frames
SAMI3 receiver logs the expected WACCMX_PHI_RECV frames
SAMI3 reaches MASTER: All Done!
CESM/WACCM-X reaches END OF MODEL RUN
neutral receiver replay QC passes
fatal markers absent
DIRECT_WAIT_MODE=1
VOLTRON_WRITER_PID=<pid>
WXSAMI3 phi payload ready after wait
```

### Completed Stability Gates

The full append2 WACCM-X/CESM -> SAMI3 online integration gate is complete:

```text
jobid = 7659727
jobname = wxsami3_ap2
state = COMPLETED
exit = 0:0
elapsed = 00:05:18
node = qhcn332
batch MaxRSS = 60176444K
archive = logs/waccmx_append2_full_20260525/
```

Strict validation returned `overall=ok` for append2 online logs, phi payload
content, time-axis consistency, live packet contract, top-blend policy, and the
f19 runtime-map/ESMF-weight product.  SAMI3 reached `MASTER: All Done!`, WACCM-X
reached `END OF MODEL RUN`, and receiver-side neutral replay matched with
`max_rel=4.83248e-13`.

The 1800 second recommended prototype gate is complete:

```text
jobid = 7663122
jobname = sami3_rai_long1800
state = COMPLETED
exit = 0:0
elapsed = 01:23:20
node = qhcn065
batch MaxRSS = 1169988K
archive = logs/sami3_dsB_lmlt_recommended_long1800_20260525/
```

Strict validation, mapping-product validation, and HDF5 summary validation all
returned `overall=ok`.  Baseline/control and recommended runs both reached
`Fin`; they wrote 362 RAIJU history outputs and 364 GAMERA history outputs, and
the final RAIJU/GAMERA history comparison matched at `Step#361`.

The previous 900 second recommended prototype gate is also complete:


```text
jobid = 7660334
jobname = sami3_rai_long900
state = COMPLETED
exit = 0:0
elapsed = 00:48:44
node = qhcn095
batch MaxRSS = 1067328K
archive = logs/sami3_dsB_lmlt_recommended_long900_20260525/
```

Strict validation and HDF5 summary artifacts have been committed and pushed.

## Next Work Order

1. Keep polling job `7661005`.
2. When dependency job `7661005` completes, run the direct-wait archiver with
   `--expect-phi-wait-marker --expect-direct-wait-mode`, write the result note,
   and push to GitHub.
3. If the direct-wait job remains queued or running, continue implementation work on the
   remaining production blockers:
   - production cadence/f09 live source-state validation beyond the current
     f19 same-call-site replay gate,
   - production top-blend height and per-variable policy,
   - direct live REMIX/Voltron phi producer to online MPI sender path,
   - true traced flux-tube volume map for SAMI3 -> RAIJU/GAMERA,
   - finer f09/distributed remap design.

`intel_expr` fallback note: the previous append2 expr job failed because
`module load` returned nonzero on a non-fatal `.modulerc` `module-hide` warning.
The expr launcher now tolerates that warning after probe jobs confirmed the
oneAPI/HDF5 environment is still applied and the CESM case env returns zero.
It has not been resubmitted yet to avoid racing the queued `intel` job against
the same CESM run directory.

## New Tooling Added In This Goal Pass

```text
scripts/validate_sami3_raiju_mapping_product.py
scripts/validate_wxsami3_append2_run.py --expect-direct-wait-mode
scripts/archive_wxsami3_append2_result.py --expect-direct-wait-mode
scripts/validate_wxsami3_topblend_policy.py
scripts/validate_wxsami3_runtime_map.py
scripts/validate_wxsami3_live_packet_contract.py field-stat gates
scripts/validate_sami3_raiju_mapping_product.py strict moment gates
scripts/validate_remix_sami3_phi_payload.py
scripts/validate_wxsami3_time_axis.py
scripts/validate_sami3_raiju_summary.py
scripts/validate_wxsami3_replay_cadence.py
scripts/archive_current_goal_mode_runs.py
```

The mapping-product validator now gates `/RaiCplMomentsOnly` plus
`/MappingQuality` products before runtime ingest.  It now also verifies masked
Pavg/Davg/Pstd/Dstd non-negativity, tiote bounds, and the runtime mask
convention for the populated bulk channel.  The direct-wait validator now
distinguishes a completed pre-generated phi payload from a same-job producer
and waiter path.

The WACCM-X archive gate now also checks the live metadata schema, phi payload
content, top-blend policy diagnostics, and runtime-map/ESMF weight consistency.
The live packet contract validator now also checks live dump field bad-counts
and plausible ranges before replay, covering lat/lon, T, U/V, pressure, height,
mean molecular mass, and the major CAM species used for residual N2.

The REMIX/Voltron phi payload now has an independent binary contract gate before
online send: exact schema/version/grid, exact byte size, finite/nonzero values,
strictly increasing frame hours, next-frame `valid_until` linkage, and optional
time-varying-frame enforcement.

The online WACCM-X/SAMI3 evidence gate now also checks timeline consistency:
sender and receiver neutral packet hours, receiver worker coverage, phi-frame
validity intervals, and whether neutral packet hours are covered by the
available phi payload frames.

The live neutral contract gate now also closes fallback accounting: above-top
cells, N2-negative residual cells, unknown invalid cells, and replay
initial/final fallback counts must agree with the source-flag metadata.
It also checks metadata cadence consistency: positive `dtime_phys_s`, positive
`send_every_nsteps`, and `packet_hour = nstep * dtime_phys_s / 3600`.
For legacy multi-packet archives that predate source-flag metadata, the replay
cadence gate verifies packet order, packet-hour cadence, rank count, and
replay-vs-receiver `max_rel` without overstating them as current full-contract
evidence.

The SAMI3 -> RAIJU/GAMERA long-run archive now turns summary diagnostics into a
hard gate: exact Pavg/Davg/Pstd/Dstd blending formula residuals, positive
Pavg/Davg inputs, empty nonfinite restart lists, matching RAIJU/GAMERA history
steps, and finite restart/history response metrics.

`archive_current_goal_mode_runs.py` freezes the strict append2 and direct-wait
archive commands for the active 2026-05-25 goal-mode jobs.  It checks `sacct`
first, skips incomplete jobs by default, and can be used with
`--allow-incomplete` only for explicit partial evidence snapshots.
