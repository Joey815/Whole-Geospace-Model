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

Status refreshed: 2026-05-25 15:27:47 CST.

### Latest Completed Gate: No-Smoke 3pkt/3phi Direct-MPI Cadence

The current same-stack WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-MPI
no-smoke continued-cadence gate is complete:

```text
jobid = 7671766
jobname = wxsami3_3p3f
state = COMPLETED
exit = 0:0
elapsed = 00:15:39
node = qhcn169
batch MaxRSS = 64920656K
archive = logs/waccmx_live_directmpi_nosmoke_dt300_3pkt_3phi_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NOSMOKE_3PKT_3PHI_RESULT_20260525.md
```

Validated runtime facts:

```text
three WACCM-X/CESM live neutral packets from CAM phys_state(:)
packet 0 received by 32/32 SAMI3 workers
packet 1 received by 32/32 SAMI3 workers
packet 2 received by 32/32 SAMI3 workers
three Voltron direct-MPI phi frames received by SAMI3
phi validity windows cover the neutral packet hours
SAMI3 reached MASTER: All Done!
WACCM-X reached END OF MODEL RUN
SAMI3 direct phi done signal received: 3
skip_count = 0
bad_marker_count = 0
```

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

Next work order after this gate:

```text
1. Return to SAMI3 -> RAIJU/GAMERA scalar-moment physics blockers:
   traced flux-tube-volume weighting, L/MLT/tube mapping, and runtime
   blending/floors for Pavg/Davg/Pstd/Dstd/tiote.
2. Keep f19 as the validated online-control grid for now; design f09 and
   distributed live-neutral remap after the scalar-moment path is hardened.
```

### Previous Completed Gate: Direct-MPI Cache After Done

The previous same-stack WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-MPI
cache-after-done gate is complete:

```text
jobid = 7671608
jobname = wxsami3_cache
state = COMPLETED
exit = 0:0
elapsed = 00:14:12
node = qhcn005
batch MaxRSS = 61973.50M
archive = logs/waccmx_live_directmpi_cache_after_done_1pkt_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_CACHE_AFTER_DONE_RESULT_20260525.md
```

This run forced a second SAMI3 phi request after the direct-MPI sender had
already sent done:

```text
PHI_MAX_FRAMES = 1
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e-6
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 0
MAX_PACKETS = 1
```

Validated runtime facts:

```text
neutral packet 0 received by 32/32 SAMI3 workers
direct phi frame 0 received with valid_until=9.99999997E-07 h
SAMI3 direct phi done signal received during phi receive
WACCMX_PHI_CACHE_AFTER_DONE at hrut=8.33333358E-02 h
SAMI3 reached MASTER: All Done!
WACCM-X reached END OF MODEL RUN
skip_count = 0
bad_marker_count = 0
```

All standard validators returned `overall=ok`, and the supplemental strict
validator with `--require-cache-after-done` also returned `overall=ok`.

Next work order after this gate:

```text
1. Run a longer f19 direct-MPI cadence case with more than two neutral packets
   and continued phi cadence.
2. Keep f19 as the validated development grid; defer f09/distributed remap
   until continued cadence is stable.
3. Return to SAMI3 -> RAIJU/GAMERA physics blockers: traced flux-tube weighting,
   L/MLT mapping, and runtime blending/floors for scalar moments.
```

### Previous Completed Gate: No-Smoke Direct-MPI Phi Harness

The previous same-stack WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-MPI
no-smoke harness gate is complete:

```text
jobid = 7671470
jobname = wxsami3_nc1h
state = COMPLETED
exit = 0:0
elapsed = 00:14:55
node = qhcn660
batch MaxRSS = 64873580K
archive = logs/waccmx_live_directmpi_nosmoke_2pkt_1phi_harness_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NOSMOKE_2PKT_1PHI_HARNESS_RESULT_20260525.md
```

This run validated the direct-MPI path without the previous final-frame smoke
controls:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 0
```

Validated runtime facts:

```text
two WACCM-X/CESM live neutral packets from CAM phys_state(:)
packet 0 received by 32/32 SAMI3 workers
packet 1 received by 32/32 SAMI3 workers
one Voltron direct-MPI phi frame received by SAMI3
Voltron direct-MPI phi done sent and consumed during SAMI3 finalize
SAMI3 reached MASTER: All Done!
WACCM-X reached END OF MODEL RUN
skip_count = 0
bad_marker_count = 0
```

All archived validators returned `ok=True` / `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

