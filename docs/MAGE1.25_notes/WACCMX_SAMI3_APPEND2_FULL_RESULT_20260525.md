# WACCM-X -> SAMI3 Append2 Full Integration Result

Date: 2026-05-25

## Scope

This is the first completed f19 WACCM-X/CESM -> SAMI3 online run in the current
goal-mode batch with both live neutral payload extraction and generated
Voltron/REMIX phi append enabled.

Runtime path:

```text
WACCM-X/CAM phys_state(:)
  -> live neutral payload metadata/source flags/runtime map
  -> SAMI3 online neutral receiver
Voltron/REMIX phi writer
  -> two-frame phi_weimer payload
  -> WACCM-X sender append
  -> SAMI3 online phi receiver
```

This remains a validated prototype.  It verifies online communication,
runtime payload semantics, and receiver-side consistency; it is not yet final
production WACCM-X neutral forcing or final traced-tube MAGE plasma coupling.

## Run Result

Slurm job:

```text
jobid = 7659727
jobname = wxsami3_ap2
state = COMPLETED
exit = 0:0
elapsed = 00:05:18
node = qhcn332
batch MaxRSS = 60176444K
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525_0000
```

Archive:

```text
logs/waccmx_append2_full_20260525/
```

Archive gate:

```text
ok = true
validate_wxsami3_append2_run = 0
validate_remix_sami3_phi_payload = 0
validate_wxsami3_time_axis = 0
validate_wxsami3_live_packet_contract = 0
validate_wxsami3_topblend_policy = 0
validate_wxsami3_runtime_map = 0
```

## Online Phi Gate

The generated phi payload passed the independent binary contract:

```text
header = [20260524, 1, 125, 97, 2]
exact_size = 97044 bytes
nframes = 2
frame_hours = [0.0, 0.0013888889225199819]
valid_until = [0.0013888889225199819, 1.0000000150474662e+30]
finite_counts = [12125, 12125]
nonzero_counts = [3492, 3492]
frame1_minus_frame0_max_abs = 3.5858945846557617
```

The online append receiver gate also passed:

```text
sender_phi_frame_markers = 2
receiver_phi_records = 2
receiver_phi_values_match_payload = matched 2 of 2
receiver_phi_markers = 4
receiver_done = MASTER: All Done!
sender_done = END OF MODEL RUN
neutral_replay_qc markers = 2
fatal marker matches = 0
```

## Time-Axis Gate

The neutral and phi timelines are internally consistent:

```text
sender_neutral_packets = 1
receiver_neutral_packets = 1
receiver_worker_coverage = 32
sender_hours = [0.0]
receiver_hours = [0.0]
phi_payload_frame_count = 2
phi_payload_hours_strictly_increasing = true
phi_payload_valid_until_links = true
phi_payload_covers_neutral_packets = true
receiver_phi_records_within_validity = true
```

## Live Payload Contract

The live packet metadata records:

```text
payload_version = wxsami3-live-payload-v2
runtime_source = CAM phys_state(:)
actual_transport = runtime_live_packet
dtime_phys_s = 300
send_every_nsteps = 1
packet_hour = 0.0
runtime_map_source_columns = 13824
runtime_map_npoints = 3618816
source_species_order = O, O2, H, N, NO, N2, He
payload_species_order = H, O, NO, O2, He, N2, N
```

Fallback accounting closed exactly:

```text
flag_total = 6031360
WACCMX_VALID = 4211765
invalid_total = 1819595
above_live_top = 1641376
n2_residual_negative = 178219
other_invalid = 0
valid_i = valid_f = source_valid = 4211765
invalid_i = invalid_f = runtime_invalid = 1819595
```

The live-dump range and replay checks also passed:

```text
source_columns = 13824
cid_coverage = 13824
lat range = -90.0 to 90.0 deg
lon range = 0.0 to 357.5 deg
T range = 113.19272490765026 to 1522.7628810979916 K
U range = -925.7242161594645 to 769.7344197674036 m/s
V range = -845.8062460574145 to 736.3650929706123 m/s
PMID range = 4.055140885992663e-08 to 107321.3890267048 Pa
ZM range = 48.56266690499009 to 720507.7580399793 m
MBARV range = 14.895337165442252 to 28.874522993878628 kg/mol
recv_compare_ranks = 32
recv_compare_max_rel = 4.83248e-13
```

## Top-Blend and Runtime Map Gates

The SAMI3 receiver logged the expected top-blend policy:

```text
mode = linear
blend_bottom_km = 600.0
blend_top_km = 720.0
apply_blend_line_count = 279
blend_cell_total = 5316
source_unknown_total = 0
He native fallback matches valid cells
W zero policy matches valid cells
```

The runtime map product matched the f19 ESMF weights:

```text
runtime_map = wxsami3_runtime_map_f19_20260523.bin
header_npoints = 3618816
header_nsource = 13824
runtime_map_size = 217128992
row_count_sum = 14475264
weights_nc n_a = 13824
weights_nc n_b = 3618816
weights_nc n_s = 14475264
uncovered rows = 0
```

## Interpretation

This completes the current append2 full-integration gate: WACCM-X produced a
runtime live neutral packet from `phys_state(:)`, the generated Voltron/REMIX
phi payload was appended and received by SAMI3, source-flag/fallback accounting
closed, replay matched the receiver at numerical roundoff, and both WACCM-X and
SAMI3 reached clean shutdown.

The next online-control gate is the direct-wait variant, where the same job
must prove that the phi producer/waiter path is active rather than consuming a
fully pre-generated payload before the online run begins.

## Evidence

Archived under:

```text
logs/waccmx_append2_full_20260525/
```

including Slurm output, CESM/WACCM-X output, SAMI3 receiver output, phi summary,
live metadata, replay/QC summaries, `sacct_7659727.txt`, and all validator JSON
and text reports.  Large binary live payload files, restart files, NetCDF
products, and SAMI3 large state outputs remain only in the local run directory.
