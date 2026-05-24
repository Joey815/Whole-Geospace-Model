# WACCM-X/SAMI3 Direct-Wait Fixed Result

Date: 2026-05-25

## Result

The same-job Voltron phi writer + CESM/WACCM-X direct-wait path now passes the
strict archive gate:

```text
jobid = 7665666
jobname = wxsami3_ap2w
state = COMPLETED
exit = 0:0
elapsed = 00:08:05
node = qhcn644
batch MaxRSS = 63370296K
archive = logs/waccmx_append2_directwait_fixed_20260525/
archive ok = true
```

This run used the endian wait fix in
`wxsami3_wait_for_phi_payload()` and the rebuilt CESM executable.

## Direct-Wait Evidence

The launcher started Voltron first, then started CESM/SAMI3 while the Voltron
writer was still active:

```text
VOLTRON_WRITER_PID=2928528
DIRECT_WAIT_MODE=1
PHI_PAYLOAD_WAIT_SECONDS=240
PHI_PAYLOAD_STABLE_SECONDS=1
```

CESM/WACCM-X then waited only one second for the payload and sent both frames:

```text
WXSAMI3 sent live neutral packet: nstep,packet_hour,count=0 0.00000000 0
WXSAMI3 phi payload ready after wait: ... size=97044 elapsed=1
WXSAMI3 sent phi frame: iframe=0 nframes=2 hour=0.00000000 valid_until=1.38888892E-03
WXSAMI3 sent phi frame: iframe=1 nframes=2 hour=1.38888892E-03 valid_until=1.00000002E+30
WXSAMI3 sent phi payload frames: 2
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

SAMI3 received both frames and completed:

```text
WACCMX_PHI_RECV 0 2 0.00000000 0.00000000 1.38888892E-03 -36.9306145 31.4838161
WACCMX_PHI_RECV 1 2 2.22222228E-03 1.38888892E-03 1.00000002E+30 -37.6830177 31.8911915
MASTER: All Done!
WACCMX online done signal received: 1
```

## Payload Contract

```text
payload size = 97044
header = [20260524, 1, 125, 97, 2]
frame0 hour = 0
frame1 hour = 0.0013888889
nonzero_counts = [3492, 3492]
frame1_minus_frame0_max_abs = 3.5858946
frame1_minus_frame0_rms = 0.68732562
```

## Validator Matrix

All current archive validators passed:

```text
validate_wxsami3_append2_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
validate_wxsami3_live_packet_contract = returncode 0
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = returncode 0
validate_wxsami3_topblend_policy = returncode 0
validate_wxsami3_runtime_map = returncode 0
```

The receiver/source-flag balance closes exactly:

```text
samples = 6031360
valid = 4211765
invalid = 1819595
above_top = 1641376
N2 residual invalid = 178219
unknown invalid = 0
apply_qc_lines = 160
apply_source_flag_lines = 160
apply_blend_lines = 160
blend_i + blend_f = 2708
```

The live replay comparison also matched the receiver:

```text
WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.08794e+06 max_rel=4.83248e-13
```

## Launcher Follow-up

The first fixed run had to stop the still-running background Voltron writer
after CESM/SAMI3 had already completed, because the direct-wait gate only needs
the produced payload and receiver confirmation.  The launcher is now patched to
do this automatically:

```text
Stopping Voltron writer after CESM/SAMI3 direct-wait completion
kill "$voltron_pid"
wait "$voltron_pid" || true
```

That keeps future direct-wait validation jobs from idling until the standalone
Voltron writer naturally exits.

## Status

This closes the current online control path milestone:

```text
Voltron/REMIX phi producer in same job
CESM/WACCM-X live neutral sender
CESM wait-for-phi readiness gate
SAMI3 online neutral receiver
SAMI3 online phi receiver
receiver done tag
strict archive validation
```

It is still a prototype online path.  Remaining production blockers are the
same physical blockers as before: direct live REMIX MPI source instead of file
payload handoff, f09/distributed live remap, production top-blend policy, and
true traced flux-tube weighting/mapping for SAMI3 -> RAIJU/GAMERA.
