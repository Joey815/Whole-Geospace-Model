# WACCM-X -> SAMI3 Source-State Phase Validation (2026-05-24)

This note records the follow-up validation after the f19 live neutral sender
prototype.  The goal was to check whether the live `phys_state(:)` packet at
CAM step 2 can be compared directly against same-run instantaneous CAM history
at model time 00600.

## Active Case

Copied case:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523
```

Original case left untouched:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online
```

Grid:

```text
ATM_GRID=1.9x2.5
lat=96
lon=144
source columns=13824
```

CAM hook:

```fortran
call wxsami3_cam_send(get_nstep(), dtime_phys, phys_state)
```

The call is in `cam_run2`, after `ionosphere_run2` and before
`stepon_run3`, `cam_run4`, and `wshist`.  Therefore CAM history files are not
a strict same-call-site reference for this hook.

## Why A Receiver Stub Was Needed

The validated full SAMI3 online smoke currently consumes two packets cleanly.
Trying to force a third packet by extending the SAMI3 physics run was not the
right diagnostic:

```text
job 7641619: CAM wrote packet 2 dump, but SAMI3 exited after packet 1
job 7641622: extended SAMI3 run hit "Time step too small" and was cancelled
```

For source-state transport validation, the receiver should only test MPI
payload delivery and not advance SAMI3 physics.  A lightweight 33-rank MPI
receiver was therefore added:

```text
scripts/wxsami3_payload_receiver_stub.c
```

It opens the SAMI3-side port, accepts the CAM intercommunicator, receives all
payload tags on worker ranks 1..32, and verifies the final done tag on ranks
0..32.

## Successful Receiver-Stub Run

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_compare_20260524.sbatch
```

Local run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_compare_20260524_0000
```

Job:

```text
job id: 7641623
state: COMPLETED
exit: 0:0
elapsed: 00:02:17
node: qhcn078
```

Sender markers:

```text
WXSAMI3 sent live neutral packet: nstep=0 hour=0.0 count=0
WXSAMI3 sent live neutral packet: nstep=1 hour=0.0833333358 count=1
WXSAMI3 sent live neutral packet: nstep=2 hour=0.166666672 count=2
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

Receiver markers:

```text
rank 1..32: packets=3
rank 0: done_value=3 packets=0
rank 1..32: done_value=3 packets=3
WXSAMI3_RECEIVER_STUB complete
```

This validates the three-packet live CAM sender transport path and the done
signal against an MPI receiver that does not depend on SAMI3 physics stability.

## Packet-2 Live Dump Summary

Packet 2 corresponds to `nstep=2`, `packet_hour=0.166666672`, and uses the
f19 live runtime map:

```text
files=16 ranks=16 total_cols=13824
T_K range      = 113.0644853198483 to 1540.7848935057236
U_m_s range    = -877.2344652281657 to 693.8229320516241
V_m_s range    = -848.9056040321143 to 717.712734883699
PMID_Pa range  = 4.055140885992663e-08 to 107010.83809744766
ZM_m range     = 49.27837860726639 to 726340.8423637329
q_O range      = 2.6478441759302645e-25 to 0.9999399361824781
q_O2 range     = 9.17273404897657e-06 to 0.2373244729492434
q_H range      = 2.8195367284956676e-28 to 0.0049428888078698946
q_N range      = 1.8976942230578848e-23 to 0.060084517945671836
q_NO range     = 8.958463204892557e-19 to 0.0013294114301633402
N2 and He      = missing in CAM registry, retained/fallback by policy
```

Runtime metadata recorded:

```text
payload_version = wxsami3-live-payload-v2
payload_mode = live
runtime_source = CAM phys_state(:)
source composition unit = mass_mixing_ratio
payload density unit = cm^-3
payload wind unit = cm/s
```

The runtime QC still shows the expected prototype limitations:

```text
above_live_top samples = 1642906
N2 residual used      = 4388454
N2 residual negative  = 177092
W                     = payload value 0, CAM omega diagnostic only
He                    = payload value -1, SAMI3 native/MSIS retained
```

## Same-Run History Comparison

The packet-2 live dump was compared to same-run `rh1` and `rh2` files at
`2005-12-31-00600` with `--species-mode molmol`.

Coordinate and OMEGA checks:

```text
lat max_abs       = 1.42e-14
lon max_abs       = 5.68e-14
OMEGA max_abs     = 0
```

But several prognostic/diagnostic fields differ:

```text
PS max_abs        = 106208 Pa
T max_abs         = 147.47 K
U max_abs         = 307.95 m/s
V max_abs         = 163.996 m/s
Z3 max_abs rh1    = 34219.6 m
Z3GM max_abs rh2  = 93460.1 m
O max_abs         = 0.013565 mol/mol
O2 max_abs        = 0.00429665 mol/mol
H max_abs         = 0.00287691 mol/mol
N max_abs         = 0.00311550 mol/mol
NO max_abs        = 2.55023e-05 mol/mol
```

Interpretation:

```text
The live sender is reading the current CAM phys_state(:) at the cam_run2 hook.
The CAM history files are written later in the model phase sequence.
Therefore this comparison is a phase-location diagnostic, not a failure of the
live payload transport.
```

The `PS` mismatch is also expected for the current dump schema: the profile
payload uses `PMID`, while the top-level dump field named `ps` does not match
surface pressure in the later history file.  Do not use that top-level dump
`ps` as a SAMI3 forcing field without a separate schema correction.

## Artifacts Included In This Repo

```text
logs/source_state_compare/live_dump_summary_pkt000000.txt
logs/source_state_compare/live_dump_summary_pkt000001.txt
logs/source_state_compare/live_dump_summary_pkt000002.txt
logs/source_state_compare/live_vs_rh1_00600_pkt000002_compare.txt
logs/source_state_compare/live_vs_rh2_00600_pkt000002_compare.txt
logs/source_state_compare/receiver_stub_3pkt_20260524.out
logs/source_state_compare/slurm_7641623_stub3cmp.out
logs/source_state_compare/wxsami3_live_meta_stub3cmp.json
```

Large binary live dump files are not committed.

## Current Conclusion

The f19 live WACCM-X -> SAMI3 sender is now validated for:

```text
CAM runtime phys_state(:) extraction
f19 live runtime-map payload construction
three-packet online MPI send path
rank 1..32 worker payload delivery
rank 0..32 done-tag delivery
file-mode fallback regression
```

It is still not production live WACCM-X neutral forcing because the following
physics and semantics items remain open:

```text
same-call-site source-state diagnostic, independent of later CAM history phase
explicit WACCM-X-top blending/fallback policy
hard N2 residual closure QC and negative-residual handling
He native/MSIS fallback validation
W/vertical-wind policy validation
REMIX -> SAMI3 potential/E-field forcing
SAMI3 -> RAIJU/GAMERA flux-tube weighting and L/MLT mapping
```

## Recommended Next Step

Do not keep extending SAMI3 physics just to receive diagnostic packets.  Keep
the two-packet full SAMI3 online smoke as the current physics-coupled
transport test.

For source-state validation, either:

```text
1. add a same-call-site NetCDF/HDF5 diagnostic writer at the current cam_run2
   hook, or
2. duplicate/move a diagnostic-only hook to the history-write-equivalent phase
   if the objective is strict history-file equality.
```

For the coupling roadmap, the next implementation step should be the physical
QC layer around the current live payload:

```text
top blending and source flags
N2 residual closure checks
He native fallback audit
W disabled/diagnostic policy
metadata schema tightening for top-level pressure fields
```
