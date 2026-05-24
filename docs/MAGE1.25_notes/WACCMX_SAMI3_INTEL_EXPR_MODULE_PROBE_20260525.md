# WACCM-X/SAMI3 intel_expr Module Probe

Date: 2026-05-25

## Scope

The main append2 WACCM-X/SAMI3 integration job is queued on `intel`.  An
`intel_expr` copy had failed immediately as job `7660816` because the module
command returned nonzero after reading `/apps/support/modulefiles/.modulerc`.

This note records the probe result and the launcher hardening for the
`intel_expr` fallback launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_intel_expr_20260525.sbatch
```

## Findings

Probe jobs on `qhcn816`:

```text
7665193 modprobe_expr  COMPLETED
7665194 modprobe_expr2 COMPLETED
7665195 cesmenv_expr   COMPLETED
```

`module load intel/oneapi/2023.2.0` and
`module load intel/hdf5/1.13.0/intel2023.2_impi2023.2` returned code `1`
because the Tcl module command complained about `module-hide` in `.modulerc`.
However, the requested environment was still applied:

```text
LOADEDMODULES=intel/oneapi/2023.2.0:intel/hdf5/1.13.0/intel2023.2_impi2023.2
LD_LIBRARY_PATH includes oneAPI and HDF5 paths
PATH includes oneAPI MPI and HDF5 paths
```

The CESM case environment itself was safe on `intel_expr`:

```text
source .env_mach_specific.sh return code = 0
mpiexec/prte/prun resolved from OpenMPI 5.0.3
```

## Launcher Change

The `intel_expr` fallback launcher now wraps module loads as:

```bash
safe_module_load() {
  module load "$@" || echo "WARN: module load returned nonzero but continuing: $*" >&2
}
```

This prevents `set -e` from killing the job on the non-fatal `.modulerc`
warning while preserving the loaded environment.

## Operational Note

The `intel_expr` launcher is now a viable fallback candidate, but it has not
been resubmitted as a full WACCM-X/SAMI3 job in this pass to avoid racing the
already queued `intel` job against the same CESM run directory and
`nuopc.runconfig` mutation.

## Evidence

Probe logs:

```text
logs/module_probe_intel_expr_7665193.out
logs/module_probe_intel_expr_7665193.err
logs/module_probe_intel_expr2_7665194.out
logs/module_probe_intel_expr2_7665194.err
logs/cesm_env_probe_intel_expr_7665195.out
logs/cesm_env_probe_intel_expr_7665195.err
```
