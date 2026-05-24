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

### Full WACCM-X/CESM -> SAMI3 Append2 Integration

Slurm:

```text
jobid = 7659727
jobname = wxsami3_ap2
state = PENDING
reason = Priority
requested = 1 intel node, 49 tasks, 296G
scheduled node hint = qhcn332
estimated start = 2026-05-25 08:41:49 CST
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
python3 scripts/validate_wxsami3_append2_run.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525_0000 \
  --expected-phi-frames 2
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

### SAMI3 -> RAIJU/GAMERA Recommended Long900

Slurm:

```text
jobid = 7660334
jobname = sami3_rai_long900
state = RUNNING
node = qhcn095
settings = alphaDavg=0.05, alphaPavg=0.05, alphaTiote=1.0, alphaPstd=0, alphaDstd=0
```

Launcher:

```text
slurm/run_sami3_raiju_recommended_long900_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long900_20260525
```

Running-state gate:

```bash
python3 scripts/validate_sami3_raiju_longrun.py \
  --run-dir /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long900_20260525 \
  --allow-incomplete \
  --expect-slurm
```

Completion gate:

```bash
python3 scripts/validate_sami3_raiju_longrun.py \
  --run-dir /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long900_20260525 \
  --expect-slurm
```

This must show both baseline/control and recommended runs reached `Fin`, wrote
RAIJU/GAMERA HDF5 outputs, contain no fatal markers, and produced the expected
restart products.

## Next Work Order

1. Keep polling jobs `7659727` and `7660334`.
2. When `7660334` completes, run the strict long900 validator, archive the
   compact logs/results, write the result note, and push to GitHub.
3. When `7659727` completes, run the append2 validator, archive the compact
   full-integration evidence, write the result note, and push to GitHub.
4. If the full append2 job remains queued, continue implementation work on the
   remaining production blockers:
   - strict same-call-site live-vs-offline source-state validation,
   - production top-blend policy,
   - direct live REMIX/Voltron phi producer to online MPI sender path,
   - true traced flux-tube volume map for SAMI3 -> RAIJU/GAMERA,
   - finer f09/distributed remap design.
