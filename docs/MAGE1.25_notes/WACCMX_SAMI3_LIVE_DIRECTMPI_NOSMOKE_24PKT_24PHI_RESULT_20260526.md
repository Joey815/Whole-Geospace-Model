# WACCM-X/SAMI3 Live Direct-MPI No-Smoke 24 Packet / 24 Phi Result

Date: 2026-05-26 CST

This run extends the validated f19 WACCM-X/CAM live-neutral plus Voltron/REMIX
direct-phi online MPI cadence test from twelve five-minute cadences to
twenty-four.

## Result

```text
jobid = 7697673
jobname = wxsami3_24p24f_h8
state = COMPLETED
exit = 0:0
elapsed = 01:08:04
node = qhcn198
batch MaxRSS = 65297928K
archive = logs/waccmx_live_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_20260526/
source_run = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_maxstep2800_20260526_0000
```

The archive driver returned `ok=true`.  All seven archived validators returned
`overall=ok`:

```text
validate_sami3_direct_phi_run_strict
validate_remix_sami3_phi_payload
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

## Runtime Settings

```text
SAMI3_MAXSTEP = 2800
SAMI3_HRMAX = 8.000000
SAMI3_DT0 = 300.
SAMI3_NEUTRAL_UPDATE_HOURS = 0.08333333333333333
SAMI3_NEUTRAL_SPAN_HOURS = 0.08333333333333333
VOLTRON_TFIN = 155.25
VOLTRON_DTCOUPLE = 5.0
VOLTRON_TIMEOUT_SECONDS = 7200
COMPONENT_TIMEOUT_SECONDS = 7200
PHI_MAX_FRAMES = 24
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_VALID_HOURS = 0.08333333333333333
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
PHI_STOP_AFTER_DONE = 0
MAX_PACKETS = 24
LIVE_DUMP_MAX = 24
CESM_STOP_N = 7500
```

## Positive Evidence

SAMI3 received all twenty-four neutral packet hours on all 32 workers:

```text
packet_count = 24
worker_coverage = 32 workers for every packet
hours = [0.0, 0.0833333358, 0.166666672, 0.25, 0.333333343,
         0.416666657, 0.5, 0.583333313, 0.666666687, 0.75,
         0.833333313, 0.916666687, 1.0, 1.08333337,
         1.16666663, 1.25, 1.33333337, 1.41666663, 1.5,
         1.58333337, 1.66666663, 1.75, 1.83333337, 1.91666663]
```

SAMI3 received all twenty-four direct-phi frames:

```text
phi_recv_frame_count = 24
phi_recv_frame_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                          12, 13, 14, 15, 16, 17, 18, 19, 20,
                          21, 22, 23]
phi_sender_sent_frames = 24
phi_sender_sent_done = true
```

The direct-phi payload contained twenty-four finite, changing frames:

```text
payload_header = [20260524, 1, 125, 97, 24]
payload_size = 1164308
frame_change_max_abs = 3.4961066
frame23_minus_frame22_max_abs = 0.74923463
last_valid_until = 1e30
```

Replay/QC comparisons were generated for all twenty-four live dumps.  The last
packet remains at roundoff-level mismatch:

```text
recv_qc_compare_pkt000023 max_rel = 1.20189e-12
limit = 1e-6
```

The live packet contract confirms this is CAM runtime state, not file-backed
neutral forcing:

```text
meta_runtime_source = CAM phys_state(:)
meta_actual_transport = runtime_live_packet
meta_payload_version = wxsami3-live-payload-v2
meta_last_packet_index = 23
meta_last_packet_hour = 1.91666663
meta_source_species_order = ['O', 'O2', 'H', 'N', 'NO', 'N2', 'He']
meta_payload_species_order = ['H', 'O', 'NO', 'O2', 'He', 'N2', 'N']
```

The source/top-blend policy remained explicit and internally balanced:

```text
topblend_mode = linear
bottom_km = 600
top_km = 720
unknown_source_flags = 0
he_native_matches_valid = true
w_zero_matches_valid = true
blend_cells_min = 1244
```

The runtime map gate still validates the f19 source geometry:

```text
nsource = 13824
npoints = 3618816
weights_dim_n_a = 13824
weights_dim_n_b = 3618816
weights_dim_n_s = 14475264
```

## Run-Management Caveat

The model chain reached all done markers before the Slurm batch exited:

```text
WACCMX_SAMI3_PHI_DIRECT sent done=24
MASTER: All Done!
END OF MODEL RUN
```

Voltron remained inside the `timeout 7200s prun ... ./voltron.x` wrapper after
the direct-phi done marker because this run used `PHI_STOP_AFTER_DONE=0`.
The wrapper was terminated after the done markers were verified.  The launcher
accepted this as:

```text
INFO: accepting Voltron nonzero exit after direct phi done and SAMI3 completion: status=143
```

This is a run-management caveat, not a physics-chain failure.  Future long
cadence runs should either use a shorter post-done Voltron timeout, validate
`PHI_STOP_AFTER_DONE=1` for this mode, or add explicit post-done wrapper
termination.

## Archive Tooling Fix

Post-run archive revalidation exposed one tooling issue: the live-packet
contract validator used to include `slurm-*.out` by default.  After a completed
Slurm script prints validator excerpts, that can duplicate sender packet lines
and match validator text as fatal markers.  The validator now supports:

```text
--exclude-slurm-logs
```

The direct-MPI archive driver uses that option for post-run contract
revalidation and stores original run-directory validator outputs under:

```text
logs/waccmx_live_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_20260526/run_validators/
```

## Interpretation

This promotes the f19 WACCM-X/CAM -> SAMI3 online control path to a validated
twenty-four-cadence prototype:

```text
CAM phys_state(:)
  -> live WACCM-X neutral packet, f19 144 x 96 source grid
  -> SAMI3 receiver and 32-worker distribution
  -> top-blend/source-flag policy
  -> REMIX/Voltron direct-MPI phi frames
  -> SAMI3 done/finalize path
  -> replay/QC and strict validators
```

This is still prototype coupling, not production live WACCM-X neutral forcing.
The online control path is no longer the main blocker at f19 cadence scale.
The remaining production work is reviewed top-blend/He/W policy, restart and
longer-cadence stability, f09 or distributed remap planning, live REMIX
producer integration without replayed payload staging, and the SAMI3 ->
Voltron/RAIJU/GAMERA physical source-domain decision.

## Next Target

Use this 24pkt/24phi f19 run as the current WACCM-X/SAMI3 online-control
baseline.  The next implementation target should return to the SAMI3 ->
Voltron/RAIJU/GAMERA scalar-moment adapter:

```text
1. Keep the WACCM-X/SAMI3 f19 24-cadence result as the validated control path.
2. Continue SAMI3 -> RAIJU around Pavg/Davg/Pstd/Dstd/tiote.
3. Resolve source-domain L coverage before claiming production plasma feedback.
4. Preserve alpha/blending and no-overwrite controls for runtime safety.
```