Harness note: with `WACCMX_SAMI3_PHI_STOP_AFTER_DONE=0`, Voltron continues
after the SAMI3 consumer is done.  The launcher now accepts a Voltron timeout
only after both `WACCMX_SAMI3_PHI_DIRECT sent done=` and `MASTER: All Done!`
are present.  This is a test-harness completion policy, not a production
physics stop policy.

Next work order after this gate:

```text
1. Force a second SAMI3 phi request after direct done to validate the
   WACCMX_PHI_CACHE_AFTER_DONE branch.
2. Run a longer f19 direct-MPI cadence case with more than two neutral packets
   and continued phi cadence.
3. Keep f19 as the validated development grid; defer f09/distributed remap
   until continued cadence is stable.
4. Return to SAMI3 -> RAIJU/GAMERA physics blockers: traced flux-tube weighting,
   L/MLT mapping, and runtime blending/floors for scalar moments.
```

### Previous Completed Gate: Live Neutral Cadence + Direct Voltron Phi

The earlier same-stack WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-MPI
cadence gate is complete:

```text
jobid = 7670231
jobname = wxsami3_ndone
state = COMPLETED
exit = 0:0
elapsed = 00:08:52
node = qhcn119
batch MaxRSS = 64922552K
archive = logs/waccmx_live_directmpi_neutral_doneaware_dt300_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NEUTRAL_DONEAWARE_DT300_RESULT_20260525.md
```

This run validated the integrated online path:

```text
WACCM-X/CESM live neutral packets from CAM phys_state(:)
OpenMPI Voltron direct-MPI REMIX phi sender
SAMI3 online neutral receiver
SAMI3 direct phi receiver
two neutral packets at the 300 s CESM cadence
three changing phi frames
neutral/phi time-axis consistency
done-aware neutral receive/finalize ordering
```

All archived validators returned `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

Cadence conclusion: the SAMI3 neutral update gate must be tied to the CESM
packet cadence for multi-packet tests.  The receiver now uses:

```text
WXSAMI3_NEUTRAL_UPDATE_HOURS
WXSAMI3_NEUTRAL_SPAN_HOURS
```

with defaults preserving the older 0.25 hour behavior.  For this run both were
set to `0.08333333333333333`, matching the 300 s CESM packet cadence.

The neutral receiver is also done-aware: workers probe the next MPI tag before
expecting a neutral header, so a done tag arriving after the final packet is
stored and consumed during finalize instead of stranding the worker.

Next work order after this gate was:

```text
1. Replace SAMI3_PHI_SKIP_MADALA_AFTER_FINAL / WACCMX_SAMI3_PHI_STOP_AFTER_DONE
   with a continued production cadence policy.
2. Run a longer continued neutral/phi cadence case after the final-frame smoke
   policy is removed.
3. Keep f19 as the validated development grid, then design the f09/distributed
   live-neutral remap once cadence is stable.
4. Return to SAMI3 -> RAIJU/GAMERA physics blockers: traced flux-tube weighting,
   L/MLT mapping, and runtime blending/floors for scalar moments.
```

### WACCM-X/CESM -> SAMI3 Direct-Wait Phi Integration

Slurm:

```text
jobid = 7661005
jobname = wxsami3_ap2w
state = FAILED
exit = 1:0
elapsed = 00:06:23
batch MaxRSS = 60350988K
```

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000
```

This direct-wait file-based variant is no longer the active gate.  The current
active path is the direct-MPI Voltron sender on the same PRTE DVM, which is the
path validated by job `7670231`.

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

The earlier direct-MPI four-frame gate is complete:

```text
jobid = 7668967
jobname = wxsami3_dm4t1
state = COMPLETED
exit = 0:0
elapsed = 00:10:06
node = qhcn182
batch MaxRSS = 63607068K
archive = logs/waccmx_live_directmpi4_tphi1_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI4_RESULT_20260525.md
```

It validated one live neutral packet and four changing direct-MPI phi frames.
The follow-on `7670231` gate above extends this to two live neutral packets and
done-aware finalization.

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

1. Resume the SAMI3 -> RAIJU/GAMERA physical-moment blockers:
   - traced flux-tube volume weighting instead of simple/index weighting,
   - L/MLT or magnetic-tube geometry mapping instead of index resize,
   - explicit scalar-moment semantics for `Pavg/Davg/Pstd/Dstd/tiote`,
   - runtime blending/floors so density, pressure, std, and tiote can be staged
     independently.
