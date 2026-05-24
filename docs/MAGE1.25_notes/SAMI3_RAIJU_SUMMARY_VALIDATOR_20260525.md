# SAMI3 -> RAIJU/GAMERA Summary Validator

Date: 2026-05-25

## Scope

This adds a pass/fail validator for the HDF5 summary generated from paired
baseline and SAMI3-recommended RAIJU/GAMERA runs:

```text
scripts/validate_sami3_raiju_summary.py
```

The existing summary script computes the blending formula residuals,
non-finite field lists, and baseline-vs-recommended response metrics.  This new
gate turns those diagnostics into archive acceptance criteria.

## Checks

The validator currently checks:

```text
summary JSON exists
Pavg/Davg/Pstd/Dstd blending formula max_abs <= tolerance
Pavg/Davg/Pstd/Dstd blending formula max_rel <= tolerance
Pavg and Davg actual values are positive when requested
baseline and prototype RAIJU/GAMERA restart nonfinite lists are empty
RAIJU and GAMERA history last-step names exist
RAIJU and GAMERA history last-step names match when requested
restart and history comparison fields are present
restart and history comparison stats are finite
```

The long-run archive helper now runs this validator automatically after
`summarize_sami3_raiju_longrun.py` for completed runs.

## Interim Long1800 Result

The currently running `long1800` case was checked while still in progress:

```text
run = analysis/runtime_ingest_long1800_20260525
label = long1800
Pavg_formula_max_abs = 0.0
Davg_formula_max_abs = 0.0
Pstd_formula_max_abs = 0.0
Dstd_formula_max_abs = 0.0
Pavg_actual_mean = 0.0016012076243789371
Davg_actual_mean = 99.32539397052527
nonfinite restart lists = []
history_last_step = Step#85 for both RAIJU and GAMERA
overall = ok
```

Because this is an interim read while Slurm job `7663122` is still running, it
does not replace the final archive.  It verifies that the recommended branch is
still obeying the exact runtime blending formula and has not produced nonfinite
restart state so far.

## Evidence

Archived under:

```text
logs/sami3_raiju_summary_validation_20260525/
```

including:

```text
long1800_interim_summary.json
long1800_interim_summary.txt
long1800_interim_validate.json
long1800_interim_validate.txt
```
