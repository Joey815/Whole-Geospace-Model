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

Status refreshed: 2026-05-25 03:51:14 CST.

### Full WACCM-X/CESM -> SAMI3 Append2 Integration

Slurm:

```text
jobid = 7659727
jobname = wxsami3_ap2
state = PENDING
reason = Priority
requested = 1 intel node, 49 tasks, 296G
```

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525_0000
```

Completion gate:

```bash
python3 scripts/archive_wxsami3_append2_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525_0000 \
  --archive-dir logs/waccmx_append2_full_20260525 \
  --job-id 7659727 \
  --expected-phi-frames 2 \
  --expected-live-packets 1 \
  --require-nonzero-phi \
  --require-receiver-phi-values \
  --require-changing-phi-frames \
  --expect-top-blend-mode linear \
  --expect-blend-bottom-km 600 \
  --expect-blend-top-km 720 \
  --min-total-blend-cells 1 \
  --require-zero-unknown-source-flags \
  --require-he-native \
  --require-w-zero \
  --weights-nc /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc \
  --expected-runtime-map-nsource 13824
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
```

### WACCM-X/CESM -> SAMI3 Direct-Wait Phi Integration

Slurm:

```text
jobid = 7661005
jobname = wxsami3_ap2w
state = PENDING
reason = Dependency
dependency = afterok:7659727
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
python3 scripts/archive_wxsami3_append2_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000 \
  --archive-dir logs/waccmx_append2_directwait_20260525 \
  --job-id 7661005 \
  --expected-phi-frames 2 \
  --expected-live-packets 1 \
  --expect-phi-wait-marker \
  --expect-direct-wait-mode \
  --require-nonzero-phi \
  --require-receiver-phi-values \
  --require-changing-phi-frames \
  --expect-top-blend-mode linear \
  --expect-blend-bottom-km 600 \
  --expect-blend-top-km 720 \
  --min-total-blend-cells 1 \
  --require-zero-unknown-source-flags \
  --require-he-native \
  --require-w-zero \
  --weights-nc /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc \
  --expected-runtime-map-nsource 13824
```

This must additionally show:

```text
DIRECT_WAIT_MODE=1
VOLTRON_WRITER_PID=<pid>
WXSAMI3 phi payload ready after wait
```

### SAMI3 -> RAIJU/GAMERA Recommended Long1800

Slurm:

```text
jobid = 7663122
jobname = sami3_rai_long1800
state = RUNNING
node = qhcn065
elapsed = 00:39:28 at 2026-05-25 03:51:14 CST
settings = alphaDavg=0.05, alphaPavg=0.05, alphaTiote=1.0, alphaPstd=0, alphaDstd=0
```

Launcher:

```text
slurm/run_sami3_raiju_recommended_long1800_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long1800_20260525
```

Running-state gate:

```bash
python3 scripts/validate_sami3_raiju_longrun.py \
  --run-dir /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long1800_20260525 \
  --label long1800 \
  --allow-incomplete \
  --expect-slurm
```

Completion gate:

```bash
python3 scripts/archive_sami3_raiju_longrun_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long1800_20260525 \
  --archive-dir logs/sami3_dsB_lmlt_recommended_long1800_20260525 \
  --label long1800 \
  --job-id 7663122
```

This must show both baseline/control and recommended runs reached `Fin`, wrote
RAIJU/GAMERA HDF5 outputs, contain no fatal markers, and produced the expected
restart products.

### Completed Stability Gate

The previous 900 second recommended prototype gate is complete:

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

1. Keep polling jobs `7659727`, `7661005`, and `7663122`.
2. When `7663122` completes, run the strict long1800 validator, archive the
   compact logs/results, write the result note, and push to GitHub.
3. When `7659727` completes, run the append2 archiver, archive the compact
   full-integration evidence, write the result note, and push to GitHub.
4. When dependency job `7661005` completes, run the direct-wait archiver with
   `--expect-phi-wait-marker --expect-direct-wait-mode`, write the result note,
   and push to GitHub.
5. If the full WACCM-X jobs remain queued, continue implementation work on the
   remaining production blockers:
   - production cadence/f09 live source-state validation beyond the current
     f19 same-call-site replay gate,
   - production top-blend height and per-variable policy,
   - direct live REMIX/Voltron phi producer to online MPI sender path,
   - true traced flux-tube volume map for SAMI3 -> RAIJU/GAMERA,
   - finer f09/distributed remap design.

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
