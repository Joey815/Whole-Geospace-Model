# REMIX -> SAMI3 Phi Payload Contract Gate

Date: 2026-05-25

## Scope

This adds an independent validator for the versioned REMIX/Voltron -> SAMI3
MPI electric-potential payload:

```text
scripts/validate_remix_sami3_phi_payload.py
```

The gate checks the binary stream before it is sent to SAMI3, separate from the
online receiver log validation.

## Payload Schema

```text
int32 magic = 20260524
int32 version = 1
int32 nlat = 125
int32 nlon = 97
int32 nframes

for each frame:
  int32 frame_index
  float32 frame_hour
  float32 valid_until_hour
  float32 phi[nlat,nlon] in Fortran order
```

## Checks

The validator currently verifies:

```text
payload exists
magic/version/nlat/nlon match expected values
nframes matches expected value when requested
file size exactly matches header and frame count
frame_index is 0..nframes-1
all phi values are finite
frame hours are strictly increasing
valid_until is not earlier than frame_hour
valid_until links to the next frame hour when requested
first frame hour matches the requested value when provided
phi is nonzero when requested
successive frames differ when requested
optional absolute phi_statV bound
```

The WACCM-X/SAMI3 append2 archive helper now runs this validator alongside the
online append2 log validator, live neutral contract validator, top-blend policy
validator, and runtime-map validator.

## Validation Results

Dynamic two-frame offset payload:

```text
payload = logs/voltron_phi_append_writer_2frame_offset_20260525/remix_sami3_phi_payload_append_writer_2frame_offset.bin
nframes = 2
hours = [0.0, 0.0013888889225199819]
valid_until links next hour = ok
nonzero_counts = [3492, 3492]
frame_change_max_abs = 3.5858945846557617
overall = ok
```

Older WACCM-X static two-frame payload:

```text
payload = logs/waccmx_live_neutral_voltron_phi_2frame_20260525/remix_sami3_phi_payload_from_voltron_live_append_2frame.bin
nframes = 2
hours = [0.0, 0.0010000000474974513]
valid_until links next hour = ok
nonzero_counts = [3492, 3492]
overall = ok
```

REMIX MPI payload binary smoke artifact:

```text
payload = logs/remix_sami3_phi_weimer_mpi_payload_bin_20260524/remix_sami3_phi_payload_north_2frame_fast.bin
nframes = 2
hours = [0.0, 0.0010000000474974513]
valid_until links next hour = ok
nonzero_counts = [3492, 3492]
overall = ok
```

The static two-frame artifact intentionally does not pass the changing-frame
gate because both frames contain the same mapped potential.  The dynamic offset
artifact does pass the changing-frame gate and is the correct evidence for a
time-varying phi payload.

## Evidence

Archived under:

```text
logs/remix_sami3_phi_payload_contract_20260525/
```

including text and JSON outputs for:

```text
offset_2frame_validate
waccmx_static_2frame_validate
remix_mpi_payload_bin_validate
```
