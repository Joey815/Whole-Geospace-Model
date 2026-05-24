# SAMI3 -> RAIJU TubeShell Extrapolation Flag Propagation

Date: 2026-05-24

## Purpose

The previous TubeShell weight-file prototype recorded the intermediate
SAMI3-to-Voltron `l_extrapolated_mask`, but the composed
Voltron-to-RAIJU product always wrote a zero final
`/quality/extrapolation_flag`.

That was harmless for the current tiny target because the 164 clamped
intermediate TubeShell cells do not contribute to the active RAIJU target
cells.  It was still a contract bug for future grids: if a clamped intermediate
cell does contribute later, `--runtime-mask-policy coverage_closed_no_extrap`
must be able to reject the corresponding RAIJU cell.

## Code Change

Updated:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/build_sami3_to_raiju_weights.py
```

`compose_sami3_voltron_raiju_weights` now accepts an optional
`voltron_extrapolated_mask`.  During SAMI3->Voltron->RAIJU composition it marks
the final target cell if any contributing Voltron intermediate cell came from a
clamped SAMI3 L query.

New metadata fields:

```text
intermediate_extrapolated_source_terms
intermediate_extrapolated_target_count
```

For composed mappings, `quality/l_extrapolated_i` is now derived from the final
2-D `quality/extrapolation_flag` instead of being hard-coded to zero.

## Unit Check

A minimal synthetic composition test was run:

```text
logs/sami3_tubeshell_extrapflag_20260524/compose_extrapflag_unit.log
```

Result:

```text
compose_extrapflag_unit passed
extrapolation_flag_count 1
intermediate_extrapolated_source_terms 1
intermediate_extrapolated_target_count 1
```

This proves the propagation path works when an extrapolated intermediate cell
does contribute to a final target.

## Regenerated TubeShell Weight File

Committed small weight artifact:

```text
logs/sami3_tubeshell_extrapflag_20260524/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_extrapflag_20260524.h5
logs/sami3_tubeshell_extrapflag_20260524/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_extrapflag_20260524.json
```

Generation summary:

```text
mapping_mode = voltron_tubeshell_l_mlt
voltron_tube_longitude = lon0
sparse_weight_count = 33840
coverage_count_min/max = 4 / 4
weight_sum_min/max = 0.9999998807907104 / 1.0000001192092896
sami3_to_voltron_l_extrapolated_count = 164
intermediate_extrapolated_source_terms = 0
intermediate_extrapolated_target_count = 0
quality/extrapolation_flag count = 0
closed_field_cell_count = 8460
closed_field_fraction = 1.0
```

Interpretation: the current target still has no final extrapolated cells.  The
new file therefore remains numerically equivalent to the previous TubeShell
lon0 product, but the future-grid flag propagation is now implemented.

## Stage-2 Validation

Stage-2 product was generated with:

```text
--mapping-mode weights
--runtime-mask-policy coverage_closed_no_extrap
```

Local diagnostic HDF5, not committed:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_extrapflag_20260524.h5
```

Committed sidecar:

```text
logs/sami3_tubeshell_extrapflag_20260524/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_extrapflag_20260524.json
```

Validation result:

```text
validate_extrapflag_policy: passed
runtime_mask_policy = coverage_closed_no_extrap
runtime_valid_count = 8460
extrapolation_flag_runtime_count = 0
coverage_count_runtime min/max = 4 / 4
RaiCplMomentsOnly Pavg/Davg/Pstd/Dstd/tiote max_abs vs prior policy product = 0.0
```

Because final extrapolation count is zero for this target, no new runtime smoke
was necessary; the generated runtime payload is byte-for-byte equivalent in the
checked scalar moment arrays and masks to the already validated policy product.

## Next Step

The mask contract now covers finite values, mapping coverage, target closed
field state, and propagated intermediate extrapolation.  The next physical step
is to improve the actual geometry:

```text
replace the current Lb/lon0 interpolation with a bvol-aware traced-tube remap,
then rerun the same coverage_closed_no_extrap runtime smoke on a product where
some cells are intentionally rejected.
```
