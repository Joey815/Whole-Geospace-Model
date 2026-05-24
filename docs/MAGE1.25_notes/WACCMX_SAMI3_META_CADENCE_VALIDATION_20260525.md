# WACCM-X/SAMI3 Metadata Cadence Validation

Date: 2026-05-25

## Scope

This tightens the live neutral metadata contract by checking the sender time
metadata:

```text
dtime_phys_s > 0
send_every_nsteps > 0
packet_hour == nstep * dtime_phys_s / 3600
```

This is separate from receiver time-axis validation.  It verifies that the
metadata written at the CAM sender call site carries a self-consistent coupling
time.

## Validation Result

Existing WACCM-X live neutral plus two-frame phi smoke:

```text
run = logs/waccmx_live_neutral_voltron_phi_2frame_20260525
dtime_phys_s = 300.0
send_every_nsteps = 1
nstep = 0
packet_hour = 0.0
expected_packet_hour = 0.0
overall = ok
```

## Evidence

Archived under:

```text
logs/waccmx_live_meta_cadence_validation_20260525/
```

including:

```text
waccmx_static_2frame_meta_cadence.txt
waccmx_static_2frame_meta_cadence.json
```
