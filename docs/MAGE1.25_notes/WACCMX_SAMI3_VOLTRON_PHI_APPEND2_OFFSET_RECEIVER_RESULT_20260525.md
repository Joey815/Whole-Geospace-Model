# SAMI3 Receiver Result For Voltron Append2 Offset Phi Payload

Date: 2026-05-25

## Purpose

After adding the Voltron phi writer frame-hour offset, validate the resulting
real append2 MPI phi payload on the SAMI3 online receiver path before the larger
CESM/WACCM-X live sender integration gets a full 49-rank node.

This test uses:

```text
real Voltron/REMIX append2 payload
  -> wxsami3_neutral_phi_sender_stub.c
  -> SAMI3 online MPI receiver
  -> SAMI3 online phi_weimer reader
```

It does not use the CESM/WACCM-X sender; that full integration remains queued
as job 7659727.

## Run

Launcher:

```text
slurm/run_sami3_online_receiver_voltron_phi_append2_offset_20260525.sbatch
```

Slurm:

```text
jobid: 7659750
state: COMPLETED
exit: 0:0
elapsed: 00:01:37
node: qhcn025
```

Archived evidence:

```text
logs/sami3_receiver_voltron_phi_append2_offset_20260525/
```

## Sender Evidence

```text
NEUTRAL_PHI_SENDER phi_payload_format=remix_sami3_phi_payload.v1 nframes=2
NEUTRAL_PHI_SENDER sent phi frame=0/2 hour=0 valid_until=0.00138889
NEUTRAL_PHI_SENDER sent phi frame=1/2 hour=0.00138889 valid_until=1e+30
NEUTRAL_PHI_SENDER sent done signal
```

## SAMI3 Receiver Evidence

```text
WACCMX_PHI_RECV 0 2 hrut=0 frame_hour=0 valid_until=1.38888892E-03 min=-36.9306145 max=31.4838161
hrutw2 = 0 1.38888892E-03

WACCMX_PHI_RECV 1 2 hrut=2.22222228E-03 frame_hour=1.38888892E-03 valid_until=1.00000002E+30 min=-37.6830177 max=31.8911915
hrutw2 = 2.22222228E-03 1.00000002E+30

MASTER: All Done!
WACCMX online done signal received: 1
```

Receiver QC:

```text
WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.1033e+06 max_rel=4.86991e-13
```

## Interpretation

The SAMI3 receiver side can consume the real Voltron append2 payload and switch
frames using the existing `hrut/hrutw2` gate. The corrected writer contract now
starts the first frame at `hrut=0`, avoiding the initial gap seen in the
unshifted writer smoke.

Remaining check:

```text
CESM/WACCM-X live sender
  -> real in-job Voltron append2 payload
  -> SAMI3 receiver
```

The queued full integration launcher is:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525.sbatch
jobid: 7659727
```
