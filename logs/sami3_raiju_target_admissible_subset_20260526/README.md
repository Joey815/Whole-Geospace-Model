# SAMI3 -> RAIJU Target-Admissible Source Subset Archive

Date: 2026-05-26 CST

This archive contains the target-admissible source-subset diagnostic for the
current schema v7 `exclude_above_target_lmax` SAMI3 -> RAIJU product.

Inputs:

```text
audit_h5 = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.h5
weights_h5 = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5
```

Archived outputs:

```text
target_admissible_subset_lon0_active_20260526.txt
target_admissible_subset_lon0_active_20260526.json
analyze_target_admissible_subset.stdout.txt
```

Key result:

```text
target_admissible_lrange bvol_fraction = 0.0004037956259340399
target_admissible_lrange count = 15040
target_admissible_lrange status = 100% used
above_target_lrange bvol_fraction = 0.9995959651040349
target_admissible_is_representative = False
```

Interpretation: the target-admissible subset is geometrically clean but too
small in active source bVol to claim representative production plasma feedback.
