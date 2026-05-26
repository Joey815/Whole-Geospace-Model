# SAMI3 -> RAIJU Production Contract Target-Subset Gate

Date: 2026-05-26 CST

## Purpose

The previous production-contract guardrail made the high-L source-domain loss
executable.  The target-admissible subset diagnostic then showed that the clean
source cells inside the current RAIJU target L range carry only a tiny fraction
of positive active Voltron bVol.

This checkpoint connects that diagnostic directly to the production-readiness
contract.

## Code Change

Updated validator:

```text
scripts/validate_sami3_raiju_production_contract.py
```

New options:

```text
--target-admissible-json <target_admissible_subset.json>
--require-target-admissible-json
--min-production-target-admissible-bvol-fraction 0.05
```

The optional JSON input is the output from:

```text
scripts/analyze_sami3_raiju_target_admissible_subset.py
```

When supplied, the validator records:

```text
target_admissible_bvol_fraction
target_admissible_is_representative
target_L_edge_min / target_L_edge_max
positive_source_bvol_sum
```

In `production-readiness` mode it now requires:

```text
target_admissible_bvol_fraction >= min_production_target_admissible_bvol_fraction
```

The default threshold is intentionally conservative and matches the previous
source-domain skip threshold:

```text
min_production_target_admissible_bvol_fraction = 0.05
```

## Validation

Archive:

```text
logs/sami3_raiju_production_contract_target_subset_20260526/
```

Input product:

```text
/online1/jiaoy_group/jiaoy/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvol_overlap_exclude_lmax_20260526.h5
```

Target-subset input:

```text
logs/sami3_raiju_target_admissible_subset_20260526/target_admissible_subset_lon0_active_20260526.json
```

Diagnostic-contract mode passes:

```text
target_admissible_bvol_fraction = 0.0004037956259340399
low_target_admissible_fraction_is_not_labeled_production = ok
classification = diagnostic_only
overall = ok
```

Production-readiness mode intentionally fails:

```text
FAIL production_source_domain_skip_threshold: fraction=0.999595965103914 max=0.05
FAIL production_label: product=unknown weight=prototype
FAIL production_target_admissible_bvol_fraction: fraction=0.0004037956259340399 min=0.05
classification = diagnostic_only
overall = FAIL
```

## Interpretation

This does not change the runtime product.  It changes the promotion rule.

The current schema v7 product remains a validated diagnostic/runtime adapter:

```text
runtime_valid_fraction = 0.9574468085106383
target_admissible_lrange status = 100% used
target_admissible_bvol_fraction = 0.0004037956259340399
```

It cannot pass production-readiness unless either:

```text
1. the source-domain policy is changed so that the target-admissible source bVol
   becomes representative, or
2. a different target domain/model is introduced for the high-L source volume,
   or
3. the product remains explicitly diagnostic-only.
```
