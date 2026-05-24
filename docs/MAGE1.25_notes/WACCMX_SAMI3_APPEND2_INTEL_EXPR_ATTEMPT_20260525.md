# WACCM-X/SAMI3 Append2 Intel-Expr Attempt

Date: 2026-05-25

## Purpose

The main full append2 integration job was pending on the `intel` partition, so
an independent `intel_expr` copy was submitted to use the idle single-node
resources there.

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_intel_expr_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_intel_expr_20260525_0000
```

## Result

Slurm:

```text
jobid = 7660816
partition = intel_expr
node = qhcn817
state = FAILED
exit = 1:0
elapsed = 00:00:01
```

The job failed before Voltron, CESM, or SAMI3 model startup.  The stderr was:

```text
Module ERROR: invalid command name "module-hide"
```

This came from `/apps/support/modulefiles/.modulerc` on the `intel_expr` node
module environment.

## Interpretation

This is an environment/module initialization failure, not a coupling-path or
model-code failure.  Continue to treat the main `intel` launcher as the valid
full append2 path unless the `intel_expr` module environment is repaired.

Archived evidence:

```text
logs/waccmx_append2_intel_expr_failed_20260525/
```
