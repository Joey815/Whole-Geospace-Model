# WACCM-X -> SAMI3 Source Reason Flag Sidecar

Date: 2026-05-24 CST

## Objective

Promote the WACCM-X -> SAMI3 fallback accounting from metadata-only diagnostics
to a runtime MPI sidecar so the SAMI3 receiver can distinguish why a cell kept
native SAMI3 neutral state.

This is still diagnostic/runtime adapter work.  It validates source semantics
and protocol behavior, but it does not by itself make the prototype production
live WACCM-X neutral forcing.

## Runtime Contract

The neutral payload array order remains unchanged:

```text
header, packet_hour,
denni, tni, ui, vi, wi,
dennf, tnf, uf, vf, wf
```

A new integer sidecar is sent immediately after `wf`:

```text
MPI tag: 212
field: source_flag(nz*nf*nl)
```

Flag values:

```text
1 = WACCMX_VALID
2 = SAMI3_NATIVE_ABOVE_TOP
3 = SAMI3_NATIVE_N2_INVALID
4 = SAMI3_NATIVE_OTHER_INVALID
```

The file-backed sender path also sends tag 212.  Because file payloads only
carry the negative-H sentinel and not the live source reason, file mode maps
valid cells to `WACCMX_VALID` and invalid cells to `SAMI3_NATIVE_OTHER_INVALID`.

## Code Changes

Updated sender:

```text
code/cesm_source_mods/src.cam/wxsami3_online_stub_mod.F90
```

Live mode now computes `source_flag(:)` while sampling CAM `phys_state(:)` and
sends it after `wf`.  File mode derives `source_flag(:)` from the H-density
sentinel and sends the same sidecar, preventing protocol hangs with the updated
receiver.

Updated receiver:

```text
code/sami3_receiver/waccmx_neutral_mod.f90
```

The receiver allocates `w_source_flag(nz,nf,nl)`, receives tag 212 after `w_wf`,
and prints reason-split diagnostics:

```text
WACCMX_RECV_SOURCE_FLAGS task step packet_hour nlocal flag_valid flag_above flag_n2 flag_other flag_unknown valid_i invalid_i valid_f invalid_f he_native_i he_native_f w_zero_i w_zero_f
WACCMX_APPLY_SOURCE_FLAGS task nll hr nplane flag_valid flag_above flag_n2 flag_other flag_unknown
```

Updated receiver stub:

```text
scripts/wxsami3_payload_receiver_stub.c
```

The C stub now receives tag 212, counts the reason flags, and prints
`WXSAMI3_RECEIVER_STUB source_flags ...`.

## Validation

Builds:

```text
CESM case build: success
SAMI3 OpenMPI build: success
C receiver stub OpenMPI build: success
```

Full SAMI3 online validation:

```text
job id: 7645354
script: slurm/run_waccmx_cam_sami3_live_payload_f19_multipacket_reasonflags_20260524.sbatch
status: COMPLETED
exit code: 0:0
elapsed: 00:03:55
node: qhcn078
done signal: 2
```

Receiver source-flag sum for packet 1 matched sender metadata exactly:

```text
receiver = [4211458, 1642002, 177900, 0, 0]
expected = [4211458, 1642002, 177900, 0, 0]
diff     = [0, 0, 0, 0, 0]
```

Replay-vs-receiver QC remains valid:

```text
pkt000000: WACCMX_RECV_QC compare ok, max_rel=4.83248e-13
pkt000001: WACCMX_RECV_QC compare ok, max_rel=6.76502e-13
```

File-mode regression:

```text
job id: 7645380
status: COMPLETED
exit code: 0:0
elapsed: 00:02:26
receiver QC compare max_rel=3.26946e-13
```

File-mode sidecar summary:

```text
flag_valid=4494609
flag_above=0
flag_n2=0
flag_other=1536751
flag_unknown=0
```

Receiver-stub runtime validation:

```text
job id: 7645415
status: COMPLETED
exit code: 0:0
elapsed: 00:02:13
done signal: 3
```

Stub source-flag sum for packet 2 matched sender metadata exactly:

```text
receiver = [4211362, 1642906, 177092, 0, 0]
expected = [4211362, 1642906, 177092, 0, 0]
diff     = [0, 0, 0, 0, 0]
```

## Artifacts

Committed small artifacts:

```text
logs/reason_flags_full_sami3_20260524/
logs/reason_flags_file_regression_20260524/
logs/reason_flags_receiver_stub_20260524/
```

Important files:

```text
logs/reason_flags_full_sami3_20260524/receiver_source_flag_compare.txt
logs/reason_flags_full_sami3_20260524/recv_qc_compare_pkt000000.txt
logs/reason_flags_full_sami3_20260524/recv_qc_compare_pkt000001.txt
logs/reason_flags_file_regression_20260524/receiver_source_flag_summary.txt
logs/reason_flags_receiver_stub_20260524/receiver_stub_source_flag_compare.txt
```

Large artifacts intentionally not committed include live dump binaries, replay
payload binaries, compiled executables, full SAMI3 run directories, and CESM
history/restart files.

## Current Interpretation

The online control path now carries enough source-reason information for the
receiver to audit `above_live_top` and `N2_invalid` fallback separately.  The
remaining neutral-forcing hardening is physical, not basic transport:

```text
explicit WACCM-X-top transition/blending policy
He native/MSIS fallback policy hardening
W-off / vertical-wind policy validation
strict same-call-site live/offline source-state validation
REMIX -> SAMI3 potential/E-field forcing
SAMI3 -> RAIJU/GAMERA flux-tube weighting and L/MLT mapping
```
