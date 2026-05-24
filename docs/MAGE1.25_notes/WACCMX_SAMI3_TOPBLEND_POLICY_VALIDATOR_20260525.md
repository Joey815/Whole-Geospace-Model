# WACCM-X -> SAMI3 Top-Blend Policy Validator

Date: 2026-05-25

## Scope

This adds a log-driven validator for the receiver-side WACCM-X top transition
policy:

```text
scripts/validate_wxsami3_topblend_policy.py
```

It validates the diagnostics emitted by `waccmx_neutral_mod.f90` rather than
recomputing the full neutral arrays.  The purpose is to make top-blend policy,
source-flag accounting, He fallback, and W-off behavior part of the standard
post-run gate for WACCM-X -> SAMI3 online jobs.

## Checks

The validator can check:

```text
WACCMX neutral top blend policy line is present
mode is linear or none
linear bottom/top heights match expected values
WACCMX_APPLY_BLEND lines are present and parseable
linear mode is enabled on apply lines
nonzero blend cells occur when requested
source-flag unknown counts are zero
He native counts match valid payload counts
W zero counts match valid payload counts
```

For the current f19 top-blend prototype, the intended gate is:

```bash
python3 scripts/validate_wxsami3_topblend_policy.py \
  --run-dir logs/topblend_20260524 \
  --expect-top-blend-mode linear \
  --expect-bottom-km 600 \
  --expect-top-km 720 \
  --min-apply-blend-lines 1 \
  --min-total-blend-cells 1 \
  --require-zero-unknown-source-flags \
  --require-he-native \
  --require-w-zero
```

## Validation Result

The validator passes on the existing 2026-05-24 top-blend runtime evidence:

```text
topblend_policy = linear, bottom=600 km, top=720 km
apply_blend_lines = 424
blend_cell_total = 7354
blend_enabled_values = [1]
unknown_apply_total = 0
unknown_recv_total = 0
he_native_matches_valid = ok
w_zero_matches_valid = ok
overall = ok
```

## Archive Integration

`scripts/archive_wxsami3_append2_result.py` now optionally runs this validator
when passed:

```text
--expect-top-blend-mode linear
--expect-blend-bottom-km 600
--expect-blend-top-km 720
--min-total-blend-cells 1
--require-zero-unknown-source-flags
--require-he-native
--require-w-zero
```

This makes the queued append2/direct-wait jobs validate neutral packet
transport, same-call-site live replay, phi payload transfer, and the explicit
top-blend/source-policy guardrail in one archive workflow.

## Evidence

Archived under:

```text
logs/waccmx_topblend_policy_validation_20260525/
```
