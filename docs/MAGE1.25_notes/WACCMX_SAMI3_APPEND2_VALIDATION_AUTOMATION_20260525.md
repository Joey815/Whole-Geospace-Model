# WACCM-X/SAMI3 Append2 Validation Automation

Date: 2026-05-25

## Purpose

The full coupling target now has several independently validated pieces:

```text
WACCM-X live neutral sender
Voltron/REMIX real append2 phi writer
SAMI3 online MPI receiver
SAMI3 online phi_weimer time gate
neutral replay QC
```

The queued full integration run should verify these pieces together.  To avoid
manual log scanning after every rerun, the repository now includes a single
log-driven validator:

```text
scripts/validate_wxsami3_append2_run.py
```

## Checks

The validator checks:

```text
run directory exists
SAMI3 MPI phi payload magic/version/grid/frame count
first phi frame starts at hour=0
WACCM-X sender reports expected phi frame count
SAMI3 receiver logs expected WACCMX_PHI_RECV count
SAMI3 reaches MASTER: All Done!
CESM/WACCM-X reaches END OF MODEL RUN
neutral replay QC reports WACCMX_RECV_QC compare ok
fatal/error markers are absent
```

## Example Commands

Completed two-frame integration smoke:

```bash
python3 scripts/validate_wxsami3_append2_run.py \
  --run-dir logs/waccmx_live_neutral_voltron_phi_2frame_20260525 \
  --expected-phi-frames 2
```

Current queued full append2 integration run, while incomplete:

```bash
python3 scripts/validate_wxsami3_append2_run.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525_0000 \
  --expected-phi-frames 2 \
  --allow-incomplete
```

SAMI3 receiver-only real Voltron append2 payload validation:

```bash
python3 scripts/validate_wxsami3_append2_run.py \
  --run-dir logs/sami3_receiver_voltron_phi_append2_offset_20260525 \
  --phi-payload logs/voltron_phi_append_writer_2frame_offset_20260525/remix_sami3_phi_payload_append_writer_2frame_offset.bin \
  --expected-phi-frames 2 \
  --allow-incomplete
```

## Regression Result

Against the completed two-frame integration smoke:

```text
ok   phi_payload_header: [20260524, 1, 125, 97, 2]
ok   phi_payload_frame_count: nframes=2, expected=2
ok   phi_payload_starts_at_zero: first_hour=0.0
ok   sender_phi_frames: sender_phi_frame_markers=2
ok   sender_phi_payload_frame_count: reported=2, expected=2
ok   receiver_phi_frames: receiver_phi_markers=4
ok   receiver_done: MASTER: All Done!
ok   sender_done: END OF MODEL RUN
ok   neutral_replay_qc: qc_ok_markers=2
ok   fatal_markers_absent: matches=0
overall=ok
```

## Role In Final Coupling Workflow

This script is now the acceptance gate for the pending full integration run:

```text
Voltron real append2 payload
  -> CESM/WACCM-X live sender
  -> SAMI3 online receiver
  -> receiver time-gated phi update
  -> neutral replay QC
```

When job 7659727 completes, run the validator on its run directory before
archiving and pushing the result.
