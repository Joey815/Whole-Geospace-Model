# SAMI3 -> RAIJU Target-Admissible Source Subset Diagnostic

Date: 2026-05-26 CST

## Purpose

The production-contract guardrail confirms that the current schema v7
`exclude_above_target_lmax` product is diagnostic-only.  This checkpoint asks a
more specific physics question:

```text
Is the small source subset inside the current RAIJU target L range large enough
to be representative of the Voltron active source volume?
```

## Script

New repeatable analyzer:

```text
scripts/analyze_sami3_raiju_target_admissible_subset.py
```

Inputs:

```text
audit_h5 = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.h5
weights_h5 = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5
source L = /source/Lb_cc
source longitude = /source/lon0_cc_deg
source bVol = /source/bvol_active_cc
target L edge = /dst/L_edge
```

Outputs:

```text
logs/sami3_raiju_target_admissible_subset_20260526/target_admissible_subset_lon0_active_20260526.txt
logs/sami3_raiju_target_admissible_subset_20260526/target_admissible_subset_lon0_active_20260526.json
```

## Result

Current target L range:

```text
target_L_edge_min = 1.4902905965657023
target_L_edge_max = 33.163437477526358
positive_source_cell_count = 33676
positive_source_bvol_sum = 2268463.9951948188
```

The target-admissible source subset is geometrically clean:

```text
target_admissible_lrange count = 15040
target_admissible_lrange bvol_sum = 915.9958388485247
target_admissible_lrange fraction_of_total_positive_bvol = 0.0004037956259340399
target_admissible_lrange Lb_min/max = 1.500771403312683 / 32.98798370361328
target_admissible_lrange Lb_weighted_mean = 26.56060885963173
target_admissible_lrange status = 100% used
term_count_min/max = 1 / 39
mapped_fraction_min/max = 0.5417668223381042 / 1.0
```

But it is not representative of active source bVol:

```text
above_target_lrange count = 5852
above_target_lrange bvol_sum = 2267547.4565805197
above_target_lrange fraction_of_total_positive_bvol = 0.9995959651040349
above_target_lrange Lb_min/max = 35.38717269897461 / 553.7752075195312
above_target_lrange Lb_weighted_mean = 354.24188507800744
```

The below-target source cells are numerous but physically negligible by active
bVol:

```text
below_target_lrange count = 12784
below_target_lrange bvol_sum = 0.5427754499905859
below_target_lrange fraction_of_total_positive_bvol = 2.3927003079631055e-07
```

## MLT Structure

The target-admissible subset is not obviously a single MLT-sector artifact.
Its 24-bin longitude histogram is broadly distributed, with per-bin bVol
fractions mostly between about `0.037` and `0.064`.

Top target-admissible source cells by active bVol all sit near the high-L edge
of the current target domain:

```text
source_i=164 source_j=185 bvol_active=0.822522044 Lb_cc=32.9879837 lon_deg=1 status=used
source_i=164 source_j=5   bvol_active=0.822522044 Lb_cc=32.9879837 lon_deg=1 status=used
source_i=164 source_j=4   bvol_active=0.822520137 Lb_cc=32.9879837 lon_deg=359 status=used
source_i=164 source_j=184 bvol_active=0.822520137 Lb_cc=32.9879837 lon_deg=359 status=used
```

## Interpretation

This confirms the source-domain problem in a more operational form:

```text
The current exclude-Lmax product is not failing because the admissible subset is
geometrically bad.

It is failing as production physics because the admissible subset contains only
0.0404% of the positive active source bVol.
```

Therefore the current product should remain a diagnostic/runtime adapter.  The
next production-facing decision cannot be solved by another runtime smoke test;
it requires a physical source-domain policy:

```text
1. define a different Voltron source subset that is intended to couple to the
   current RAIJU inner-domain grid, or
2. introduce a different target domain/model for the high-L source bVol, or
3. keep this path diagnostic-only and use it for controlled alpha/blending
   sensitivity tests.
```