2. Keep f19 as the validated online-control grid for now.  Design
   f09/distributed live neutral remap after the scalar-moment path is hardened.

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
scripts/validate_wxsami3_source_flag_balance.py
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
The source-flag balance validator now closes receiver-side source flags and
per-shell apply diagnostics against `wxsami3_live_meta.json`: total samples,
valid/invalid, above-top, N2 residual invalid, unknown flags, He native fallback,
W zero policy, and top-blend partitions must all agree.

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

## 2026-05-25 05:02 CST Update

The same-job Voltron phi writer + CESM/WACCM-X direct-wait run `7661005`
failed, but the failure is now isolated:

```text
archive = logs/waccmx_append2_directwait_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_DIRECTWAIT_FALSE_TIMEOUT_20260525.md
payload validator = overall=ok
source flag balance = ok
time-axis/topblend/runtime-map gates = ok
failure = WXSAMI3 phi payload wait timed out with correct 97044 byte payload present
```

Root cause: `wxsami3_wait_for_phi_payload()` opened the little-endian binary
payload without `convert='little_endian'`, while the sender read path and
payload writer both use little-endian.  That made the wait loop reject the
correct header and time out.

Patch applied to both the active CESM case SourceMod and the GitHub-tracked
SourceMod copy:

```text
code/cesm_source_mods/src.cam/wxsami3_online_stub_mod.F90
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523/SourceMods/src.cam/wxsami3_online_stub_mod.F90
```

The CESM case rebuilt successfully after the fix:

```text
build command used temporary CIME HOME:
  /home/jiaoy_group/jiaoy/data/CESM/experiments/cime_home_v3_qhslurm_20260525
case-local EXTRA_MACHDIR was cleared to avoid the v3 qhslurm fragment reload
MODEL BUILD HAS FINISHED SUCCESSFULLY
Total build time = 95.828171 seconds
```

Next immediate gate: commit/push this failure archive and endian wait fix, then
rerun direct-wait.  Acceptance is no timeout, two sender phi frames, two
receiver `WACCMX_PHI_RECV` records, receiver `MASTER: All Done!`, and strict
direct-wait archive `ok=true`.

## 2026-05-25 05:14 CST Update

The fixed direct-wait run passed:

```text
jobid = 7665666
jobname = wxsami3_ap2w
state = COMPLETED
exit = 0:0
elapsed = 00:08:05
node = qhcn644
archive = logs/waccmx_append2_directwait_fixed_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_DIRECTWAIT_FIXED_RESULT_20260525.md
archive ok = true
```

Key online markers:

```text
VOLTRON_WRITER_PID=2928528
DIRECT_WAIT_MODE=1
WXSAMI3 phi payload ready after wait ... size=97044 elapsed=1
WXSAMI3 sent phi payload frames: 2
WACCMX_PHI_RECV records: 2
MASTER: All Done!
END OF MODEL RUN
```

Strict gates passed:

```text
validate_wxsami3_append2_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_live_packet_contract = returncode 0
validate_wxsami3_time_axis = returncode 0
validate_wxsami3_topblend_policy = returncode 0
validate_wxsami3_runtime_map = returncode 0
```

The direct-wait launcher is patched so future runs stop the background Voltron
writer after CESM/SAMI3 complete.  In this fixed run the writer had already
produced the two-frame payload and the receiver had completed; manual stop was
used only to let the Slurm script continue to summary/replay QC instead of
idling on the standalone writer.

Immediate next work should move from control-path validation to production
coupling hardening:

```text
1. Replace file payload phi producer with a direct REMIX/Voltron -> SAMI3 online handoff.
2. Make f09/distributed live neutral remap explicit instead of f19 root-gather prototype.
3. Turn the top-blend policy into a production per-variable contract.
4. Continue SAMI3 -> RAIJU/GAMERA physical blockers: traced flux-tube weighting and geometry mapping.
```

## 2026-05-25 05:26 CST Update

The first direct REMIX/Voltron -> SAMI3 online phi handoff prototype passed as a
standalone SAMI3 validation:

```text
jobid = 7665788
jobname = sami3_dphi
state = COMPLETED
exit = 0:0
elapsed = 00:01:42
node = qhcn181
archive = logs/sami3_direct_phi_port_20260525/
doc = docs/MAGE1.25_notes/SAMI3_DIRECT_PHI_PORT_RESULT_20260525.md
```

