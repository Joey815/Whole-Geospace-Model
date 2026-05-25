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

New script:

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

## Next Gate

The next implementation step should not tune scalar moment blending.  It should
reduce the closure failure by improving the geometry path:

```text
1. Export or reconstruct enough traced-tube geometry to split large-footprint
   source cells into acceptable target-domain quadrature terms.
2. Preserve the current validator as the acceptance gate.
3. Require the production candidate to pass target-domain closure before
   enabling pressure/std/tiote physical interpretation.
```
