# SAMI3 -> RAIJU Flux-Volume Geometry Audit

Date: 2026-05-25 CST

## Purpose

This gate makes the current `bin_bvol_overlap` TubeShell mapping reproducible
from the mapping artifact itself.

The previous bVol-overlap weight file contained the runtime sparse weights, but
did not store enough edge/corner geometry to independently recompute the raw
Voltron TubeShell bVol overlap.  This made it hard to audit whether the sparse
weights were a faithful representation of the approximate footprint-overlap
algorithm.

## Code Changes

The mapping writer now stores reproducibility-critical geometry as float64:

```text
/intermediate/lon0_corner_rad
/intermediate/lonc_corner_rad
/intermediate/lat0_corner_rad
/intermediate/latc_corner_rad
/intermediate/Lb_corner
/intermediate/bvol_cc
/dst/L_edge
/dst/MLT_edge_deg_unwrapped
/dst/MLT_edge_deg
```

For `bin_bvol_overlap`, the mapping schema is now:

```text
schema_version = 6
```

The runtime sparse map is unchanged relative to the previous bVol-overlap gate:

```text
map/dst_index = identical
map/src_index = identical
map/weight max_abs_diff = 0
quality/coverage_count = identical
quality/weight_sum max_abs_diff = 0
intermediate/voltron_to_raiju/dst_index = identical
intermediate/voltron_to_raiju/src_index = identical
intermediate/voltron_to_raiju/weight max_abs_diff = 0
```

A new independent audit script was added:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/analyze_sami3_raiju_flux_volume_geometry.py
```

It reads the mapping file geometry, recomputes the raw Voltron TubeShell bVol
overlap against the RAIJU target bins, renormalizes by target cell, and compares
the result with the stored `/intermediate/voltron_to_raiju` sparse weights.

## Artifacts

Archive:

```text
logs/sami3_flux_volume_geometry_audit_20260525/
```

Files:

```text
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_geomdiag_20260525.h5
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_geomdiag_20260525.json
sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_20260525.h5
sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_20260525.json
```

## Audit Result

Independent recomputation matches the stored sparse map:

```text
stored_count = 39853
recomputed_count = 39853
missing_stored_terms = 0
extra_recomputed_terms = 0
max_abs_diff = 1.4889254773553517e-08
mean_abs_diff = 2.8356879694924742e-09
```

The nonzero target coverage remains:

```text
target_positive_count = 8100
target_zero_count = 360
target_positive_fraction = 0.9574468085106383
```

Source-cell status counts:

```text
used = 15040
bad_bvol = 164
bad_geometry = 0
large_footprint = 1392
outside_target = 17244
no_terms = 0
```

Mapped source bVol fraction:

```text
source_valid_bvol_sum = 2268463.9952379456
source_mapped_bvol_sum = 780.7575498798901
source_mapped_bvol_fraction_of_valid = 0.00034417894730482345
```

The accepted source cells are geometrically well behaved under the current
approximate overlap gate:

```text
mapped_fraction min/median/mean/max = 0.5417668362199105 / 1.0 / 0.9837498883031306 / 1.0000000000000004
used L-span max = 4.1430025303357425 Re
used longitude-span max = 2.0000000000001137 deg
max terms per source cell = 39
target normalized sum min/max = 0.9999999999999993 / 1.0000000000000007
```

The audit now also writes a source-status bVol ledger:

```text
used count/bVol/fraction = 15040 / 915.9958391445339 / 0.00040379562605685195
bad_bvol count/bVol/fraction = 164 / 0.0 / 0.0
bad_geometry count/bVol/fraction = 0 / 0.0 / 0.0
large_footprint count/bVol/fraction = 1392 / 2128789.047317451 / 0.9384275226700948
outside_target count/bVol/fraction = 17244 / 138758.95208135032 / 0.06116868170384847
no_terms count/bVol/fraction = 0 / 0.0 / 0.0
```

Target-domain proxy closure:

```text
raw_bvol_sum_total = 780.7575498798902
target_bvol_sum_positive = 8393.502757935126
raw_sum_over_positive_target_bvol_sum = 0.09301927602773116
```

This closure ratio is only a proxy because the Voltron and RAIJU bVol arrays
may use different native normalizations.

The raw Voltron-to-RAIJU bVol ratio remains broad:

```text
raw_to_target_bvol_ratio min/median/mean/max =
0.01639128323644509 / 0.11244339677746451 / 0.8533872887822489 / 3.78549415244694
```

## Interpretation

The current `bin_bvol_overlap` mapping is now auditable and reproducible.  The
schema v6 artifact contains enough target-bin and TubeShell corner geometry for
a standalone script to reconstruct the same sparse map.

This does not make the mapping production physics.  The audit shows that only a
small fraction of total valid Voltron TubeShell bVol lies inside the current
RAIJU target domain after footprint-QC rejection.  Most valid source bVol is
carried by broad-footprint cells that are intentionally rejected by the current
QC gate; the next largest contribution is outside the current target bins.

Therefore the next physics-mapping task is not to tune the existing overlap
weights.  The next task is to define target-domain flux-volume closure and then
replace this approximate corner-footprint overlap with a true traced-tube
flux-volume quadrature that has an explicit source/target volume accounting
contract.