This run separates the channels:

```text
neutral sender -> SAMI3 neutral MPI port
direct phi sender -> SAMI3 rank0 phi-only MPI port
```

Validated markers:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
WACCMX_PHI_RECV records = 2
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

Strict gates:

```text
validate_sami3_direct_phi_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
recv_qc_compare = compare ok
```

New implementation pieces:

```text
SAMI3 env contract: SAMI3_PHI_DIRECT_PORT_FILE
code/sami3_receiver/waccmx_neutral_mod.f90
scripts/wxsami3_phi_direct_sender_stub.c
scripts/validate_sami3_direct_phi_run.py
slurm/run_sami3_online_receiver_direct_phi_port_20260525.sbatch
```

This removes CESM from the online phi forwarding path for the validated
standalone test.  The remaining production blocker is that the direct phi
sender still reads the existing Voltron payload file; next step is to replace
that sender stub with a runtime REMIX/Voltron sender path.

## 2026-05-25 06:40 CST Update

The active REMIX/Voltron -> SAMI3 direct-phi route has moved from the standalone
sender stub to a runtime Voltron sender.  `voltron_mpi.x` was rejected for this
smoke because it enters the MPI Gamera coupler route and waits for a remote
Gamera app.  The working executable is the MPI-enabled serial `voltron.x`, where
only `waccmx_stub_backend.F90` uses MPI to connect to the SAMI3 phi-only port.

Current run:

```text
jobid = 7666704
launcher = slurm/run_sami3_intelmpi_voltron_runtime_direct_phi_20260525.sbatch
doc = docs/MAGE1.25_notes/SAMI3_INTELMPI_VOLTRON_RUNTIME_DIRECT_PHI_RESULT_20260525.md
archive snapshot = logs/sami3_intelmpi_voltron_runtime_direct_phi_20260525/
```

Validated in the live snapshot:

```text
Voltron runtime direct sender connected to SAMI3
Voltron sent two changing phi frames and done=2
SAMI3 received WACCMX_PHI_RECV frame 0 and frame 1
phi payload binary validator = overall=ok
direct-phi handshake validator with --allow-incomplete-run = overall=ok
```

Not yet complete:

```text
strict whole-run validator still fails until SAMI3 reaches finalize and writes
MASTER: All Done!, online done markers, and recv_qc_compare.txt.
```

Next decision gate is whether `7666704` naturally exits before its 30 minute
limit.  If it times out, the next implementation step is a dedicated
smoke-exit/finalize path; rerunning the same parameters is not useful.

## 2026-05-25 08:05 CST Update

The runtime Voltron -> SAMI3 direct-phi smoke now has a strict completed run:

```text
jobid = 7667186
jobname = sami3_vrtd
state = COMPLETED
exit = 0:0
elapsed = 00:04:38
doc = docs/MAGE1.25_notes/SAMI3_INTELMPI_VOLTRON_RUNTIME_DIRECT_PHI_RESULT_20260525.md
archive = logs/sami3_intelmpi_voltron_runtime_direct_phi_20260525/
```

Key markers:

```text
Voltron runtime direct sender connected to SAMI3
Voltron sent two changing phi frames and done=2
Voltron stopped after done via WACCMX_SAMI3_PHI_STOP_AFTER_DONE=1
SAMI3 received WACCMX_PHI_RECV frame 0 and frame 1
SAMI3 reached MASTER: All Done!
SAMI3 received neutral done and direct-phi done
recv_qc_compare = ok
validate_sami3_direct_phi_run strict = overall=ok
validate_remix_sami3_phi_payload = overall=ok
```

