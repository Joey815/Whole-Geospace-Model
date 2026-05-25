# WACCM-X/SAMI3 Live Direct-MPI No-Smoke 6 Packet / 6 Phi Result

Date: 2026-05-26 CST

This run is the first validated f19 WACCM-X/CAM live-neutral plus Voltron/REMIX
direct-phi online MPI cadence test with six neutral packets and six phi frames.

## Result

```text
jobid = 7678504
jobname = wxsami3_6p6f_h2
state = COMPLETED
exit = 0:0
elapsed = 00:25:56
node = qhcn657
MaxRSS = 64984360K
archive = logs/waccmx_live_directmpi_nosmoke_dt300_6pkt_6phi_hrmax2_20260526/
source_run = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_6pkt_6phi_hrmax2_maxstep400_20260526_0000
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
SAMI3_MAXSTEP = 400
SAMI3_HRMAX = 2.000000
SAMI3_DT0 = 300.
SAMI3_NEUTRAL_UPDATE_HOURS = 0.08333333333333333
SAMI3_NEUTRAL_SPAN_HOURS = 0.08333333333333333
PHI_MAX_FRAMES = 6
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_VALID_HOURS = 0.08333333333333333
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
MAX_PACKETS = 6
LIVE_DUMP_MAX = 6
SEND_EVERY_NSTEPS = 1
CESM_STOP_N = 2100
```

The successful cadence required increasing `SAMI3_HRMAX`; just increasing
`SAMI3_MAXSTEP` was not enough because `ntmmax` is capped by
`min(maxstep, int((hrmax-hrpr)/dthr)) + 1`.

## Positive Evidence

SAMI3 received all six neutral packet hours:

```text
0 0.00000000
1 8.33333358E-02
2 0.166666672
3 0.250000000
4 0.333333343
5 0.416666657
```

SAMI3 received all six direct-phi frames:

```text
phi_recv_frame_count = 6
phi_recv_frame_indices = [0, 1, 2, 3, 4, 5]
phi_sender_sent_frames = 6
```

The sender and receiver exchanged clean done signals:

```text
WACCMX online done signal received: 6
SAMI3 direct phi done signal received: 6
done finalizing,taskid 0..32
```

The live packet contract confirms this is CAM runtime state, not file-backed
neutral forcing:

```text
meta_runtime_source = CAM phys_state(:)
meta_actual_transport = runtime_live_packet
meta_last_packet_index = 5
meta_payload_version = wxsami3-live-payload-v2
```

The direct-phi payload contained six finite, changing frames:

```text
header = [20260524, 1, 125, 97, 6]
hours = [0.0, 0.0833333358, 0.1666666716, 0.25, 0.3333333433, 0.4166666567]
frame_change_max_abs = 3.4961066246032715
```

Replay/QC comparisons were generated for all six live dumps:

```text
recv_qc_compare_pkt000000.txt
recv_qc_compare_pkt000001.txt
recv_qc_compare_pkt000002.txt
recv_qc_compare_pkt000003.txt
recv_qc_compare_pkt000004.txt
recv_qc_compare_pkt000005.txt
```

## Failed Parameter Attempts Absorbed

The successful setting followed several intentionally cancelled attempts:

```text
7678173: MAXSTEP=6, HRMAX=.700000
  SAMI3 consumed only packet hours 0, 0.0833333, 0.1666667.

7678321: MAXSTEP=12, HRMAX=.700000
  Same three-packet limit.

7678363: MAXSTEP=60, HRMAX=.700000
  Same three-packet limit.

7678434: MAXSTEP=180, HRMAX=.700000
  Reached packet hour 0.25 but stopped before 0.3333333 and 0.4166667.
```

The issue was not simply `MAXSTEP`; `HRMAX=.700000` produced an effective
`ntmmax=42`, too short for the desired six 5-minute coupling packets. The
validated setting uses `HRMAX=2.000000`, which gives enough SAMI3 output/update
slots for the six-packet cadence.

## Interpretation

This promotes the f19 WACCM-X/CAM -> SAMI3 online MPI path from a short
three-packet proof to a validated six-cadence no-smoke prototype:

```text
CAM phys_state(:)
  -> live WACCM-X neutral packet, f19 144 x 96 source grid
  -> SAMI3 receiver and worker distribution
  -> top-blend/source-flag policy
  -> REMIX/Voltron direct-MPI phi frames
  -> SAMI3 done/finalize path
```

This is still a prototype, not production live forcing. Remaining blockers are
longer cadence/stability, f09 or distributed remap design, production top-blend
policy, He/W policy review, and the downstream SAMI3 -> RAIJU/GAMERA physical
mapping and weighting path.

## Next Target

Use this validated 6pkt/6phi result as the new WACCM-X/SAMI3 online-control
baseline, then return to the current SAMI3 -> Voltron/RAIJU/GAMERA adapter line:

```text
1. Document current WACCM-X/SAMI3 baseline as validated f19 6pkt/6phi.
2. Keep f19 for near-term integration; defer f09 until the full chain is stable.
3. Resume SAMI3 -> RAIJU scalar moments around the existing Pavg/Davg/Pstd/Dstd/tiote interface.
4. Replace smoke index/mean assumptions with Voltron-consistent weighting and domain policy.
5. Preserve alpha/blending and no-overwrite controls before any physical production claim.
```
