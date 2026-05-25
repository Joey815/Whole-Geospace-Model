# SAMI3 -> RAIJU Source-Domain Policy Product

Date: 2026-05-26 CST

## Purpose

The target-domain closure work showed that the no-span Voltron TubeShell
overlap geometry closes inside the current RAIJU target L range, but almost all
positive active source bVol lies above the RAIJU target outer L edge:

```text
target_L_edge_max = 33.16343747752636
source_above_target_Lmax_fraction = 0.9995959821271133
```

This checkpoint makes that source-domain decision explicit in the sparse
stage-2 product instead of hiding it inside an overlap threshold.

## Code Change

Updated:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/build_sami3_to_raiju_weights.py
code/kaiju_sami3_moments/scripts/sami3_moments/analyze_sami3_raiju_flux_volume_geometry.py
```

New builder option:

```text
--voltron-source-domain-policy none
--voltron-source-domain-policy exclude_above_target_lmax
--voltron-source-domain-policy exclude_outside_target_lrange
```

For the current conservative product we use:

```text
--voltron-compose-weight-mode bin_bvol_overlap
--voltron-overlap-max-l-span 0
--voltron-overlap-max-lon-span 0
--voltron-source-domain-policy exclude_above_target_lmax
```

The generated HDF5 weight file uses schema version 7 and writes:

```text
/intermediate/voltron_to_raiju/source_domain_excluded_mask
```

Mask values:

```text
0 = included
1 = source Lb_cc above target Lmax
2 = source Lb_cc below target Lmin
```

The audit tool now reads this optional mask and treats excluded source cells as
explicit outside-target source-domain volume during recomputation.

## Archived Artifacts

Archive:

```text
logs/sami3_tubeshell_bin_bvol_overlap_exclude_lmax_20260526/
```

Included artifacts:

```text
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.json
sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.h5
sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.json
sami3_raiju_target_domain_classification_exclude_lmax_20260526.json
sami3_raiju_target_domain_classification_exclude_lmax_20260526.txt
validate_sami3_raiju_target_closure_exclude_lmax_domainaware_20260526.json
validate_sami3_raiju_target_closure_exclude_lmax_domainaware_20260526.txt
sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5
sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.json
validate_sami3_raiju_mapping_product_exclude_lmax_20260526.json
validate_sami3_raiju_mapping_product_exclude_lmax_20260526.txt
```

## Weight Product Result

Generated weight product:

```text
schema_version = 7
voltron_source_domain_policy = exclude_above_target_lmax
sparse_weight_count = 46969
coverage_count_max = 12
overlap_split_term_count = 39853
overlap_max_terms_per_source_cell = 39
target_l_max = 33.16343747752636
```

Source-domain accounting:

```text
source_domain_positive_bvol_sum = 2268463.99523794
source_domain_skipped_above_lmax = 5852
source_domain_skipped_above_lmax_bvol = 2267547.4566233493
source_domain_skipped_above_lmax_bvol_fraction = 0.999595965103914
source_domain_skipped_below_lmin = 0
source_domain_skipped_below_lmin_bvol_fraction = 0.0
```

The builder fraction above uses the stored `bvol_cc` ledger.  The domain
classifier reports the same conclusion from active bVol:

```text
positive_all active_bvol_sum = 2268464.0
positive_all above_target_Lmax_bvol_fraction = 0.9995959821271133
positive_all inside_target_Lrange_bvol_fraction = 0.000403795629822371
```

## Geometry Audit Result

Independent recomputation against the stored sparse terms:

```text
target_positive_fraction = 0.9574468085106383
source_mapped_bvol_fraction_of_valid = 0.00034417894730482345
stored_count = 39853
recomputed_count = 39853
missing_stored_terms = 0
extra_recomputed_terms = 0
weight_compare_max_abs_diff = 1.4889254773553517e-08
```

Source status:

```text
used = 15040
bad_bvol = 164
large_footprint = 0
outside_target = 18636
source_domain_excluded_above_lmax = 5852
source_domain_excluded_below_lmin = 0
```

## Closure Gate Result

The domain-aware target-admissible closure gate passes:

```text
overall = ok
target_admissible_bvol_positive = 915.995849609375
target_admissible_fraction_sum = 1.0
target_admissible_used_fraction = 1.0
target_admissible_large_footprint_fraction = 0.0
target_admissible_outside_target_fraction = 0.0
target_admissible_bad_bvol_fraction = 0.0
target_admissible_bad_geometry_fraction = 0.0
target_admissible_no_terms_fraction = 0.0
```

This confirms that the target-domain sparse geometry closes for the small
source bVol subset that is admissible under the current RAIJU target L range.

## Stage-2 Mapping Product Result

Generated moment product:

```text
sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5
```

Moment product validator:

```text
overall = ok
runtime_valid_fraction = 0.9574468085106383
finite_all_fraction = 1.0
extrapolated_fraction = 0.0
coverage_valid_positive valid_min = 4
weight_sum_valid_near_one max_dev = 1.1920928955078125e-07
tiote masked range = 0.8749623894691467 / 1.0004475116729736
```

Mapped moments are finite across the runtime arrays:

```text
Pavg max = 0.24306359917085124
Davg max = 17404.894700846824
Pstd max = 0.7095791842325547
Dstd max = 38530.7995528546
tiote max = 1.0004475090321325
```

## Interpretation

This is a conservative, auditable target-domain policy product:

```text
It does not force high-L Voltron source volume into the current RAIJU target
grid.
It records how much source bVol was excluded before overlap construction.
It validates the target-admissible subset with an explicit closure gate.
It validates the resulting stage-2 /RaiCplMomentsOnly product.
```

It is still not production physics coupling.  The physically important fact is
that the current RAIJU target grid excludes almost all positive active source
bVol.  The next physics decision is whether to extend the RAIJU target domain,
derive a different Voltron source subset for inner-magnetosphere coupling, or
keep this as a diagnostic/runtime adapter.
