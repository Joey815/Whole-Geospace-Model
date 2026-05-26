# SAMI3 -> RAIJU Source L-Coverage Diagnostic

Date: 2026-05-26 CST

## Purpose

The target-admissible subset diagnostic showed that the source cells inside the
current RAIJU target L range are geometrically clean but carry only 0.0404% of
positive active source bVol.  This checkpoint asks the next operational
question:

```text
How far in L would the source/target-domain policy need to extend to capture
meaningful fractions of the Voltron active source bVol?
```

## Script

New repeatable analyzer:

```text
scripts/analyze_sami3_raiju_source_l_coverage.py
```

Inputs:

```text
audit_h5 = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.h5
weights_h5 = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5
source L = /source/Lb_cc
source bVol = /source/bvol_active_cc
target L edge = /dst/L_edge
```

Outputs:

```text
logs/sami3_raiju_source_l_coverage_20260526/source_l_coverage_lon0_active_20260526.txt
logs/sami3_raiju_source_l_coverage_20260526/source_l_coverage_lon0_active_20260526.json
```

## Result

Current source and target facts:

```text
target_L_edge_min = 1.4902905965657023
target_L_edge_max = 33.163437477526358
positive_source_cell_count = 33676
positive_source_bvol_sum = 2268463.9951948188
positive_source_L_min = 1.0192675590515137
positive_source_L_max = 553.7752075195312
```

Current RAIJU target-domain coverage:

```text
within_target_L count = 15040
within_target_L bvol_sum = 915.9958388485247
within_target_L fraction_of_positive_bvol = 0.0004037956259340399

above_target_L count = 5852
above_target_L bvol_sum = 2267547.4565805197
above_target_L fraction_of_positive_bvol = 0.9995959651040349
```

Active-bVol weighted L quantiles:

```text
0.001 = 42.96409606933594
0.01  = 83.38025665283203
0.05  = 145.15077209472656
0.10  = 180.75912475585938
0.50  = 317.8695983886719
0.90  = 530.341796875
0.95  = 545.7605590820312
0.99  = 553.7748413085938
```

Cumulative active-bVol coverage by L threshold:

```text
L <= 33.163437477526358 : 0.0004040348959648362
L <= 50                 : 0.0017470308214748557
L <= 75                 : 0.006154285547005926
L <= 100                : 0.017065090174806206
L <= 150                : 0.052912857749114334
L <= 200                : 0.1087823661997311
L <= 300                : 0.30961166546734464
L <= 350                : 0.5230229531453087
L <= 450                : 0.7964747634872962
L <= 550                : 0.9532487500051143
```

Production-assessment gate for a minimal 5% active-bVol coverage target:

```text
min_target_bvol_fraction = 0.05
current_target_bvol_fraction = 0.0004037956259340399
current_target_meets_min_fraction = false
L_required_for_min_fraction = 145.15077209472656
```

## Interpretation

This strengthens the diagnostic-only conclusion.  The present target domain
does not merely miss a modest outer shell; it misses essentially all positive
active source bVol.  A minimal 5% bVol threshold would require L around 145,
the active-bVol median is around L=318, and 90% coverage is around L=530.

That means the current `exclude_above_target_lmax` product should not be
promoted by tuning alpha values or by running another runtime smoke.  One of
these physical decisions is required first:

```text
1. redefine the Voltron source subset intended for the current inner RAIJU
   target grid,
2. introduce a different target/domain treatment for the high-L source bVol,
   or
3. keep this adapter diagnostic-only and use it only for controlled
   sensitivity experiments.
```
