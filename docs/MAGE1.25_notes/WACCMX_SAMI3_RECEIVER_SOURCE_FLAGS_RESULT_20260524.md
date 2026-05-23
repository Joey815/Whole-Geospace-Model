# WACCM-X -> SAMI3 Receiver Source/Fallback Diagnostics

Date: 2026-05-24 CST

## Objective

Carry the sender-side live neutral source/fallback accounting into the SAMI3
receiver diagnostics without changing the MPI payload binary layout.

This remains diagnostic/runtime adapter work.  It does not make the current
prototype production live neutral forcing.

## Code Changes

Updated SAMI3 receiver:

```text
code/sami3_receiver/waccmx_neutral_mod.f90
```

New receiver log lines:

```text
WACCMX_RECV_SOURCE_FLAGS task step packet_hour nlocal valid_i invalid_i valid_f invalid_f he_native_i he_native_f w_zero_i w_zero_f
WACCMX_APPLY_QC task nll hr nplane valid_i invalid_i valid_f invalid_f he_native_i he_native_f w_zero_i w_zero_f
```

Important limitation: the current MPI payload has only one invalid sentinel,
negative H density.  The receiver can verify total native fallback samples, but
it cannot distinguish above-live-top fallback from N2-invalid fallback without a
future sidecar or new MPI flag tag.

Updated live-dump replay helper:

```text
scripts/make_wxsami3_payload_from_live_dump.c
```

The helper now honors:

```text
WXSAMI3_N2_NEGATIVE_MODE=floor|invalid|fail
```

This keeps post-run replay comparison consistent with the sender when negative
residual N2 samples are deliberately marked invalid instead of floored.

## Validation

SAMI3 was rebuilt with the OpenMPI wrapper used by the online `prun/prte`
launcher:

```text
/apps/support/intel_spr_rocky8.9/openmpi/5.0.3/gcc8.5.0/bin/mpif90
```

The resulting executable links against OpenMPI 5.0.3 `libmpi`.  A bad local
build with the Intel MPI wrapper was caught first: job 7641664 reached
`numworkers=0` and was cancelled.  That was an environment mismatch, not a
receiver source-flag logic failure.

The first OpenMPI full run, job 7641667, completed the CESM/SAMI3 online model
phase but failed in replay comparison because the replay helper still floored
negative residual N2.  After adding the same N2 negative-mode switch to the
helper, job 7641669 completed successfully:

```text
job id: 7641669
script: slurm/run_waccmx_cam_sami3_live_payload_f19_multipacket_n2invalid_recvflags_20260524.sbatch
status: COMPLETED
exit code: 0:0
elapsed: 00:03:33
node: qhcn078
```

Sender packet QC:

```text
packet 0:
  samples = 6031360
  invalid = 1819595
  above_live_top = 1641376
  n2_residual_used = 4389984
  n2_residual_negative = 178219

packet 1:
  samples = 6031360
  invalid = 1819902
  above_live_top = 1642002
  n2_residual_used = 4389358
  n2_residual_negative = 177900
```

Receiver model markers:

```text
WACCMX_RECV_SOURCE_FLAGS present on worker ranks
WACCMX_APPLY_QC present during neutral application
MASTER: All Done!
WACCMX online done signal received: 2
```

Replay-vs-receiver QC:

```text
pkt000000: WACCMX_RECV_QC compare ok, ranks=32, max_rel=4.83248e-13
pkt000001: WACCMX_RECV_QC compare ok, ranks=32, max_rel=6.76502e-13
```

## Artifacts

Committed small artifacts:

```text
logs/recv_source_flags_full_sami3_20260524/slurm_7641669_recvflags.out
logs/recv_source_flags_full_sami3_20260524/sami3_online_receiver_7641669.out
logs/recv_source_flags_full_sami3_20260524/wxsami3_live_meta.json
logs/recv_source_flags_full_sami3_20260524/wxsami3_physstate_meta.json
logs/recv_source_flags_full_sami3_20260524/recv_qc_compare_pkt000000.txt
logs/recv_source_flags_full_sami3_20260524/recv_qc_compare_pkt000001.txt
logs/recv_source_flags_full_sami3_20260524/replay_builder_pkt000000.out
logs/recv_source_flags_full_sami3_20260524/replay_builder_pkt000001.out
logs/recv_source_flags_full_sami3_20260524/live_dump_summary_pkt000000.txt
logs/recv_source_flags_full_sami3_20260524/live_dump_summary_pkt000001.txt
logs/recv_source_flags_full_sami3_20260524/slurm_7641667_failed_replay_compare.err
```

Large artifacts intentionally not committed:

```text
391171702 /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_multipacket_n2invalid_recvflags_20260524_0000/live_dump
530764416 /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_multipacket_n2invalid_recvflags_20260524_0000/replay_pkt000000
530764416 /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_multipacket_n2invalid_recvflags_20260524_0000/replay_pkt000001
```

## Next Step

The next WACCM-X -> SAMI3 neutral-forcing step is no longer basic transport; it
is physics hardening: explicit WACCM-X-top transition/blending metadata, and a
decision on whether receiver-side reason flags need a new sidecar/MPI tag so
above-top and N2-invalid fallback are distinguishable at ingest time.
