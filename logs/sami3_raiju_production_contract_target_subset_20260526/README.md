# SAMI3 -> RAIJU Production Contract With Target-Subset Gate

Date: 2026-05-26 CST

This archive reruns the production-contract validator for the current schema v7
`exclude_above_target_lmax` product with an additional target-admissible subset
input:

```text
target_admissible_json =
logs/sami3_raiju_target_admissible_subset_20260526/target_admissible_subset_lon0_active_20260526.json
```

The diagnostic contract passes and keeps the product classified as
`diagnostic_only`.  The production-readiness contract intentionally fails on
both source-domain loss and target-admissible representativeness:

```text
FAIL production_source_domain_skip_threshold: fraction=0.999595965103914 max=0.05
FAIL production_label: product=unknown weight=prototype
FAIL production_target_admissible_bvol_fraction: fraction=0.0004037956259340399 min=0.05
classification=diagnostic_only
overall=FAIL
```

The new target-subset gate makes the physical blocker explicit in the executable
contract: the current RAIJU target-domain subset is clean but too small to be
treated as representative production plasma feedback.
