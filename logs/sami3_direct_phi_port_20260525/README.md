# SAMI3 Direct Phi Port Validation - 2026-05-25

This archive validates the next step after the CESM direct-wait bridge:

```text
neutral: WACCM-X/CESM-style sender -> SAMI3 neutral MPI port
phi:     direct REMIX/Voltron payload sender -> SAMI3 rank0 phi-only MPI port
```

The run no longer sends phi through the neutral sender connection.  SAMI3 opens
the optional direct phi port when `SAMI3_PHI_DIRECT_PORT_FILE` is set and the
online `phi_weimer` hook requests a frame.

## Result

```text
jobid = 7665788
state = COMPLETED
exit = 0:0
elapsed = 00:01:42
node = qhcn181
archive ok = true
```

Key markers:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
WACCMX_PHI_RECV records = 2
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

Validators:

```text
validate_sami3_direct_phi_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
recv_qc_compare = compare ok
```

Important files:

```text
sami3_online_receiver.out
neutral_sender.out
phi_direct_sender.out
recv_qc_compare.txt
sacct_7665788.txt
validate_sami3_direct_phi_run.txt
validate_remix_sami3_phi_payload.txt
archive_summary.json
```
