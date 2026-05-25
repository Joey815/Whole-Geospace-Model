# WACCM-X/SAMI3 Live Direct-MPI No-Smoke 12 Packet / 12 Phi Result

Date: 2026-05-26 CST

This run extends the validated f19 WACCM-X/CAM live-neutral plus Voltron/REMIX
direct-phi online MPI cadence test from six five-minute cadences to twelve.

## Result

```text
jobid = 7680171
jobname = wxsami3_12p12f_h4
state = COMPLETED
exit = 0:0
elapsed = 00:48:27
node = qhcn343
MaxRSS = 65270560K
archive = logs/waccmx_live_directmpi_nosmoke_dt300_12pkt_12phi_hrmax4_20260526/
source_run = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_12pkt_12phi_hrmax4_maxstep1400_20260526_0000
```

All archived validators returned `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_runtime_map
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
```

## Runtime Settings

```text
SAMI3_MAXSTEP = 1400
SAMI3_HRMAX = 4.000000
SAMI3_DT0 = 300.
SAMI3_NEUTRAL_UPDATE_HOURS = 0.08333333333333333
SAMI3_NEUTRAL_SPAN_HOURS = 0.08333333333333333
VOLTRON_TFIN = 80.25
VOLTRON_DTCOUPLE = 5.0
VOLTRON_TIMEOUT_SECONDS = 2400
ALLOW_VOLTRON_TIMEOUT_AFTER_DONE = 1
PHI_MAX_FRAMES = 12
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_VALID_HOURS = 0.08333333333333333
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
PHI_STOP_AFTER_DONE = 0
MAX_PACKETS = 12
LIVE_DUMP_MAX = 12
SEND_EVERY_NSTEPS = 1
CESM_STOP_N = 3900
```

## Positive Evidence

SAMI3 received all twelve neutral packet hours on all 32 workers:

```text
0  0.00000000
1  8.33333358E-02
2  0.166666672
3  0.250000000
4  0.333333343
5  0.416666657
6  0.500000000
7  0.583333313
8  0.666666687
9  0.750000000
10 0.833333313
11 0.916666687
```

SAMI3 received all twelve direct-phi frames:

```text
phi_recv_frame_count = 12
phi_recv_frame_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
phi_sender_sent_frames = 12
```

The direct-phi payload contained twelve finite, changing frames:

```text
header = [20260524, 1, 125, 97, 12]
hours = [0.0, 0.0833333358, 0.1666666716, 0.25, 0.3333333433,
         0.4166666567, 0.5, 0.5833333135, 0.6666666865,
         0.75, 0.8333333135, 0.9166666865]
frame_change_max_abs = 3.4961066246032715
```

Replay/QC comparisons were generated for all twelve live dumps.  The worst
archived relative mismatch is still roundoff-level:

```text
recv_qc_compare_pkt000000 max_rel = 4.83248e-13
recv_qc_compare_pkt000001 max_rel = 6.76502e-13
recv_qc_compare_pkt000010 max_rel = 1.12426e-12
recv_qc_compare_pkt000011 max_rel = 1.12911e-12
limit = 1e-6
```

The live packet contract confirms this is CAM runtime state, not file-backed
neutral forcing:

```text
meta_runtime_source = CAM phys_state(:)
meta_actual_transport = runtime_live_packet
meta_payload_version = wxsami3-live-payload-v2
meta_last_packet_index = 11
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
```

The runtime map gate still validates the f19 source geometry:

```text
nsource = 13824
npoints = 3618816
weights_dim_n_a = 13824
weights_dim_n_b = 3618816
weights_dim_n_s = 14475264
```

## Absorbed Diagnostic Attempt

The immediately preceding 12pkt/12phi attempt used `SAMI3_MAXSTEP=800` and
`SAMI3_HRMAX=3.000000`:

```text
jobid = 7680009
state = CANCELLED by 3446
elapsed = 00:37:57
phi_recv = 10
phi_sent = 12
rank0000_pkt = 11
last received phi frame = 9, valid until 0.833333313 h
MASTER: All Done!
```

That attempt showed that Voltron could produce all twelve frames, but SAMI3
terminated before consuming frames 10 and 11.  The successful run therefore
raised both `MAXSTEP` and `HRMAX`.

## Interpretation

This promotes the f19 WACCM-X/CAM -> SAMI3 online control path to a validated
twelve-cadence prototype:

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
The near-term WACCM-X/SAMI3 path is now stable enough for longer cadence tests,
but production physics still needs reviewed top-blend policy, He/W policy,
restart/cadence behavior, and eventual f09 or distributed remap planning.

## Next Target

Keep this 12pkt/12phi f19 run as the current WACCM-X/SAMI3 online-control
baseline.  The next implementation target should return to the SAMI3 ->
Voltron/RAIJU/GAMERA scalar-moment adapter:

```text
1. Keep the WACCM-X/SAMI3 f19 12-cadence result as the validated control path.
2. Continue SAMI3 -> RAIJU around Pavg/Davg/Pstd/Dstd/tiote.
3. Resolve the current source-domain L policy before claiming production
   plasma feedback.
4. Preserve alpha/blending and no-overwrite controls for runtime safety.
```
