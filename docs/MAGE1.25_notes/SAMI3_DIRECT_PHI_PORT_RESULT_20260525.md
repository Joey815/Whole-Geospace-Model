# SAMI3 Direct Phi Port Result - 2026-05-25

## Purpose

This test moves the REMIX/Voltron -> SAMI3 `phi_weimer` handoff one step beyond
the previous CESM direct-wait bridge.

Previous successful path:

```text
Voltron/REMIX writes phi payload file
CESM/WACCM-X sender waits for file
CESM/WACCM-X sender forwards phi over the neutral MPI intercomm
SAMI3 receives phi on the existing WACCM-X connection
```

New validated path:

```text
neutral sender -> SAMI3 neutral MPI port
direct phi sender -> SAMI3 rank0 phi-only MPI port
```

This keeps WACCM-X neutral forcing and REMIX/Voltron electrodynamic forcing on
separate online MPI channels.

## Code Changes

SAMI3 receiver:

```text
code/sami3_receiver/waccmx_neutral_mod.f90
```

New optional environment contract:

```text
SAMI3_PHI_DIRECT_PORT_FILE=/path/to/sami3_direct_phi_port.txt
```

If this variable is set, SAMI3 rank0 opens a second MPI port on
`MPI_COMM_SELF` when `waccmx_recv_phi_weimer_online()` first needs a
`phi_weimer` frame.  The phi data are then received from that direct phi
intercomm instead of from the WACCM-X neutral intercomm.

Direct sender:

```text
scripts/wxsami3_phi_direct_sender_stub.c
```

It reads the existing REMIX/Voltron SAMI3 phi payload schema and sends:

```text
TAG_PHI_HEADER
TAG_PHI_HOUR
TAG_PHI_VALID_UNTIL
TAG_PHI_DATA
TAG_DONE
```

Standalone validation launcher:

```text
slurm/run_sami3_online_receiver_direct_phi_port_20260525.sbatch
```

Validator:

```text
scripts/validate_sami3_direct_phi_run.py
```

## Run Result

```text
jobid = 7665788
jobname = sami3_dphi
state = COMPLETED
exit = 0:0
elapsed = 00:01:42
node = qhcn181
archive = logs/sami3_direct_phi_port_20260525/
archive ok = true
```

Receiver markers:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
WACCMX_PHI_RECV           0           2   0.00000000       0.00000000       1.38888892E-03  -36.9306145       31.4838161
WACCMX_PHI_RECV           1           2   2.22222228E-03   1.38888892E-03   1.00000002E+30  -37.6830177       31.8911915
MASTER: All Done!
WACCMX online done signal received:           1
SAMI3 direct phi done signal received:           2
```

Direct phi sender markers:

```text
PHI_DIRECT_SENDER payload_format=remix_sami3_phi_payload.v1 nframes=2
PHI_DIRECT_SENDER sent frame=0/2 hour=0 valid_until=0.00138889
PHI_DIRECT_SENDER sent frame=1/2 hour=0.00138889 valid_until=1e+30
PHI_DIRECT_SENDER sent done=2
```

Validation:

```text
validate_sami3_direct_phi_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.1033e+06 max_rel=4.86991e-13
```

## Interpretation

This is still a diagnostic/runtime adapter, not the final production REMIX
coupler.  The phi payload is still generated as a file by the current Voltron
writer, but the online MPI handoff into SAMI3 no longer depends on CESM reading
and forwarding that file.

What is now validated:

```text
1. SAMI3 can hold the existing neutral online connection and a separate phi-only connection.
2. The direct phi sender can connect later, when SAMI3 first asks for phi_weimer.
3. SAMI3 receives two time-ordered Voltron-derived phi frames on the direct port.
4. Neutral packet QC remains unchanged.
5. Both neutral done and direct-phi done complete cleanly.
```

Next production step:

```text
Replace the file-backed direct phi sender with a real REMIX/Voltron runtime sender.
```
