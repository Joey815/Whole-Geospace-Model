# WACCM-X/SAMI3 Direct-Wait Phi Launcher

Date: 2026-05-25

## Purpose

The append2 full integration launcher validates:

```text
Voltron writes the two-frame phi payload first
CESM/WACCM-X sender reads the completed file
SAMI3 online receiver consumes the phi frames
```

The direct-wait launcher moves one step closer to the final online route:

```text
Voltron phi writer starts in the same job
CESM/WACCM-X starts while the writer is still an active producer
CESM/WACCM-X sender waits for the payload via WXSAMI3_PHI_PAYLOAD_WAIT_SECONDS
SAMI3 online receiver consumes the phi frames
```

## Launcher

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000
```

Key setting:

```text
WXSAMI3_PHI_PAYLOAD_WAIT_SECONDS = 240
WXSAMI3_PHI_PAYLOAD_STABLE_SECONDS = 1
```

## Submitted Job

```text
jobid = 7661005
jobname = wxsami3_ap2w
state = PENDING
reason = Dependency
dependency = afterok:7659727
```

The dependency is intentional.  Both full WACCM-X/SAMI3 launchers use the same
CESM case executable and `nuopc.runconfig`, so the direct-wait test should only
run after the current full append2 integration job succeeds.

## Acceptance

Use the same validator as the pre-generated append2 full integration run:

```bash
python3 scripts/validate_wxsami3_append2_run.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000 \
  --expected-phi-frames 2 \
  --expect-phi-wait-marker \
  --expect-direct-wait-mode
```

The archive helper should use the same direct-wait checks:

```bash
python3 scripts/archive_wxsami3_append2_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000 \
  --archive-dir logs/waccmx_append2_directwait_20260525 \
  --job-id 7661005 \
  --expected-phi-frames 2 \
  --expected-live-packets 1 \
  --expect-phi-wait-marker \
  --expect-direct-wait-mode \
  --require-nonzero-phi \
  --expect-top-blend-mode linear \
  --expect-blend-bottom-km 600 \
  --expect-blend-top-km 720 \
  --min-total-blend-cells 1 \
  --require-zero-unknown-source-flags \
  --require-he-native \
  --require-w-zero
```

Additional expected markers:

```text
DIRECT_WAIT_MODE=1
VOLTRON_WRITER_PID=<pid>
WXSAMI3 phi payload ready after wait
```
