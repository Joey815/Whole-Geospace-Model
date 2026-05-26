# SAMI3 -> RAIJU Source L-Coverage Archive

Date: 2026-05-26 CST

This archive contains the active-bVol source L-coverage diagnostic for the
current schema v7 `exclude_above_target_lmax` SAMI3 -> RAIJU product.

Inputs:

```text
audit_h5 = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.h5
weights_h5 = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5
```

Archived outputs:

```text
source_l_coverage_lon0_active_20260526.txt
source_l_coverage_lon0_active_20260526.json
analyze_source_l_coverage.stdout.txt
```

Key result:

```text
current target L range = 1.4902905965657023 .. 33.163437477526358
within_target_L bVol fraction = 0.0004037956259340399
above_target_L bVol fraction = 0.9995959651040349
L_required_for_5_percent_active_bVol = 145.15077209472656
weighted_L_median = 317.8695983886719
weighted_L_90_percent = 530.341796875
```

Interpretation: the current RAIJU target L domain captures only 0.0404% of
positive active source bVol.  A minimal 5% active-bVol coverage threshold would
already require extending the target/source-domain policy to about L=145, so
the current path remains diagnostic-only unless the source-domain physics is
redefined.
