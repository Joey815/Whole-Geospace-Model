# WACCM-X/SAMI3 Live Neutral + Direct Voltron Phi Result - 2026-05-25

## Result

The first same-stack online smoke combining live WACCM-X/CESM neutral extraction
with direct OpenMPI Voltron -> SAMI3 phi handoff completed:

```text
jobid = 7668385
jobname = wxsami3_dmpi
state = COMPLETED
exit = 0:0
elapsed = 00:07:10
node = qhcn005
batch MaxRSS = 63585144K
archive = logs/waccmx_live_directmpi_20260525/
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
```

This is the first completed job where:

```text
CESM/WACCM-X sends live neutral forcing from CAM phys_state(:)
CESM/WACCM-X does not send file-backed phi payload frames
OpenMPI voltron.x sends REMIX phi frames directly to the SAMI3 phi MPI port
SAMI3 receives both the live neutral packet and direct phi frames
```

## Runtime Chain

The job used one OpenMPI/PRTE DVM:

```text
33 SAMI3 ranks
16 CESM/WACCM-X ranks
1 OpenMPI-enabled serial voltron.x rank
```

CESM/WACCM-X sender:

```text
WXSAMI3 phi payload enabled: F
WXSAMI3 sent live neutral packet: nstep=0 packet_hour=0 count=0
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

Voltron direct phi sender:

```text
WACCMX_SAMI3_PHI_DIRECT connected
WACCMX_SAMI3_PHI_DIRECT sent frame=0 nframes=2 hour=0 valid_until=0.0013888889
WACCMX_SAMI3_PHI_DIRECT sent frame=1 nframes=2 hour=0.0013888889 valid_until=1.0e30
WACCMX_SAMI3_PHI_DIRECT sent done=2
WACCMX_SAMI3_PHI_DIRECT stop after done requested
```

SAMI3 receiver:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
WACCMX_PHI_RECV frame 0 of 2, min/max = -36.9728775, 31.5048161
WACCMX_PHI_RECV frame 1 of 2, min/max = -37.7063637, 31.7590370
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

## Validation

All standard validators passed:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

Neutral replay/QC:

```text
WACCMX_RECV_QC compare ok:
  ranks = 32
  occurrence = 0
  step_set = [0]
  packet_hour_set = [0.0]
  max_abs = 2.08794e+06
  max_rel = 4.83248e-13
```

Phi payload contract:

```text
size = 97044 bytes
header = [20260524, 1, 125, 97, 2]
frame 0 hour = 0
frame 1 hour = 0.0013888889
frame1_minus_frame0_max_abs = 3.4961066
frame1_minus_frame0_rms = 0.62902843
```

Live neutral contract highlights:

```text
source_columns = 13824
receiver workers = 32
source flags valid = 4211765
source flags invalid = 1819595
above live top = 1641376
N2 residual negative = 178219
unknown invalid = 0
top blend bottom/top = 600/720 km
blend_i + blend_f = 2708
```

## Interpretation

This closes the current online control-path milestone:

```text
WACCM-X/CESM live neutral from phys_state(:)
REMIX/Voltron runtime phi through direct MPI
SAMI3 online neutral + direct phi receiver
validated source flags, top-blend policy, time-axis consistency, and runtime map
```

It is still a prototype physics coupling.  The short smoke uses:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 1
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 1
```

Those switches allow the two-frame test to finalize after the final direct phi
frame.  Production coupling still needs a real cadence policy for continued
REMIX/SAMI3 potential updates, plus the outstanding physical upgrades:

```text
f09/distributed live neutral remap
production top-blend and fallback policy
REMIX/SAMI3 multi-cycle time synchronization
SAMI3 -> RAIJU/GAMERA traced flux-tube weighting and L/MLT mapping
runtime blending/floors for scalar moments
```
