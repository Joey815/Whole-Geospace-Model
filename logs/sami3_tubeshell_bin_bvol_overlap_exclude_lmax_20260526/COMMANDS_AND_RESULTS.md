# Commands And Results

Date: 2026-05-26 CST

## Weight Generation

```text
python scripts/sami3_moments/build_sami3_to_raiju_weights.py \
  analysis/sami3_moments_stubpayload_ds_over_B_20260524.h5 \
  --out analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5 \
  --mapping-mode voltron_tubeshell_l_mlt \
  --raicpl-template analysis/runtime_ingest_active_bvol_ledger_smoke2_20260525/sami3_moments_active_bvol_ledger_smoke2.raiCpl.Res.00000.h5 \
  --voltron-template analysis/runtime_ingest_active_bvol_ledger_smoke2_20260525/sami3_moments_active_bvol_ledger_smoke2.volt.Res.00000.h5 \
  --voltron-tube-longitude lon0 \
  --voltron-compose-weight-mode bin_bvol_overlap \
  --voltron-bvol-floor 0 \
  --voltron-overlap-max-l-span 0 \
  --voltron-overlap-max-lon-span 0 \
  --voltron-source-domain-policy exclude_above_target_lmax \
  --sami3-grid-dir data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000
```

Result:

```text
schema_version = 7
sparse_weight_count = 46969
coverage_count_max = 12
source_domain_skipped_above_lmax = 5852
source_domain_skipped_above_lmax_bvol_fraction = 0.999595965103914
```

## Geometry Audit

```text
python scripts/sami3_moments/analyze_sami3_raiju_flux_volume_geometry.py \
  --weight-file analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5 \
  --out analysis/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.h5 \
  --voltron-tube-longitude lon0 \
  --voltron-bvol-floor 0 \
  --voltron-overlap-max-l-span 0 \
  --voltron-overlap-max-lon-span 0
```

Result:

```text
stored_count = 39853
recomputed_count = 39853
missing_stored_terms = 0
extra_recomputed_terms = 0
weight_compare_max_abs_diff = 1.4889254773553517e-08
source_domain_excluded_above_lmax = 5852
```

## Target-Domain Classification

```text
python scripts/classify_sami3_raiju_target_domain.py \
  --audit-h5 analysis/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.h5 \
  --weights-h5 analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5 \
  --json-output analysis/sami3_raiju_target_domain_classification_exclude_lmax_20260526.json \
  --text-output analysis/sami3_raiju_target_domain_classification_exclude_lmax_20260526.txt
```

Result:

```text
positive_all active_bvol_sum = 2268464.0
positive_all above_target_Lmax_bvol_fraction = 0.9995959821271133
positive_all inside_target_Lrange_bvol_fraction = 0.000403795629822371
```

## Domain-Aware Closure Gate

```text
python scripts/validate_sami3_raiju_target_closure.py \
  --audit-json analysis/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_exclude_lmax_20260526.json \
  --bvol-source active \
  --require-active-ledger \
  --closure-denominator target-admissible-lrange \
  --domain-classification-json analysis/sami3_raiju_target_domain_classification_exclude_lmax_20260526.json \
  --json-output analysis/validate_sami3_raiju_target_closure_exclude_lmax_domainaware_20260526.json
```

Result:

```text
overall = ok
target_admissible_used_fraction = 1.0
target_admissible_outside_target_fraction = 0.0
target_admissible_bad_bvol_fraction = 0.0
```

## Stage-2 Product

```text
python scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  analysis/sami3_moments_stubpayload_ds_over_B_20260524.h5 \
  --out analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5 \
  --n-fluid-in 1 \
  --bulk-channel 0 \
  --density-mode num \
  --pressure-mode ion \
  --raicpl-template analysis/runtime_ingest_blend_20260524/sami3_moments_base_control.raiCpl.Res.00000.h5 \
  --mapping-mode weights \
  --mapping-weight-file analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5 \
  --runtime-mask-policy coverage_closed_no_extrap
```

Validation:

```text
python scripts/validate_sami3_raiju_mapping_product.py \
  --product-h5 analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5 \
  --expect-mapping-mode weights \
  --min-valid-fraction 0.95 \
  --min-finite-all-fraction 1.0 \
  --max-extrapolated-fraction 0.0 \
  --weight-sum-tol 1e-5 \
  --json-output analysis/validate_sami3_raiju_mapping_product_exclude_lmax_20260526.json
```

Result:

```text
overall = ok
runtime_valid_fraction = 0.9574468085106383
finite_all_fraction = 1.0
extrapolated_fraction = 0.0
weight_sum_valid_near_one max_dev = 1.1920928955078125e-07
```
