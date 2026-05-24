# WACCM-X/SAMI3 Time-Axis Validator

Date: 2026-05-25

## Scope

This adds a log and payload validator for the online WACCM-X/CAM -> SAMI3
neutral packet time axis and the REMIX/Voltron -> SAMI3 phi-frame time axis:

```text
scripts/validate_wxsami3_time_axis.py
```

The gate is intentionally separate from value replay QC.  It checks whether the
coupling timeline is internally consistent.

## Checks

The validator currently checks:

```text
sender neutral packet count
receiver neutral packet count
receiver worker records agree on packet hour
receiver worker coverage when expected worker count is supplied
sender and receiver neutral packet hours match
optional neutral packet cadence
phi payload frame count
phi payload frame hours are strictly increasing
phi valid_until links to the next frame hour
neutral packet hours are covered by a phi frame validity interval
SAMI3 receiver phi-frame records are present
SAMI3 receiver phi hrut is inside each frame validity interval
```

The append2 archive helper now runs this validator as part of the full evidence
gate.  It accepts optional `--expected-sami3-workers` and
`--expected-neutral-cadence-hours` inputs for longer multi-packet tests.

## Validation Result

Existing WACCM-X live neutral plus static two-frame phi smoke:

```text
run = logs/waccmx_live_neutral_voltron_phi_2frame_20260525
expected_neutral_packets = 1
expected_phi_frames = 2
expected_sami3_workers = 32
sender_hours = [0.0]
receiver_hours = [0.0]
receiver_unique_tasks = [32]
phi_hours = [0.0, 0.0010000000474974513]
phi_valid_until = [0.0010000000474974513, 1.0000000150474662e+30]
uncovered_neutral_hours = []
receiver_phi_records = 2
overall = ok
```

This is a time-axis consistency gate, not a claim that the static phi payload is
time-varying.  Time-varying phi content is covered by the independent phi
payload contract gate using the offset two-frame payload.

## Evidence

Archived under:

```text
logs/wxsami3_time_axis_validation_20260525/
```

including text and JSON outputs for:

```text
waccmx_static_2frame_time_axis
offset_payload_time_axis
```
