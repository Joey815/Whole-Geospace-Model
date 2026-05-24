# SAMI3 -> RAIJU Mapping Product Validator

Date: 2026-05-25

## Scope

This adds a small HDF5 validator for SAMI3 -> RAIJU stage-2 products that carry
the runtime moment group and explicit mapping diagnostics:

```text
scripts/validate_sami3_raiju_mapping_product.py
```

The validator is intended for products such as:

```text
RaiCplMomentsOnly/
MappingQuality/
```

It checks the scalar-moment arrays used by the runtime hook plus the mapping
quality fields used to judge coverage, extrapolation, finite values, and sparse
weight normalization.

## Checks

The current validator checks:

```text
product exists
RaiCplMomentsOnly group exists
MappingQuality group exists
mapping_mode matches the expected mode when requested
Pavg/Davg/Pstd/Dstd and masks exist
Pavg/Davg/Pstd/Dstd are finite
moment arrays and masks have matching runtime shapes
tiote and tiote_mask exist and are finite
finite_all_moments_runtime_mask fraction meets threshold
runtime_valid_mask fraction meets threshold
extrapolation mask fraction stays below threshold
coverage_count_runtime is non-negative
valid mapped cells have positive coverage
weight_sum_runtime is near one on valid mapped cells
source and target coordinates are finite
L coordinates are positive
MLT coordinates are in [0, 360]
source coordinate axes are monotonic
```

Target-grid monotonicity is not required by default because RAIJU runtime arrays
can be stored in model-layout order rather than sorted coordinate order.  A
strict target-order check can still be enabled with:

```text
--require-target-monotonic
```

## Validation Results

Two existing 2026-05-24 stage-2 products were validated with the new script.

Inline L/MLT product:

```text
product = sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524.h5
expected mapping_mode = l_mlt
finite_all_fraction = 1.0
runtime_valid_fraction = 1.0
extrapolated_fraction = 0.0
overall = ok
```

Voltron TubeShell bVol-binned product:

```text
product = sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvolcc_20260524.h5
expected mapping_mode = weights
finite_all_fraction = 1.0
runtime_valid_fraction = 0.7021276595744681
coverage_count_min = 0
coverage_count_max = 6
valid coverage_count_min = 4
extrapolated_fraction = 0.0
weight_sum_valid_max_deviation = 1.1920928955078125e-07
overall = ok
```

## Interpretation

This validator is a production-hardening check for the current prototype
mapping artifacts.  It does not by itself make the mapping physically final.
The bVol-binned product still has intentionally invalid uncovered target cells,
and the current coordinate mapping remains a prototype approximation rather
than a traced flux-tube-volume map.

The useful new checkpoint is that the existing stage-2 products now have a
repeatable, scriptable QC gate before runtime ingest or longer stability scans.

## Evidence

Archived under:

```text
logs/sami3_mapping_product_validation_20260525/
```

including text and JSON validation output for:

```text
l_mlt_validate.txt
l_mlt_validate.json
bin_bvolcc_validate.txt
bin_bvolcc_validate.json
```
