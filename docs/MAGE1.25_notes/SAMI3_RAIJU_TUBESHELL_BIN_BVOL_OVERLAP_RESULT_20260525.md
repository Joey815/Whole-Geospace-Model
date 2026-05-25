# SAMI3 -> RAIJU TubeShell bVol-Overlap Mapping Prototype

Date: 2026-05-25 CST

## Purpose

This checkpoint advances the previous `bin_bvol_cc` center-binning prototype.
Instead of assigning each Voltron TubeShell cell center to one RAIJU target
cell, the new mode:

```text
--voltron-compose-weight-mode bin_bvol_overlap
```

estimates each TubeShell source cell footprint from corner `Lb` and `lon0`
and distributes `bVol_cc` over every overlapped RAIJU L/longitude bin before
per-target normalization.

This is still a prototype.  It is not yet a production traced-tube quadrature,
but it removes the strongest limitation of center-only binning and adds a
geometry QC gate for pathological TubeShell cells.

## Code Change

Updated:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/build_sami3_to_raiju_weights.py
code/kaiju_sami3_moments/scripts/sami3_moments/README.md
```

New behavior:

```text
--voltron-compose-weight-mode bin_bvol_overlap
--voltron-overlap-max-l-span 20
--voltron-overlap-max-lon-span 10
```

The QC gate skips source cells with excessive corner footprint spans so a small
number of boundary/topology cells cannot smear bVol over unrelated target bins.

## Generated Weight File

Committed artifacts:

```text
logs/sami3_tubeshell_bin_bvol_overlap_20260525/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_20260525.h5
logs/sami3_tubeshell_bin_bvol_overlap_20260525/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_20260525.json
```

Generation summary:

```text
schema_version = 5
mapping_mode = voltron_tubeshell_l_mlt
voltron_tube_longitude = lon0
voltron_compose_weight_mode = bin_bvol_overlap
sparse_weight_count = 46969
coverage_count_min/max = 0 / 12
positive target cells = 8100 / 8460
runtime valid fraction = 0.9574468085106383
weight_sum_valid max deviation = 1.1920928955078125e-07
l_extrapolated_cell_count = 0
skipped_large_footprint = 1392
overlap_max_terms_per_source_cell = 39
overlap_used_l_span_max = 4.1430025303357425
overlap_used_lon_span_max = 2.0000000000001137
```

Compared with old `bin_bvol_cc`, coverage improves:

```text
old valid count = 5940
new valid count = 8100
shared valid count = 5940
new-only valid count = 2160
old-only valid count = 0
```

Shared-cell moment changes remain moderate after the geometry QC gate:

```text
Pavg shared_rms = 0.0028880704194307327
Davg shared_rms = 215.2569580078125
Pavg shared mean old/new = 0.06074320524930954 / 0.05927674099802971
Davg shared mean old/new = 5045.98828125 / 4939.8193359375
```

## Stage-2 Product

Stage-2 product:

```text
logs/sami3_tubeshell_bin_bvol_overlap_20260525/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_20260525.h5
logs/sami3_tubeshell_bin_bvol_overlap_20260525/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_20260525.json
```

Validated with:

```text
validate_sami3_raiju_mapping_product.py
  --expect-mapping-mode weights
  --min-valid-fraction 0.95
  --min-finite-all-fraction 1.0
  --max-extrapolated-fraction 0.0
  --weight-sum-tol 1e-5
```

Result:

```text
overall = ok
runtime_valid_fraction = 0.9574468085106383
coverage_valid_positive valid_min = 4
weight_sum_valid_near_one max_dev = 1.1920928955078125e-07
tiote masked range = 0.8749623894691467 / 1.0004475116729736
```

## Runtime Smoke

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_smoke_20260525
```

Prototype job:

```text
jobid = 7674022
jobname = sami3_bvol_ov_smk
state = COMPLETED
exit = 0:0
elapsed = 00:01:02
node = qhcn049
batch MaxRSS = 1018724K
```

Baseline job:

```text
jobid = 7674051
jobname = base_bvol_ov_smk
state = COMPLETED
exit = 0:0
elapsed = 00:01:02
node = qhcn287
batch MaxRSS = 1018648K
```

Runtime settings:

```text
tFin = 11.5 s
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 0.0
```

Runtime validators:

```text
validate_runtime_bvol_overlap_smoke_pair.txt: overall=ok
validate_bvol_overlap_smoke_summary.txt: overall=ok
```

Formula checks against the baseline restart are exact:

```text
Pavg_formula_max_abs = 0
Davg_formula_max_abs = 0
Pstd_formula_max_abs = 0
Dstd_formula_max_abs = 0
```

Physics restart nonfinite checks are clean:

```text
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
```

## Interpretation

`bin_bvol_overlap` is now the preferred mapping prototype for the next
SAMI3->RAIJU runtime gate.  It has better target coverage than center binning,
keeps pressure/std/tiote disabled in runtime blending, and passes both offline
mapping validation and paired runtime smoke validation.

The next gate should be a longer conservative run:

```text
mapping = bin_bvol_overlap
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 0.0
duration = 1800 s
```

Pressure ingest should remain disabled until the RAIJU/GAMERA `Pavg` semantics
are settled.