This remains a smoke/finalize completion, not production electrodynamics,
because it uses:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL=1
```

That switch only activates after the final available direct-phi frame has been
received; it now returns cached last phi for subsequent `potpphi` calls so the
short online MPI smoke can finalize without dropping to a zero-potential field.
The production next step is a real cadence policy for post-final-frame
potential solves and multi-frame REMIX timing.

## 2026-05-25 08:27 CST Update

The runtime Voltron -> SAMI3 direct-phi path now has a clean four-frame cadence
smoke:

```text
jobid = 7667369
jobname = sami3_vrtd4
state = COMPLETED
exit = 0:0
elapsed = 00:07:13
launcher = slurm/run_sami3_intelmpi_voltron_runtime_direct_phi_4frame_20260525.sbatch
archive = logs/sami3_intelmpi_voltron_runtime_direct_phi_4frame_20260525/
```

Key markers:

```text
SAMI3 ntmmax = 5
Voltron sent frame 0, 1, 2, 3 and done=4
SAMI3 received WACCMX_PHI_RECV frame 0, 1, 2, 3
SAMI3 reached MASTER: All Done!
recv_qc_compare = ok
validate_sami3_direct_phi_run strict = overall=ok
validate_remix_sami3_phi_payload = overall=ok
```

The QC parser was also hardened against interleaved Fortran stdout lines in
multi-frame runs.  It now accepts only the expected `WACCMX_RECV_QC`
continuation widths and skips unrelated `d = ...` or `WACCMX_APPLY_*`
diagnostic lines.

## 2026-05-25 09:03 CST Update

The direct REMIX/Voltron -> SAMI3 online phi route now also passes with the
OpenMPI/PRTE stack used by the WACCM-X/CESM live-neutral branch:

```text
jobid = 7668135
jobname = sami3_ovrtd
state = COMPLETED
exit = 0:0
elapsed = 00:05:23
node = qhcn012
archive = logs/sami3_openmpi_voltron_runtime_direct_phi_20260525/
doc = docs/MAGE1.25_notes/SAMI3_OPENMPI_VOLTRON_RUNTIME_DIRECT_PHI_RESULT_20260525.md
```

This run used:

```text
OpenMPI/PRTE SAMI3 receiver
OpenMPI neutral replay sender
OpenMPI-enabled serial voltron.x
one PRTE DVM
```

Key markers:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
Voltron sent WACCMX_SAMI3_PHI_DIRECT frame 0 and frame 1
SAMI3 received WACCMX_PHI_RECV frame 0 and frame 1
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL active; returning cached phi
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

Strict gates:

```text
validate_sami3_direct_phi_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
recv_qc_compare = ok
```

Important implementation note: OpenMPI `prun` did not reliably propagate the
Voltron direct-phi environment from the launcher subshell.  The working launcher
therefore exports every `WACCMX_SAMI3_PHI_*` variable explicitly with `prun -x`.

Immediate next work is to merge this OpenMPI direct Voltron phi route into the
existing live WACCM-X/CESM `phys_state(:)` neutral launcher.  That will replace
the current file-backed append/direct-wait phi handoff with a same-stack direct
Voltron -> SAMI3 MPI handoff.

## 2026-05-25 09:30 CST Update

The same-stack live WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-phi smoke now
passes:

```text
jobid = 7668385
jobname = wxsami3_dmpi
state = COMPLETED
exit = 0:0
elapsed = 00:07:10
node = qhcn005
batch MaxRSS = 63585144K
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
archive = logs/waccmx_live_directmpi_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_RESULT_20260525.md
```

This is the first completed integrated smoke where CESM/WACCM-X sends live
neutral forcing from CAM `phys_state(:)` while phi is sent by runtime OpenMPI
Voltron directly into the SAMI3 phi MPI port.  The old CESM file-backed phi
forwarding path is disabled in this launcher:

```text
WXSAMI3 phi payload enabled: F
```

Key markers:

```text
WXSAMI3 sent live neutral packet
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
WACCMX_SAMI3_PHI_DIRECT sent frame 0 and frame 1
WACCMX_SAMI3_PHI_DIRECT sent done=2
SAMI3 received WACCMX_PHI_RECV frame 0 and frame 1
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

Strict gates:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

