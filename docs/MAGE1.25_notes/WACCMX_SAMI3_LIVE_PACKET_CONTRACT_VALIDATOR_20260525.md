# WACCM-X -> SAMI3 Live Packet Contract Validator

Date: 2026-05-25

## Scope

This checkpoint adds a validator for the same-call-site live neutral packet
contract.  It does not use later CAM history time means as the source of truth.
Instead, it checks this runtime chain:

```text
CAM phys_state(:) live dump
-> offline replay payload generated from that live dump
-> SAMI3 receiver WACCMX_RECV_QC lines
```

If the replay comparison passes, the SAMI3 receiver packet can be reconstructed
from the live dump written by the sender at the same call site.

## Validator

New script:

```text
scripts/validate_wxsami3_live_packet_contract.py
```

The validator checks:

```text
wxsami3_live_meta.json payload_version/runtime_source/transport
payload header magic/nz/nf/nl/nneut
runtime_map source column count
source units and payload units
density conversion string
source species order and payload species order
source flag MPI tag and values
CAM constituent indices for O/O2/H/N/NO
N2 residual and He native index policy
fallback policy contract
N2 negative residual mode
source flag count closure
sender checksum count closure
per-packet live_dump_summary files
per-packet live-dump field bad-count and range checks
per-packet replay_builder outputs
per-packet recv_qc_compare outputs
SAMI3 receiver completion marker
WACCM-X sender completion marker
fatal marker absence
```

Default f19 source geometry:

```text
expected_source_columns = 144 * 96 = 13824
expected_payload_header = magic=20260522, nz=304, nf=124, nl=5, nneut=7
expected_receiver_ranks = 32
expected_n2_mode = invalid
max_qc_rel = 1e-6
```

The validator accepts both `slurm-*.out` and older archived `slurm_*.out`
names when collecting sender-side markers.

## Validation Runs

One-packet Voltron phi two-frame runtime:

```text
python3 scripts/validate_wxsami3_live_packet_contract.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_2frame_20260525_0000 \
  --expected-packets 1 \
  --json-output logs/waccmx_live_packet_contract_20260525/voltron_phi_2frame_contract.json
```

Result:

```text
packet0_summary_source_columns = 13824
packet0_replay_source_coverage = source_cols=13824 filled=13824
packet0_replay_n2_mode = invalid
packet0_replay_bad_weighted_z = 0
packet0_recv_compare_ranks = 32
packet0_recv_compare_occurrence = 0
packet0_recv_compare_max_rel = 4.83248e-13
sender_live_packet_count = 1
receiver_qc_line_count >= 32
sami3_done = true
waccmx_done = true
overall = ok
```

Two-packet top-blend runtime:

```text
python3 scripts/validate_wxsami3_live_packet_contract.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_multipacket_topblend_20260524_0000 \
  --expected-packets 2 \
  --json-output logs/waccmx_live_packet_contract_20260525/topblend_2packet_contract.json
```

Result:

```text
packet0_recv_compare_max_rel = 4.83248e-13
packet1_recv_compare_max_rel = 6.76502e-13
packet0_replay_bad_weighted_z = 0
packet1_replay_bad_weighted_z = 0
sender_live_packet_count = 2
receiver_qc_line_count >= 64
sami3_done = true
waccmx_done = true
overall = ok
```

The metadata/schema-expanded validator was rerun on the archived top-blend
evidence and now also confirms:

```text
source_units = T K, wind m/s, pressure Pa, height m, composition mass_mixing_ratio
payload_units = density cm^-3, temperature K, wind cm/s
source_species_order = O,O2,H,N,NO,N2,He
payload_species_order = H,O,NO,O2,He,N2,N
source_flag_mpi_tag = 212
source_flag_values = 1/2/3/4 for valid/above_top/N2_invalid/other_invalid
CAM constituent indices O=57, O2=58, H=37, N=51, NO=54
N2 index = -1 residual policy
He index = -1 native/MSIS policy
overall = ok
```

The field-stat gate now also checks the live dump itself before replay:

```text
cid missing = 0
cid unique = 13824
lat/lon bad = 0 and ranges within [-90,90] / [0,360]
T_K bad = 0 and range within [50,5000] K
U_m_s/V_m_s bad = 0 and ranges within +/-5000 m/s
PMID_Pa bad = 0 and range within (0,2e5] Pa
ZM_m bad = 0 and range within [-1e3,2e6] m
MBARV_kg_mol bad = 0 and range within [1,60]
q_O/q_O2/q_H/q_N/q_NO bad = 0 and ranges within [-1e-12,1.1]
```

N2 and He are intentionally not required to be finite in the live dump summary
because the current f19 physical prototype uses residual N2 and native/MSIS He
fallbacks.

## Use On Append2 Runs

The queued full append2 and direct-wait jobs use:

```text
WXSAMI3_LIVE_DUMP_MAX=1
WXSAMI3_MAX_PACKETS=1
```

After either run completes, run:

```text
python3 scripts/validate_wxsami3_live_packet_contract.py \
  --run-dir <append2-or-directwait-run-dir> \
  --expected-packets 1 \
  --json-output <run-dir>/live_packet_contract.json
```

This should be run in addition to:

```text
python3 scripts/validate_wxsami3_append2_run.py \
  --run-dir <append2-or-directwait-run-dir> \
  --expected-phi-frames 2
```

For the direct-wait launcher, add:

```text
--expect-phi-wait-marker
```

## Interpretation

This closes a validation gap in the live neutral path.  The earlier CAM history
comparison remains useful as a phase diagnostic, but it is not a strict
source-state equality test because history output may be written at a different
model phase and may carry time-mean semantics.

The current live packet contract validator proves the packet delivered to SAMI3
can be regenerated from the sender's same-call-site live dump with receiver QC
agreement at roughly 1e-12 relative error, and that the live neutral fields used
for that replay have finite, plausible runtime ranges.

This does not make the full system production coupling yet.  Remaining neutral
path blockers include the production top-blend policy, He fallback hardening,
W/vertical-wind policy validation, and f09/finer distributed remap design.

## Evidence

Archived under:

```text
logs/waccmx_live_packet_contract_20260525/
logs/waccmx_live_meta_contract_20260525/
```

including text and JSON validator outputs for both checked runs.
