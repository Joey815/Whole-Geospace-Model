# SAMI3 -> RAIJU Voltron TubeShell Coordinate Weight Prototype

Date: 2026-05-24

## Scope

This checkpoint adds a more geometry-aware prototype mapping mode:

```text
--mapping-mode voltron_tubeshell_l_mlt
```

The previous schema-3 `voltron_shell_l_mlt` mode used Voltron's ShellGrid
cell-center L/MLT as the intermediate coordinate.  This new mode maps SAMI3 to
the actual Voltron TubeShell cell-centered traced-tube coordinates:

```text
SAMI3 L/MLT grid
-> Voltron TubeShell Lb + lon0/lonc
-> RAIJU ShellGrid
```

This is still a prototype, not production physics.  It tests the traced-tube
coordinate plumbing, but it does not yet implement a full flux-tube-volume or
`bvol`-weighted remap.

## Code

Updated files:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/build_sami3_to_raiju_weights.py
code/kaiju_sami3_moments/scripts/sami3_moments/README.md
```

New options:

```text
--mapping-mode voltron_tubeshell_l_mlt
--voltron-tube-longitude lon0
--voltron-tube-longitude lonc
```

The weight file remains `schema_version=3` and still writes the same direct
runtime contract:

```text
/map/dst_index
/map/src_index
/map/weight
/quality/*
```

Additional intermediate diagnostics include:

```text
/intermediate/Lb_cc
/intermediate/lon0_cc_deg
/intermediate/lonc_cc_deg
/intermediate/lat0_cc_rad
/intermediate/latc_cc_rad
/intermediate/sami3_to_voltron/l_extrapolated_mask
```

## Generated Products

Archived evidence:

```text
logs/sami3_voltron_tubeshell_weightfile_20260524/
```

Included small artifacts:

```text
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_20260524.h5
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_20260524.json
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lonc_20260524.h5
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lonc_20260524.json
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_closedmask_20260524.json
sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_20260524.json
sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lonc_20260524.json
sami3_voltron_tubeshell_l_mlt_20260524.log
sami3_voltron_tubeshell_l_mlt_20260524_summary.txt
```

The generated stage-2 diagnostic HDF5 products are local only and listed in
`manifests/large_artifacts_not_committed.txt`.

## Validation

Both `lon0` and `lonc` TubeShell-coordinate products validate through the
existing stage-2 validator:

```text
runtime_mapping = weights
runtime_mapping_quality finite_all_fraction = 1.0
```

Weight-file stats for both longitude choices:

```text
map_weight_count = 33840
coverage_min = 4
coverage_max = 4
weight_sum_min = 0.9999998807907104
weight_sum_max = 1.0000001192092896
sami3_to_voltron_l_extrapolated = 164
Lb_cc_min = 0.0
Lb_cc_max = 553.7752075195312
```

The `--apply-voltron-closed-mask` test for `lon0` skipped no active
Voltron-to-RAIJU terms in the current tiny target region:

```text
skipped_voltron_to_raiju_terms_by_mask = 0
```

The 164 clamped TubeShell cells are therefore not participating in the current
RAIJU target cells, but they should still be handled explicitly for other grids.

## Comparison

`lon0` and `lonc` products are effectively identical for the current template:

```text
Pavg lon0-vs-lonc max_abs = 5.122274160385132e-09
Davg lon0-vs-lonc max_abs = 0.00018310546875
Pstd lon0-vs-lonc max_abs = 6.705522537231445e-08
Dstd lon0-vs-lonc max_abs = 0.001953125
tiote lon0-vs-lonc max_abs = 4.172325134277344e-07
```

Compared to the ShellGrid intermediate product, TubeShell `Lb+longitude`
changes the mapped scalar moments noticeably:

```text
Davg mean shell = 1985.475588861129
Davg mean lon0  = 1724.3497391370101
Davg max_abs shell-vs-lon0 = 2671.9531860351562

Pavg mean shell = 0.023705168903692984
Pavg mean lon0  = 0.020616471462820335
Pavg max_abs shell-vs-lon0 = 0.03142083017155528
```

This is expected: the mapping is now querying SAMI3 using traced TubeShell `Lb`
instead of the idealized ShellGrid `1/sin(theta)^2` coordinate.

## Interpretation

This is the first working TubeShell-coordinate SAMI3->Voltron->RAIJU weight
prototype.  It is a useful bridge toward a production geometry mapper because
the code path now accepts 2-D Voltron traced-tube query coordinates rather than
only separable 1-D shell-grid coordinates.

The remaining physics blocker is:

```text
replace the TubeShell Lb/longitude interpolation with a true bvol/flux-tube
volume weighted remap and a documented open/closed coverage policy
```
