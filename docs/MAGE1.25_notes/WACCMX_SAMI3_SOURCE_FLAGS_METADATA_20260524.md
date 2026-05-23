# WACCM-X -> SAMI3 Source Flag Metadata Result

Date: 2026-05-24 CST

## Objective

Make the f19 WACCM-X -> SAMI3 live neutral sender state explicit about which
payload samples are real CAM/WACCM-X values and which samples intentionally ask
SAMI3 to retain native neutral values.

This is a metadata-only diagnostic hardening step.  It does not change the MPI
payload binary layout or the SAMI3 receiver payload parser.

## Code Change

Updated:

```text
code/cesm_source_mods/src.cam/wxsami3_online_stub_mod.F90
```

The live packet metadata now writes:

```json
"source_flags": {
  "WACCMX_VALID": 4211362,
  "SAMI3_NATIVE_ABOVE_TOP": 1642906,
  "SAMI3_NATIVE_N2_INVALID": 177092,
  "SAMI3_NATIVE_OTHER_INVALID": 0,
  "SAMI3_NATIVE_HE": "policy: He payload value -1",
  "SAMI3_NATIVE_W": "policy: W payload value 0"
}
```

The diagnostic metadata writer also records the intended source flag contract:

```text
WACCMX_VALID
SAMI3_NATIVE_ABOVE_TOP
SAMI3_NATIVE_N2_INVALID
SAMI3_NATIVE_OTHER_INVALID
SAMI3_NATIVE_HE
SAMI3_NATIVE_W
```

The counts are derived from the existing runtime QC counters:

```text
WACCMX_VALID = samples - invalid
SAMI3_NATIVE_ABOVE_TOP = above_live_top
SAMI3_NATIVE_N2_INVALID = n2_residual_negative when N2 mode is invalid
SAMI3_NATIVE_OTHER_INVALID = invalid - above_live_top - N2-invalid
```

## Validation

The copied f19 CESM case rebuilt successfully after the SourceMod update:

```text
MODEL BUILD HAS FINISHED SUCCESSFULLY
Total build time: 18.888089 seconds
```

Receiver-stub validation job:

```text
job id: 7641645
script: slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_source_flags_20260524.sbatch
status: COMPLETED
exit code: 0:0
elapsed: 00:02:12
node: qhcn078
```

The sender produced three runtime live packets and a done signal.  The receiver
stub saw all three packets on ranks 1..32, and every rank got the done tag:

```text
rank 0: packets=0, done_value=3
ranks 1..32: packets=3, done_value=3
WXSAMI3_RECEIVER_STUB complete
```

Packet 2 metadata:

```text
samples = 6031360
invalid = 1819998
above_live_top = 1642906
n2_residual_used = 4388454
n2_residual_negative = 177092
WACCMX_VALID = 4211362
SAMI3_NATIVE_ABOVE_TOP = 1642906
SAMI3_NATIVE_N2_INVALID = 177092
SAMI3_NATIVE_OTHER_INVALID = 0
```

This matches the intended invalid-mode accounting: the 177092 negative residual
N2 samples are not silently floored; they are explicitly counted as native
fallback samples.

## Artifacts

Committed small artifacts:

```text
logs/source_flags_20260524/wxsami3_live_meta.json
logs/source_flags_20260524/wxsami3_physstate_meta.json
logs/source_flags_20260524/slurm_7641645_source_flags.out
logs/source_flags_20260524/receiver_stub_7641645.out
slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_source_flags_20260524.sbatch
```

Large artifact intentionally not committed:

```text
586754998 /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_source_flags_20260524_0000/live_dump
```

## Next Step

Carry the source/fallback accounting across the SAMI3 receiver side.  The first
version can remain diagnostic-only: count invalid/native fallback reasons during
receiver ingest and verify they agree with sender metadata for a full SAMI3
two-packet smoke run using `WXSAMI3_N2_NEGATIVE_MODE=invalid`.
