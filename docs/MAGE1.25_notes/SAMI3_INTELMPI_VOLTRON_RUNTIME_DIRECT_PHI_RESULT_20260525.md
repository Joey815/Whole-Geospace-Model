# SAMI3 Intel MPI Voltron Runtime Direct Phi Result - 2026-05-25

## Purpose

This pass replaces the standalone direct-phi sender stub with a Voltron runtime
sender.  The intended online path is:

```text
SAMI3 opens neutral MPI port
neutral replay sender connects and sends WACCM-X/CAM neutral packet
SAMI3 opens a second phi-only MPI port when phi_weimer is needed
MPI-enabled serial voltron.x computes/remaps REMIX potential
voltron.x connects directly to the SAMI3 phi port and sends phi frames
```

This is still a runtime adapter prototype.  It validates the online control path
and payload semantics; it is not yet production REMIX/SAMI3 electrodynamic
coupling.

## Important Route Correction

The standalone `voltron_mpi.x` executable is not the right driver for this
smoke.  It allocates the MPI Voltron/Gamera coupler path and waits for a remote
MPI Gamera application.  In this configuration it got past the earlier GCM
rank abort but then hung in the Gamera coupler route.

The working route is an MPI-enabled serial `voltron.x`:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_phi_direct_mpi_ifort_20260525/bin/voltron.x
```

The only MPI use in this executable is the SAMI3 direct-phi port connect/send
inside `waccmx_stub_backend.F90`.

## Code Changes

Voltron backend:

```text
code/kaiju_sami3_moments/src/remix/waccmx_stub_backend.F90
```

New behavior under `KAIJU_ENABLE_MPI`:

```text
WACCMX_SAMI3_PHI_DIRECT_PORT_FILE=/path/to/sami3_direct_phi_port.txt
WACCMX_SAMI3_PHI_MAX_FRAMES=2
WACCMX_SAMI3_PHI_VALID_HOURS=0.0013888889
WACCMX_SAMI3_PHI_FINAL_VALID_UNTIL_HOUR=1.0e30
```

When the direct port file is set, Voltron:

```text
1. lazily calls MPI_Init if the serial executable has not already initialized MPI
2. reads the SAMI3 port name
3. MPI_Comm_connects from MPI_COMM_SELF
4. sends TAG_PHI_HEADER / TAG_PHI_HOUR / TAG_PHI_VALID_UNTIL / TAG_PHI_DATA
5. after the final frame, sends TAG_DONE and disconnects
6. MPI_Finalizes only if this backend started MPI
```

SAMI3 receiver:

```text
code/sami3_receiver/waccmx_neutral_mod.f90
```

The neutral online port name is now broadcast before collective
`MPI_Comm_accept`, so non-root receiver ranks do not enter accept with an
undefined port-name buffer.

Launcher:

```text
slurm/run_sami3_intelmpi_voltron_runtime_direct_phi_20260525.sbatch
```

Critical settings:

```text
VOLTRON_EXE=.../bin/voltron.x
Voltron launch: mpirun -n 1 ./voltron.x gtrd_20211204_0500_0510-waccmxfile-smoke.xml
SAMI3 maxstep=20
SAMI3 hrmax=.020000
Voltron tFin=10.25
```

The `hrmax=.020000` setting is needed for this short smoke to produce
`ntmmax=2`.  Lower tested values such as `.005` and `.012` produced
`ntmmax=1`, so SAMI3 exited before it could consume frame 1.

## Active Run Snapshot

Current job:

```text
jobid = 7666704
jobname = sami3_vrtd
node = qhcn012
time limit = 00:30:00
run dir = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/sami3_intelmpi_voltron_runtime_direct_phi_20260525_0000
```

At the snapshot archived in this repository, the job had not yet reached the
natural SAMI3 finalize path.  The strict whole-run validator therefore remains
failed on finalize artifacts, but the direct runtime phi handshake is complete.

## Runtime Markers

Voltron runtime sender:

```text
WACCMX_SAMI3_PHI_DIRECT connected
WACCMX_SAMI3_PHI_DIRECT sent frame=0 nframes=2 hour=0.0 valid_until=1.3888889E-03
WACCMX_SAMI3_PHI_DIRECT sent frame=1 nframes=2 hour=1.3888889E-03 valid_until=1.0000000E+30
WACCMX_SAMI3_PHI_DIRECT sent done=2
```

SAMI3 receiver:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
WACCMX_PHI_RECV 0 2 hour=0.0 valid_until=1.3888889E-03 min=-36.93061 max=31.48382
WACCMX_PHI_RECV 1 2 hour=1.3888889E-03 valid_until=1.0000000E+30 min=-37.68302 max=31.89119
```

Neutral sender:

```text
NEUTRAL_SENDER sent step=0 packet_hour=0 rank=0001..0032
NEUTRAL_SENDER sent done signal
NEUTRAL_SENDER done
```

## Validation

Archived evidence:

```text
logs/sami3_intelmpi_voltron_runtime_direct_phi_20260525/
```

Payload contract:

```text
validate_remix_sami3_phi_payload = overall=ok
header = magic=20260524 version=1 nlat=125 nlon=97 nframes=2
frame indices = [0, 1]
hours = [0.0, 0.0013888889]
valid_until = [0.0013888889, 1.0e30]
max_abs_diff between frames = 3.5858946
```

Runtime handshake validator:

```text
validate_sami3_direct_phi_run --allow-incomplete-run = overall=ok
```

Strict whole-run validator:

```text
validate_sami3_direct_phi_run = overall=FAIL
```

The strict failure is expected for this snapshot because the job had not yet
written:

```text
MASTER: All Done!
WACCMX online done signal received
SAMI3 direct phi done signal received
recv_qc_compare.txt
```

The `no_fatal_markers` check has been tightened so configuration keys such as
`abortOnNonfinit` are not counted as fatal aborts.

## Current Interpretation

Validated now:

```text
1. SAMI3 can run the neutral MPI intercomm and a second direct phi intercomm.
2. MPI-enabled serial voltron.x can connect directly to SAMI3.
3. Voltron runtime REMIX potential is remapped into the SAMI3 phi payload grid.
4. Two physically different runtime phi frames are transmitted and consumed.
5. The neutral replay channel still sends the expected WACCM-X packet and done tag.
```

Still unresolved:

```text
1. The current full model run has not yet naturally finalized in the archived snapshot.
2. SAMI3 direct phi done is currently consumed only in online finalize.
3. If SAMI3 remains in a long solver tail after frame 1, add a smoke-only stop/finalize gate
   or a marker-driven archive path that is explicitly not a natural-completion test.
4. Production coupling still needs cadence management, REMIX/SAMI3 time synchronization,
   and longer multi-cycle validation.
```

## Next Step

Keep polling job `7666704` until it either completes or reaches the 30 minute
limit.  Then:

```text
1. If it completes: rerun strict validators, archive recv_qc_compare, and update this result.
2. If it times out: preserve the timeout as evidence, document the frame-1 solver/finalize tail,
   and implement a dedicated smoke-exit strategy rather than rerunning the same parameters.
```

