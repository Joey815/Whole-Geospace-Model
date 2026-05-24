# SAMI3 -> RAIJU Recommended Prototype 1800s Launch

Date: 2026-05-25

## Scope

This launches the next conservative stability check after the completed 900s
recommended prototype run.  It does not change the moment adapter settings.
Only the baseline/control duration is extended from 900s to 1800s.

Prototype settings remain:

```text
weight-mode = ds_over_B
mapping-mode = l_mlt
density-mode = num
pressure-mode = ion
alphaDavg = 0.05
alphaPavg = 0.05
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
moments/useStateTioteForIngest = T
```

Launcher:

```text
slurm/run_sami3_raiju_recommended_long1800_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long1800_20260525
```

Submitted job:

```text
jobid = 7663122
jobname = sami3_rai_long1800
partition = intel
node = qhcn065
state at 2026-05-25 03:11:48 CST = RUNNING
time limit = 06:00:00
```

## Acceptance After Completion

Run the strict validator:

```text
python3 scripts/validate_sami3_raiju_longrun.py \
  --run-dir /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long1800_20260525 \
  --label long1800 \
  --expect-slurm \
  --json-output /tmp/sami3_raiju_long1800_strict.json
```

Expected acceptance:

```text
baseline log reaches Fin
recommended log reaches Fin
RAIJU/GAMERA history write counts are non-trivial
fatal markers absent
expected baseline/recommended HDF5 products exist
Slurm output contains run_complete=1
```

Then generate the compact result summary and archive the small evidence under:

```text
logs/sami3_dsB_lmlt_recommended_long1800_20260525/
```

The long-run archive helper can run the strict validator, generate the HDF5
summary through the local `mage-vis` h5py environment, and copy the small
evidence:

```text
python3 scripts/archive_sami3_raiju_longrun_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long1800_20260525 \
  --archive-dir logs/sami3_dsB_lmlt_recommended_long1800_20260525 \
  --label long1800 \
  --job-id 7663122
```

Do not commit the large HDF5 history/restart products.

## Interpretation

If this passes, it extends the current recommended scalar-moment prototype
stability evidence from 900s to 1800s at the same conservative blend settings.
It still does not resolve the production mapping blocker: the current
`ds_over_B + l_mlt` path remains a prototype, not a true traced flux-tube volume
map.
