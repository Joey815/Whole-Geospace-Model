# WACCM-X/SAMI3 Fallback Count Validation

Date: 2026-05-25

## Scope

This tightens the live neutral packet contract around fallback accounting for
the current f19 online WACCM-X -> SAMI3 prototype.

The validator now checks that:

```text
runtime_qc.above_live_top == source_flags.SAMI3_NATIVE_ABOVE_TOP
runtime_qc.n2_residual_negative == source_flags.SAMI3_NATIVE_N2_INVALID
source_flags.SAMI3_NATIVE_OTHER_INVALID == 0 when requested
replay initial and final counts match for samples, invalid, above_live_top,
  n2_residual_used, and n2_residual_negative
N2 residual was actually used when residual mode is expected
N2 residual min/max are finite and ordered
```

The archive helper forwards `--require-zero-unknown-source-flags` into this
live contract validator, so the same source-flag policy is checked in both the
top-blend/source-flag gate and the live packet contract gate.

## Validation Result

Existing WACCM-X live neutral plus two-frame phi smoke:

```text
run = logs/waccmx_live_neutral_voltron_phi_2frame_20260525
above_live_top = 1641376
SAMI3_NATIVE_ABOVE_TOP = 1641376
n2_residual_negative = 178219
SAMI3_NATIVE_N2_INVALID = 178219
SAMI3_NATIVE_OTHER_INVALID = 0
n2_residual_used = 4389984
n2_residual_min = -0.053314608006139914
n2_residual_max = 0.8129786925378699
overall = ok
```

This does not make residual-derived N2 a final physics choice.  It verifies
that the current prototype records the fallback decision consistently instead
of silently clipping or losing invalid-cell accounting.

## Evidence

Archived under:

```text
logs/waccmx_live_neutral_fallback_validation_20260525/
```

including:

```text
waccmx_static_2frame_fallback_contract.txt
waccmx_static_2frame_fallback_contract.json
```
