# SAMI3 -> RAIJU Voltron-Shell Weight File Prototype

Date: 2026-05-24

## Scope

This checkpoint adds a new explicit sparse mapping-weight generation mode:

```text
--mapping-mode voltron_shell_l_mlt
```

The new mode composes:

```text
SAMI3 L/MLT grid
-> Voltron TubeShell ShellGrid
-> RAIJU ShellGrid
```

It is closer to the MAGE runtime path than the direct `l_mlt_separable` file
because the artifact now carries a real Voltron TubeShell intermediate grid and
its `bVol/topo/Lb/bmin/nTrc` geometry.  It is still a prototype L/MLT mapping,
not a production traced-tube or `bvol`-weighted physical remap.

## Code

Updated files:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/build_sami3_to_raiju_weights.py
code/kaiju_sami3_moments/scripts/sami3_moments/run_sami3_mage_moments_smoke.sh
code/kaiju_sami3_moments/scripts/sami3_moments/README.md
```

`build_sami3_to_raiju_weights.py` now supports:

```text
--mapping-mode l_mlt_separable
--mapping-mode voltron_shell_l_mlt
--voltron-template /path/to/voltron.h5
--apply-voltron-closed-mask
```

## Schema

The Voltron-shell file writes:

```text
schema_version = 3
mapping_mode = voltron_shell_l_mlt
physical_validity = prototype
```

New HDF5 groups:

```text
/intermediate/L
/intermediate/MLT_deg
/intermediate/bvol_corner
/intermediate/bvol_cc
/intermediate/topo_corner
/intermediate/closed_cell_mask
/intermediate/Lb_corner
/intermediate/Lb_cc
/intermediate/bmin_corner
/intermediate/bmin_cc
/intermediate/nTrc_corner
/intermediate/nTrc_cc
/intermediate/sami3_to_voltron/*
/intermediate/voltron_to_raiju/*
```

The direct runtime mapping remains in:

```text
/map/dst_index
/map/src_index
/map/weight
/quality/coverage_count
/quality/weight_sum
/quality/closed_field_mask
```

## Voltron Geometry Confirmed

Template:

```text
analysis/runtime_ingest_blend_20260524/sami3_moments_base_control.volt.Res.00000.h5
```

Observed Voltron TubeShell geometry:

```text
ShellGrid/theta shape = (181,)
ShellGrid/phi   shape = (189,)
TubeShell/bVol  shape = (189, 181)
TubeShell/topo  unique = 1.0 open: 554, 2.0 closed: 33655
TubeShell bVol/Lb/bmin/nTrc are present
```

The generated intermediate grid is:

```text
/intermediate/L                         shape = (180,)
/intermediate/MLT_deg                   shape = (188,)
/intermediate/bvol_cc                   shape = (188, 180)
/intermediate/closed_cell_mask          shape = (188, 180)
/intermediate/sami3_to_voltron/dst_index shape = (128592, 2)
/intermediate/voltron_to_raiju/dst_index shape = (8836, 2)
```

Closed intermediate cells:

```text
33276 / 33840
```

## Generated Product

Archived evidence:

```text
logs/sami3_voltron_shell_weightfile_20260524/
```

Included small artifacts:

```text
sami3_to_raiju_weights_voltron_shell_l_mlt_20260524.h5
sami3_to_raiju_weights_voltron_shell_l_mlt_20260524.json
sami3_to_raiju_weights_voltron_shell_l_mlt_closedmask_20260524.json
sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_shell_l_mlt_20260524.json
sami3_voltron_shell_weightfile_20260524.log
```

The larger stage-2 diagnostic HDF5 was generated locally but not committed.

## Verification

Full smoke command:

```text
PYTHON_BIN=/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  bash scripts/sami3_moments/run_sami3_mage_moments_smoke.sh \
  > analysis/sami3_voltron_shell_weightfile_20260524.log 2>&1
```

Result:

```text
SAMI3 MAGE moments smoke passed
runtime_mapping=weights
runtime_mapping_quality finite_all_fraction=1.0
```

Generated schema-3 weight stats:

```text
sparse_weight_count = 33840
coverage_count_min = 4
coverage_count_max = 4
weight_sum_min = 0.9999998807907104
weight_sum_max = 1.0000001192092896
l_extrapolated_cell_count = 0
closed_field_cell_count = 8460
closed_field_fraction = 1.0
```

The `--apply-voltron-closed-mask` test did not skip any active
Voltron-to-RAIJU source terms for this smoke template:

```text
skipped_voltron_to_raiju_terms_by_mask = 0
```

This means the current RAIJU target region does not sample the open Voltron
TubeShell cells in this template; it should not be generalized to other grids.

## Comparison To Direct L/MLT

The Voltron-shell weight-file stage-2 product matches the existing inline
`l_mlt` product to floating-point roundoff:

```text
RaiCplMomentsOnly/Pavg  max_abs = 1.4901161193847656e-08  max_rel = 1.4901161193847656e-08
RaiCplMomentsOnly/Davg  max_abs = 0.001953125             max_rel = 1.1794265085779101e-07
RaiCplMomentsOnly/Pstd  max_abs = 2.9802322387695312e-08  max_rel = 2.9802322387695312e-08
RaiCplMomentsOnly/Dstd  max_abs = 0.00390625              max_rel = 1.189390305446135e-07
RaiCplMomentsOnly/tiote max_abs = 5.960464477539063e-08   max_rel = 5.960464477539063e-08
```

Overall:

```text
Voltron-shell weight-file comparison max_abs = 0.00390625
Voltron-shell weight-file comparison max_rel = 1.189390305446135e-07
```

## Interpretation

This step validates the file contract and intermediate geometry plumbing.  It
does not yet solve the physical mapping problem.  The next physical blocker is:

```text
replace the L/MLT shell-grid interpolation with true Voltron traced-tube or
bvol-consistent flux-tube weights
```

The useful outcome is that downstream stage-2 and Fortran runtime ingestion can
continue to consume the same `/map` contract while the weight-generation method
is replaced.
