# SAMI3 -> RAIJU Target-Domain Closure Gate

Date: 2026-05-25 CST

## Purpose

The active bVol ledger confirms that Voltron can write the compact
active-domain volume diagnostics:

```text
/TubeShell/bVolActive
/TubeShell/bVolActiveFrac
```

That does not by itself make the current `bin_bvol_overlap` mapping physically
acceptable.  The next question is whether enough valid Voltron flux-tube volume
actually enters the RAIJU target domain, and whether rejected volume is small
enough to treat the mapped moments as a physical coupling rather than a
diagnostic/runtime adapter.

This note defines that closure check as an explicit validator.

## Validator

Primary script:

```text
scripts/validate_sami3_raiju_target_closure.py
```

Input:

```text
--audit-json <sami3_raiju_flux_volume_geometry_audit*.json>
```

The validator reads the flux-volume geometry audit and checks:

```text
weight_compare stored/recomputed counts match
weight_compare has no missing/extra sparse terms
weight_compare max_abs_diff is within tolerance
target_positive_fraction is above threshold
source bVol status fractions are present and sum to unity
used bVol fraction is above threshold
large_footprint bVol fraction is below threshold
outside_target bVol fraction is below threshold
bad_bvol/bad_geometry/no_terms fractions are below threshold
optional active-domain ledger exists and is finite
```

The validator now supports two closure denominators:

```text
--closure-denominator all-source
--closure-denominator target-admissible-lrange
```

`all-source` is the original production-style check: the denominator is all
valid source bVol in the audit.  `target-admissible-lrange` uses a companion
domain classifier and computes the closure fractions only over source cells
whose `Lb_cc` lies inside the current RAIJU target `L_edge` range.  This does
not make outside-domain volume physically coupled; it separates target-domain
mapping correctness from source/target domain mismatch.

Companion classifier:

```text
scripts/classify_sami3_raiju_target_domain.py
```

Classifier inputs:

```text
--audit-h5 <sami3_raiju_flux_volume_geometry_audit*.h5>
--weights-h5 <sami3_to_raiju_weights*.h5>
```

The default bVol source is `prefer-active`; for the current active-ledger audit
we use:

```text
--bvol-source active
--require-active-ledger
```

## Current Result

Archived output:

```text
logs/sami3_raiju_target_closure_gate_20260525/
  validate_sami3_raiju_target_closure_activeledger_20260525.txt
  validate_sami3_raiju_target_closure_activeledger_20260525.json
```

Command:

```text
scripts/validate_sami3_raiju_target_closure.py \
  --audit-json logs/sami3_active_bvol_ledger_runtime_smoke_20260525/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_activeledger_20260525.json \
  --bvol-source active \
  --require-active-ledger \
  --json-output logs/sami3_raiju_target_closure_gate_20260525/validate_sami3_raiju_target_closure_activeledger_20260525.json
```

The result is intentionally:

```text
overall = FAIL
```

Passing checks:

```text
weight_count_match = 39853 vs 39853
weight_no_missing_terms = 0
weight_no_extra_terms = 0
weight_max_abs_diff = 1.4889254773553517e-08 <= 1e-06
target_positive_fraction = 0.9574468085106383 >= 0.9
status_fraction_sum = 1.0
bad_bvol_fraction = 0
bad_geometry_fraction = 0
no_terms_fraction = 0
active_valid_bvol_sum = 2268463.9952379456
active_frac_all_finite = 33676/33676
active_frac_min = 0.25
```

Failing physical-closure checks:

```text
used_fraction = 0.00040379562605685195 < 0.5
large_footprint_fraction = 0.9384275226700948 > 0.05
outside_target_fraction = 0.061168681703848454 > 0.05
```

## Interpretation

This is a useful failure.  It says:

```text
The current bVol-overlap mapper is reproducible.
The active-domain bVol ledger is written and finite.
The current mapped target domain captures far too little valid source bVol.
Most valid source bVol is rejected by the broad-footprint gate.
```

Therefore the current SAMI3 -> RAIJU path remains a conservative
density-only diagnostic/runtime adapter.  It should not be labeled production
physics coupling.

## No-Span Diagnostic

To test whether the failure is just caused by the conservative footprint-span
gate, a second offline diagnostic disabled both span limits:

```text
--voltron-overlap-max-l-span 0
--voltron-overlap-max-lon-span 0
```

Archived output:

```text
logs/sami3_raiju_target_closure_nospan_20260525/
```

Weight/audit summary:

```text
sparse_weight_count = 238146
overlap_split_term_count = 225658
overlap_max_terms_per_source_cell = 4050
coverage_count_max = 52
source_status_counts = used 15440, bad_bvol 164, large_footprint 0,
                       outside_target 18236
source_mapped_bvol_fraction_of_valid = 0.008957983012102013
```

Target-closure validator result:

```text
overall = FAIL
used_fraction = 0.112192593703183 < 0.5
large_footprint_fraction = 0.0 <= 0.05
outside_target_fraction = 0.8878074062968169 > 0.05
weight_max_abs_diff = 2.9787811772763462e-08 <= 1e-06
```

This rules out a simple threshold relaxation as the fix.  Disabling the
large-footprint gate increases sparse terms by about 5x and creates source
cells with thousands of overlap terms, but it still does not close the target
domain in active bVol.

## Domain-Aware Diagnostic

After the traced-line debug export identified the largest outside-target cell
as a very high-L source tube, the no-span product was rerun through the
domain-aware closure gate.

Archived output:

```text
logs/sami3_raiju_target_closure_domainaware_20260526/
  validate_sami3_raiju_target_closure_activeledger_nospan_domainaware_20260526.txt
  validate_sami3_raiju_target_closure_activeledger_nospan_domainaware_20260526.json
  validate_sami3_raiju_target_closure_activeledger_nospan_domainaware_strict_source_domain_20260526.txt
  validate_sami3_raiju_target_closure_activeledger_nospan_domainaware_strict_source_domain_20260526.json
```

Domain-aware command:

```text
scripts/validate_sami3_raiju_target_closure.py \
  --audit-json logs/sami3_raiju_target_closure_nospan_20260525/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_activeledger_nospan_20260525.json \
  --bvol-source active \
  --require-active-ledger \
  --closure-denominator target-admissible-lrange \
  --domain-classification-json logs/sami3_trace_debug_target_i005_j095_20260525/trace_debug_outside_target_lrange_classification_20260525.json \
  --json-output logs/sami3_raiju_target_closure_domainaware_20260526/validate_sami3_raiju_target_closure_activeledger_nospan_domainaware_20260526.json
```

Result:

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

Strict source-domain policy command adds:

```text
--max-source-above-target-lmax-fraction 0.05
```

Strict result:

```text
overall = FAIL
source_above_target_Lmax_fraction = 0.9995959821271133 > 0.05
```

Interpretation:

```text
Within the current RAIJU target L range, the no-span sparse geometry closes.
The production blocker is source/target domain mismatch: almost all positive
active source bVol is above the target outer L edge.  This must be handled as a
physical domain-policy decision, not as an overlap-threshold tuning problem.
```

## Next Gate

The next implementation step should not tune scalar moment blending.  It should
make the source-domain policy explicit:

```text
1. Choose and implement the policy for source bVol above the RAIJU target Lmax:
   exclude from target-domain coupling, diagnostic clamp/project only, or extend
   the target domain.
2. Build the sparse SAMI3 -> Voltron -> RAIJU product with that policy recorded
   in metadata.
3. Require both checks before claiming production physics:
   target-admissible closure passes;
   strict source-domain policy is physically justified or passes its threshold.
```
