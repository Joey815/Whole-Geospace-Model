# SAMI3 OpenMPI Voltron Runtime Direct Phi Result - 2026-05-25

## Purpose

This pass repeats the runtime Voltron -> SAMI3 direct-phi smoke with the same
MPI family used by the current WACCM-X/CESM + SAMI3 online branch:

```text
OpenMPI/PRTE SAMI3 receiver
OpenMPI neutral replay sender
OpenMPI-enabled serial voltron.x
```

The Intel MPI direct-phi smoke proved the runtime adapter, but it cannot be
directly merged into the OpenMPI/PRTE WACCM-X/CESM live-neutral job.  This pass
therefore validates the direct REMIX/Voltron phi route with a compatible MPI
stack.

## Build Provenance

OpenMPI `voltron.x` build:

```text
build_dir = /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_phi_direct_openmpi_20260525
source_dir = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523
voltron_exe = /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_phi_direct_openmpi_20260525/bin/voltron.x
toolchain = openmpi-5.0.3-gcc8.5.0 + netcdf/hdf5 gcc8.5.0_ompi5.0.3
```

The copied Kaiju tree needed one compatibility patch for GNU Fortran 8.5:

```text
code/kaiju_sami3_moments/patches/tgcm_no_findloc_gfortran8.patch
```

This replaces `findloc(...)` in `src/remix/tgcm.F90` with an explicit loop so
the OpenMPI/GNU build can compile the REMIX/TIE-GCM reader path.

## Launcher

```text
slurm/run_sami3_openmpi_voltron_runtime_direct_phi_20260525.sbatch
```

The critical runtime detail is that Voltron is launched under the existing PRTE
DVM and the direct-phi environment is explicitly exported through `prun -x`.
Without those explicit exports, Voltron can write its HDF5 forwarding package
but does not enter the `WACCMX_SAMI3_PHI_DIRECT` MPI send path.

## Completed Smoke Run

```text
jobid = 7668135
jobname = sami3_ovrtd
state = COMPLETED
exit = 0:0
elapsed = 00:05:23
node = qhcn012
batch MaxRSS = 40607864K
run dir = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/sami3_openmpi_voltron_runtime_direct_phi_20260525_0000
archive = logs/sami3_openmpi_voltron_runtime_direct_phi_20260525/
```

Smoke-only finalize controls:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 1
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 1
```

These controls are for short-run completion.  They do not define the production
potential cadence policy.

## Runtime Markers

SAMI3 receiver:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
WACCMX_PHI_RECV frame 0 of 2, min/max = -36.9728775, 31.5048161
WACCMX_PHI_RECV frame 1 of 2, min/max = -37.7063637, 31.7590370
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL active; returning cached phi
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

Voltron runtime sender:

```text
WACCMX_SAMI3_PHI_DIRECT connected
WACCMX_SAMI3_PHI_DIRECT sent frame=0 nframes=2 hour=0 valid_until=1.38888892E-03
WACCMX_SAMI3_PHI_DIRECT sent frame=1 nframes=2 hour=1.38888892E-03 valid_until=1.00000002E+30
WACCMX_SAMI3_PHI_DIRECT sent done=2
WACCMX_SAMI3_PHI_DIRECT stop after done requested
```

Neutral replay sender:

```text
NEUTRAL_SENDER sent step=0 packet_hour=0 rank=0001..0032
NEUTRAL_SENDER sent done signal
NEUTRAL_SENDER done
```

## Validation

Strict direct-phi runtime validator:

```text
validate_sami3_direct_phi_run = overall=ok
```

Phi payload contract:

```text
validate_remix_sami3_phi_payload = overall=ok
header = magic=20260524 version=1 nlat=125 nlon=97 nframes=2
frame indices = [0, 1]
hours = [0.0, 0.0013888889]
valid_until = [0.0013888889, 1.0e30]
max_abs_diff between frames = 3.4961066
```

Neutral replay/QC:

```text
WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.1033e+06 max_rel=4.86991e-13
```

## Current Interpretation

Validated now:

```text
1. The Voltron direct-phi runtime adapter works with OpenMPI/PRTE.
2. SAMI3 can hold both the neutral online intercomm and the direct phi intercomm
   in the same OpenMPI job.
3. Runtime Voltron phi frames are remapped into the SAMI3 phi grid, change over
   time, and are consumed by SAMI3.
4. The neutral replay channel still passes its receiver-side QC.
5. SAMI3, neutral sender, and Voltron all finalize cleanly on one node.
```

Next target:

```text
Merge this OpenMPI direct Voltron phi route into the existing live WACCM-X/CESM
phys_state(:) neutral sender launcher, replacing the current file-backed
append/direct-wait phi handoff.
```