This closes the current online control-path milestone.  It remains a prototype
physics coupling because the smoke still uses final-frame cache/stop controls:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL=1
WACCMX_SAMI3_PHI_STOP_AFTER_DONE=1
```

Next work should move from online handoff validation to production hardening:
multi-cycle REMIX/SAMI3 cadence, f09/distributed live-neutral remap,
production top-blend/fallback policy, and the SAMI3 -> RAIJU/GAMERA traced
flux-tube weighting plus L/MLT mapping.

## 2026-05-25 11:10 CST Update

The first controlled 2-packet live-neutral plus direct-Voltron-phi run completed
the model runtime path but exposed a validator semantics bug:

```text
jobid = 7669353
jobname = wxsami3_p2p1
state = FAILED
exit = 1:0
elapsed = 00:06:50
node = qhcn005
archive = logs/waccmx_live_directmpi_2pkt_phi1_postfix_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_POSTFIX_RESULT_20260525.md
```

Runtime markers showed the coupling path succeeded:

```text
CESM sent live neutral packet 0 at hour 0.00000000
CESM sent live neutral packet 1 at hour 0.0833333358
SAMI3 received 32 worker QC rows for packet 0
SAMI3 received 32 worker QC rows for packet 1
Voltron sent one direct phi frame with final-valid cache
SAMI3 received WACCMX_PHI_RECV frame 0
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 1
```

The failed validator was not filtering apply diagnostics correctly.  Receiver
diagnostics carry WACCM-X packet hour, but `WACCMX_APPLY_*` diagnostics carry
SAMI3 apply hour.  For this run packet 1 has receiver hour `0.0833333358` but
apply hour `0.25`.  The validator now selects the packet-index-th distinct
apply-hour block unless `--apply-hour` is provided.

Post-fix validation on the same run logs is fully green:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

A clean rerun with the fixed validator is active:

```text
jobid = 7669527
run = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_2pkt_phi1_clean_20260525_0000
purpose = produce a Slurm COMPLETED record for the same 2-packet + direct-phi gate
```

## 2026-05-25 11:15 CST Update

The clean rerun completed successfully:

```text
jobid = 7669527
jobname = wxsami3_p2p1c
state = COMPLETED
exit = 0:0
elapsed = 00:06:54
node = qhcn660
batch MaxRSS = 64901032K
archive = logs/waccmx_live_directmpi_2pkt_phi1_clean_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_CLEAN_RESULT_20260525.md
```

Runtime markers:

```text
CESM sent live neutral packet 0 at hour 0.00000000
CESM sent live neutral packet 1 at hour 0.0833333358
SAMI3 received packet 0 on 32 workers
SAMI3 received packet 1 on 32 workers
Voltron sent direct phi frame 0 with final-valid cache
SAMI3 received WACCMX_PHI_RECV frame 0
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 1
```

All batch validators passed:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

This closes the clean 2-packet coexistence gate.  The next target is production
cadence hardening: replace this forced `SAMI3_DT0=900.` / one-final-phi-frame
smoke with repeated neutral consumption and repeated Voltron/REMIX phi frames
without relying on the final-frame cache.

## 2026-05-25 11:32 CST Update

The next controlled 2-packet + 2-direct-phi cadence run was diagnostic rather
than successful:

```text
jobid = 7669625
jobname = wxsami3_p2p2
state = FAILED
exit = 16:0
elapsed = 00:05:51
node = qhcn660
archive = logs/waccmx_live_directmpi_2pkt_phi2_dt900_diag_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_2PHI_DIAGNOSTIC_20260525.md
```

Positive evidence:

```text
SAMI3 received WACCM-X packet 0 on 32 workers
SAMI3 received WACCM-X packet 1 on 32 workers
SAMI3 received direct phi frame 0 of 2
SAMI3 received direct phi frame 1 of 2
packet0 replay/QC max_rel = 4.83248e-13
packet1 replay/QC max_rel = 6.76502e-13
validate_remix_sami3_phi_payload = overall=ok
validate_wxsami3_time_axis_allow_incomplete = overall=ok
```

Failure mode:

```text
SAMI3 did not reach MASTER: All Done!
WACCM-X done and direct-phi done were not received before abort
SAMI3 printed Time step too small / vparallel diagnostics
PRTE reported MPI_ERRORS_ARE_FATAL
```

The run also exposed a sender metadata issue: `PHI_FRAME_HOUR_OFFSET` is
subtracted from Voltron runtime, not used as a frame interval.  With
`PHI_FRAME_HOUR_OFFSET=0.25`, the emitted frame hours were negative:

```text
frame0 hour = -0.248611107
frame1 hour = -0.247222215
```

Next implementation step: add an explicit diagnostic frame-hour override to the
Voltron sender, for example:

```text
WACCMX_SAMI3_PHI_FRAME_HOUR_BASE
WACCMX_SAMI3_PHI_FRAME_HOUR_STEP
```

so controlled cadence tests can emit `frame_hour = base + frame_index * step`
without changing the existing runtime-time based path.

## 2026-05-25 11:50 CST Update

The controlled 2-packet + 2-direct-phi cadence rerun now passes cleanly after
adding explicit Voltron direct-phi frame-hour base/step controls:

```text
jobid = 7669815
jobname = wxsami3_p2p2b
state = COMPLETED
exit = 0:0
elapsed = 00:07:42
node = qhcn005
archive = logs/waccmx_live_directmpi_2pkt_phi2_basestep_clean_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_2PHI_BASESTEP_CLEAN_RESULT_20260525.md
```

New direct-phi sender controls:

```text
WACCMX_SAMI3_PHI_FRAME_HOUR_BASE
WACCMX_SAMI3_PHI_FRAME_HOUR_STEP
frame_hour = base + frame_index * step
```

The successful run used:

```text
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.25
PHI_FRAME_HOUR_OFFSET = 0.0
PHI_MAX_FRAMES = 2
PHI_VALID_HOURS = 0.25
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
MAX_PACKETS = 2
```

Key markers:

```text
WXSAMI3 sent live neutral packet 0 at hour 0.00000000
WXSAMI3 sent live neutral packet 1 at hour 0.0833333358
WACCMX_SAMI3_PHI_DIRECT sent frame 0 hour=0.0 valid_until=0.25
WACCMX_SAMI3_PHI_DIRECT sent frame 1 hour=0.25 valid_until=1.0e30
WACCMX_SAMI3_PHI_DIRECT sent done=2
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 2
```

All archived gates returned `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance_packet0
validate_wxsami3_source_flag_balance_packet1
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

