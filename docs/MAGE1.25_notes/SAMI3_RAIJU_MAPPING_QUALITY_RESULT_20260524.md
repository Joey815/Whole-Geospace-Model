# SAMI3 -> RAIJU Mapping Quality Datasets

Date: 2026-05-24

## Scope

This checkpoint turns the L/MLT mapping quality information from metadata-only
statistics into explicit HDF5 datasets in the stage-2 diagnostic product.

This does not change the runtime Fortran reader and does not make the mapping a
production Voltron traced-tube mapping.  It gives downstream checks concrete
arrays for coverage, interpolation, and extrapolation diagnostics.

## Code

Updated active files:

```text
scripts/sami3_moments/sami3_moments_to_raiju_diag.py
scripts/sami3_moments/validate_sami3_mage_moments.py
scripts/sami3_moments/README.md
```

Archived collaboration snapshot:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/
```

## New HDF5 Group

When a runtime `RaiCplMomentsOnly` layout is requested, stage 2 now writes:

```text
/MappingQuality/finite_moment_count_runtime
/MappingQuality/finite_all_moments_runtime_mask
```

For `--mapping-mode l_mlt`, it additionally writes:

```text
/MappingQuality/source_l
/MappingQuality/source_mlt_deg
/MappingQuality/target_l
/MappingQuality/target_mlt_deg
/MappingQuality/l_left_source_index
/MappingQuality/l_right_source_index
/MappingQuality/l_interp_weight
/MappingQuality/l_extrapolated_i
/MappingQuality/l_extrapolated_runtime_mask
/MappingQuality/mlt_left_source_index
/MappingQuality/mlt_right_source_index
/MappingQuality/mlt_interp_weight
```

The 2-D runtime quality masks use HDF5 order `(NJ, NI)`, matching
`/RaiCplMomentsOnly/tiote`.  The summary is mirrored in:

```text
metadata/json.raicpl_runtime_mapping_quality
metadata/json.raicpl_runtime_mapping.quality_summary
```

## Verification

Commands:

```text
python -m py_compile \
  scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  scripts/sami3_moments/validate_sami3_mage_moments.py

scripts/sami3_moments/run_sami3_mage_moments_smoke.sh \
  > analysis/sami3_mapping_quality_20260524.log 2>&1
```

Result:

```text
SAMI3 MAGE moments smoke passed
runtime_mapping=l_mlt
runtime_mapping_quality finite_all_fraction=1.0
```

The current `ds_over_B + l_mlt` product reports:

```text
finite_all_cell_count = 8460
finite_all_fraction = 1.0
l_extrapolated_i_count = 0
l_extrapolated_cell_count = 0
l_extrapolated_fraction = 0.0
source_l_min/max = 1.0141534559011587 / 1058.519161639254
target_l_min/max = 1.508787000709922 / 30.111605578372767
```

Dataset check:

```text
finite_moment_count_runtime shape = (188, 45)
finite_all_moments_runtime_mask shape = (188, 45)
l_extrapolated_runtime_mask shape = (188, 45)
source_l shape = (124,)
source_mlt_deg shape = (96,)
target_l shape = (45,)
target_mlt_deg shape = (188,)
```

## Interpretation

This closes the immediate audit gap where L/MLT coverage and extrapolation were
only present in JSON metadata.  Future runtime products can now be checked by
array, and plotting tools can show exactly which RAIJU cells are finite,
interpolated, or L-clamped.

The remaining physics blocker is still the same: the mapping is separable in L
and MLT and does not yet use Voltron traced-tube topology or `bvol`.

## Evidence

Archived under:

```text
logs/sami3_mapping_quality_20260524/
```

including the smoke log, mapping-quality summary, and updated JSON metadata for
the `ds_over_B + l_mlt` product.
