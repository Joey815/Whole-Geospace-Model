# SAMI3 -> RAIJU Explicit Mapping Weight File

Date: 2026-05-24

## Scope

This checkpoint moves the current prototype `L/MLT` runtime mapping out of the
stage-2 adapter's inline code path and into an explicit sparse HDF5 weight-file
contract.

The generated file is still based on the existing separable `L/MLT`
interpolation.  It is not yet a Voltron traced-tube or `bvol` production
mapping.  The purpose of this step is to make the mapping interface explicit,
auditable, and replaceable.

## Code

Updated active files:

```text
scripts/sami3_moments/build_sami3_to_raiju_weights.py
scripts/sami3_moments/sami3_moments_to_raiju_diag.py
scripts/sami3_moments/validate_sami3_mage_moments.py
scripts/sami3_moments/run_sami3_mage_moments_smoke.sh
scripts/sami3_moments/README.md
```

Archived collaboration snapshot:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/
```

## Weight File Contract

New generator:

```text
build_sami3_to_raiju_weights.py \
  sami3_moments_stubpayload_ds_over_B_20260524.h5 \
  --out sami3_to_raiju_weights_l_mlt_20260524 \
  --raicpl-template sami3_moments_base_control.raiCpl.Res.00000.h5
```

The current generated file is:

```text
analysis/sami3_to_raiju_weights_l_mlt_20260524.h5
```

It is also archived in the collaboration repo as a small verification artifact:

```text
logs/sami3_weightfile_mapping_20260524/sami3_to_raiju_weights_l_mlt_20260524.h5
```

HDF5 layout:

```text
/src/L
/src/MLT_deg
/src/tube_L
/src/nf_index
/src/nlt_index

/dst/L
/dst/MLT_deg
/dst/shell_index
/dst/mlt_index

/map/dst_index
/map/src_index
/map/weight
/map/corner
/map/l_left_source_index
/map/l_right_source_index
/map/l_interp_weight
/map/mlt_left_source_index
/map/mlt_right_source_index
/map/mlt_interp_weight

/quality/coverage_count
/quality/weight_sum
/quality/extrapolation_flag
/quality/closed_field_mask
/quality/l_extrapolated_i

/metadata/json
```

Sparse-index convention:

```text
/map/dst_index columns = runtime j,i
/map/src_index columns = SAMI3 nf,nlt
```

Current file attributes:

```text
product = sami3_to_raiju_mapping_weights
schema_version = 1
mapping_mode = l_mlt_separable
physical_validity = prototype
source_shape_nf_nlt = [124, 96]
target_shape_ni_nj = [45, 188]
```

Quality summary:

```text
sparse_weight_count = 33840
coverage_count_min = 4
coverage_count_max = 4
weight_sum_min = 1.0
weight_sum_max = 1.0
l_extrapolated_cell_count = 0
```

`closed_field_mask` is present but is currently all one.  That is an explicit
prototype placeholder because this file does not yet encode traced-field
topology or a production closed-field policy.

## Stage-2 Consumption

The stage-2 adapter now supports:

```text
--mapping-mode weights
--mapping-weight-file sami3_to_raiju_weights_l_mlt_20260524.h5
```

If no `--raicpl-template` or `--target-raicpl-shape` is supplied, the runtime
target shape is inferred from the weight file.

The resulting product records:

```text
metadata/json.raicpl_runtime_mapping.mode = weights
metadata/json.raicpl_runtime_mapping.weight_file = ...
metadata/json.raicpl_runtime_mapping_quality.weight_file_mapping_mode = l_mlt_separable
```

and writes the usual runtime group:

```text
/RaiCplMomentsOnly/Pavg
/RaiCplMomentsOnly/Davg
/RaiCplMomentsOnly/Pstd
/RaiCplMomentsOnly/Dstd
/RaiCplMomentsOnly/tiote
```

## Verification

Commands:

```text
python -m py_compile \
  scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  scripts/sami3_moments/build_sami3_to_raiju_weights.py \
  scripts/sami3_moments/validate_sami3_mage_moments.py

bash -n scripts/sami3_moments/run_sami3_mage_moments_smoke.sh

scripts/sami3_moments/run_sami3_mage_moments_smoke.sh \
  > analysis/sami3_weightfile_mapping_20260524.log 2>&1
```

Result:

```text
SAMI3 MAGE moments smoke passed
runtime_mapping=weights
runtime_mapping_quality finite_all_fraction=1.0
```

The smoke compares the old inline `l_mlt` output against the new
weight-file-driven output for the current `ds_over_B + l_mlt` product:

```text
RaiCplMomentsOnly/Pavg  max_abs = 1.4901161193847656e-08  max_rel = 1.4901161193847656e-08
RaiCplMomentsOnly/Davg  max_abs = 0.001953125             max_rel = 1.1794265085779101e-07
RaiCplMomentsOnly/Pstd  max_abs = 2.9802322387695312e-08  max_rel = 2.9802322387695312e-08
RaiCplMomentsOnly/Dstd  max_abs = 0.00390625              max_rel = 1.189390305446135e-07
RaiCplMomentsOnly/tiote max_abs = 5.960464477539063e-08   max_rel = 5.960464477539063e-08
```

Overall:

```text
weight-file mapping equivalence max_abs = 0.00390625
weight-file mapping equivalence max_rel = 1.189390305446135e-07
```

The absolute differences are from `float32` HDF5 write-rounding.  The relative
difference confirms that the new explicit weight-file path is numerically
equivalent to the old inline `l_mlt` mapper for this prototype.

## Interpretation

This closes the immediate engineering gap between "we have a prototype L/MLT
mapper" and "we have a replaceable mapping artifact".  Future work can now
replace `sami3_to_raiju_weights_l_mlt_20260524.h5` with a Voltron traced-tube
or `bvol`-consistent file without changing the runtime HDF5 product layout or
the Fortran ingest hook.

The remaining physics blocker is therefore narrower and clearer:

```text
replace l_mlt_separable sparse weights with Voltron traced-tube / bvol-aligned weights
```

## Evidence

Archived under:

```text
logs/sami3_weightfile_mapping_20260524/
```

including the smoke log, the mapping-weight HDF5 file, the mapping-weight JSON,
and the weight-file-driven diagnostic JSON.
