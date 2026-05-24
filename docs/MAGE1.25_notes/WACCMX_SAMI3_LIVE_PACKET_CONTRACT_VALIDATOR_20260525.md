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
runtime_map source column count
source unit and fallback policy contract
N2 negative residual mode
source flag count closure
sender checksum count closure
per-packet live_dump_summary files
per-packet replay_builder outputs
per-packet recv_qc_compare outputs
SAMI3 receiver completion marker
WACCM-X sender completion marker
fatal marker absence
```

Default f19 source geometry:

```text
expected_source_columns = 144 * 96 = 13824
expected_receiver_ranks = 32
expected_n2_mode = invalid
max_qc_rel = 1e-6
```

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
agreement at roughly 1e-12 relative error.

This does not make the full system production coupling yet.  Remaining neutral
path blockers include the production top-blend policy, He fallback hardening,
W/vertical-wind policy validation, and f09/finer distributed remap design.

## Evidence

Archived under:

```text
logs/waccmx_live_packet_contract_20260525/
```

including text and JSON validator outputs for both checked runs.
