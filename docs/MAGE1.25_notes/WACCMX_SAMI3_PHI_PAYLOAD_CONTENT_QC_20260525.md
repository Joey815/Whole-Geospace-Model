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
--expected-first-phi-hour <hour>
--require-nonzero-phi
--require-receiver-phi-values
--require-changing-phi-frames
--min-phi-frame-max-abs-diff <value>
--sender-kind waccmx|neutral_phi_stub
```

## Current Probe Result

The existing full WACCM-X two-frame runtime validates with
`--require-nonzero-phi --require-receiver-phi-values`:

```text
finite_counts = [12125, 12125]
hours = [0.0, 0.0010000000474974513]
valid_until = [0.0010000000474974513, 1.0000000150474662e+30]
nonzero_counts = [3492, 3492]
receiver_phi_values_match_payload = matched 2 of 2
overall = ok
```

That older short-window payload still fails the stricter
`--require-changing-phi-frames` probe:

```text
max_abs_diff = 0.0
min required = 1.0e-6
overall = FAIL
```

The newer append-capable Voltron writer and standalone SAMI3 receiver test
close that gap:

```text
hours = [0.0, 0.0013888889225199819]
valid_until = [0.0013888889225199819, 1.0000000150474662e+30]
nonzero_counts = [3492, 3492]
phi_payload_frame_change = max_abs_diff 3.5858945846557617
receiver_phi_values_match_payload = matched 2 of 2
sender_kind = neutral_phi_stub
overall = ok
```

Therefore the queued append2/direct-wait full integration archives should now
gate on changing Voltron/REMIX phi frames, not only nonzero frames.

## Archive Integration

The queued append2 and direct-wait archive commands should include:

```text
--require-nonzero-phi
--require-receiver-phi-values
--require-changing-phi-frames
```

## Evidence

Archived under:

```text
logs/waccmx_phi_payload_content_validation_20260525/
```