Current grid contract for this branch:

```text
WACCM-X source grid = f19 = 144 x 96 = 13824 CAM columns
SAMI3 neutral payload header = nz=304, nf=124, nl=5, nneut=7
```

Validator hardening in this update:

```text
validate_sami3_direct_phi_run.py now accepts the live CESM marker:
  WXSAMI3 sent done signal to SAMI3

validate_wxsami3_source_flag_balance.py now only applies wxsami3_live_meta.json
numeric closure when the selected packet index matches the metadata packet.
This keeps packet0 line/count validation from being compared against packet1
metadata in multi-packet runs where the live meta file records the latest packet.
```

Next work should use this clean two-stream gate as the baseline for longer
production-cadence hardening: more than one SAMI3 dynamic step, repeated
Voltron/REMIX phi frames without final-frame cache dependence, and then the
f09/distributed neutral remap plus SAMI3 -> RAIJU/GAMERA physical weighting and
geometry mapping blockers.

## 2026-05-25 12:04 CST Update

The follow-on repeated-cadence diagnostic with smaller `SAMI3_DT0` was
intentionally cancelled after it exposed the next blocker:

```text
jobid = 7670003
jobname = wxsami3_p2p3d300
state = CANCELLED by user
batch exit = 0:15
elapsed = 00:09:07
node = qhcn005
archive = logs/waccmx_live_directmpi_2pkt_phi3_dt300_diag_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_3PHI_DT300_DIAGNOSTIC_20260525.md
```

This run used:

```text
SAMI3_MAXSTEP = 2
SAMI3_DT0 = 300.
PHI_MAX_FRAMES = 3
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_VALID_HOURS = 0.08333333333333333
MAX_PACKETS = 2
```

Positive evidence:

```text
No Time step too small marker
No MPI_ERRORS_ARE_FATAL marker
Voltron sent phi frames at hours 0.0, 0.0833333358, 0.166666672
SAMI3 received all three WACCMX_PHI_RECV frames
SAMI3 reached MASTER: All Done!
validate_remix_sami3_phi_payload = overall=ok
validate_wxsami3_time_axis_allow_incomplete = overall=ok
```

Blocker:

```text
SAMI3 received only WACCM-X neutral packet 0:
  receiver packet count = 32 rows for packet 0, 0 rows for packet 1

Missing markers:
  WACCMX online done signal received
  SAMI3 direct phi done signal received
  WACCMX_SAMI3_PHI_DIRECT sent done
  WXSAMI3 sent done signal to SAMI3
  END OF MODEL RUN
```

Interpretation:

```text
DT0=300 removes the immediate SAMI3 numerical abort seen at DT0=900,
but SAMI3 can now outrun CESM/WACCM-X and finalize before the second live
neutral packet arrives.
```

Next implementation target: add a neutral-cadence synchronization policy rather
than tuning `DT0` further.  Candidate paths are a SAMI3 wait-at-coupling-boundary
mode, a CESM pre-send/startup gate, or a shared coupling clock that prevents
SAMI3 from advancing beyond the available WACCM-X packet stream.
