# WACCM-X/SAMI3 Phi Payload Content QC

Date: 2026-05-25

## Scope

The append2 validator now checks more than the `remix_sami3_phi_payload.v1`
header and frame count.  For each phi payload frame it records:

```text
finite_count
min/max
nonzero count
frame hour
valid_until hour
consecutive frame max_abs/rms difference
```

Always-on checks now include:

```text
all phi values are finite
frame hours are nondecreasing
valid_until >= frame hour
```

Optional checks:

```text
--require-nonzero-phi
--require-changing-phi-frames
--min-phi-frame-max-abs-diff <value>
```

## Current Probe Result

The existing two-frame Voltron phi runtime validates with
`--require-nonzero-phi`:

```text
finite_counts = [12125, 12125]
hours = [0.0, 0.0010000000474974513]
valid_until = [0.0010000000474974513, 1.0000000150474662e+30]
nonzero_counts = [3492, 3492]
overall = ok
```

The stricter `--require-changing-phi-frames` probe fails:

```text
max_abs_diff = 0.0
min required = 1.0e-6
overall = FAIL
```

This is treated as a diagnostic finding, not a hard failure for the current
append2/direct-wait gates.  The present short-window Voltron payload is finite,
nonzero, and time-ordered, but the two POT frames are numerically identical.
A future dynamic-potential test should enable `--require-changing-phi-frames`.

## Archive Integration

The queued append2 and direct-wait archive commands should include:

```text
--require-nonzero-phi
```

Do not add `--require-changing-phi-frames` until a test case is chosen where
the REMIX/Voltron potential is expected to evolve between frames.

## Evidence

Archived under:

```text
logs/waccmx_phi_payload_content_validation_20260525/
```
