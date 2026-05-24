# SAMI3 -> RAIJU Longrun Archive Workflow

Date: 2026-05-25

## Scope

This checkpoint adds a small post-run archiver for SAMI3 -> RAIJU/GAMERA
long-run smoke tests.

New script:

```text
scripts/archive_sami3_raiju_longrun_result.py
```

It runs:

```text
scripts/validate_sami3_raiju_longrun.py --label <label> --expect-slurm
```

and copies only lightweight evidence:

```text
base_control_<label>.log
dsB_lmlt_recommended_<label>.log
tinyCase_base_control_<label>.xml
tinyCase_sami3_moments_dsB_lmlt_recommended_<label>.xml
recommended_<label>_summary.txt, if present
slurm-*.out
sacct_<jobid>.txt
validator JSON/text outputs
archive_summary.json
```

It deliberately does not copy the large HDF5 history/restart products.

## Smoke Test

Smoke-tested against the completed long900 run:

```text
python3 scripts/archive_sami3_raiju_longrun_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long900_20260525 \
  --archive-dir /tmp/sami3_raiju_long900_archive_smoke_20260525 \
  --label long900 \
  --job-id 7660334
```

Result:

```text
validator_returncode = 0
copied_files = 7
overall = ok
```

## Use On Long1800

After the current long1800 job completes:

```text
python3 scripts/archive_sami3_raiju_longrun_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long1800_20260525 \
  --archive-dir logs/sami3_dsB_lmlt_recommended_long1800_20260525 \
  --label long1800 \
  --job-id 7663122
```

Then add the small archive directory and result note to GitHub.  Keep the HDF5
products in the local run directory.
