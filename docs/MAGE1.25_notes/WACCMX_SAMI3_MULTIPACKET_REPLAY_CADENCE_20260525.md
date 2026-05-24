# WACCM-X/SAMI3 Multipacket Replay Cadence Gate

Date: 2026-05-25

## Scope

This adds a small validator for archived replay-compare artifacts from
multi-packet WACCM-X -> SAMI3 tests:

```text
scripts/validate_wxsami3_replay_cadence.py
```

It is intentionally narrower than the current full live packet contract.  Older
multi-packet artifacts do not contain the newest source-flag metadata or full
sender/receiver logs, but they still carry enough replay compare evidence to
validate packet order, cadence, worker count, and replay-vs-receiver numerical
agreement.

## Checks

The validator checks:

```text
live_dump_summary_pktNNNNNN.txt exists
replay_builder_pktNNNNNN.out exists
recv_qc_compare_pktNNNNNN.txt exists
compare ok marker is present
occurrence matches packet index
rank count matches expected worker count
each packet has one step and one packet hour
steps are monotonic
packet hours are monotonic
optional packet-hour cadence
max_rel is below tolerance
```

## Validation Result

Existing two-packet f19 replay artifact:

```text
run = logs/multipacket_20260524
expected_packets = 2
expected_ranks = 32
packet0 step = 0
packet0 hour = 0.0
packet0 max_rel = 4.86991e-13
packet1 step = 1
packet1 hour = 0.0833333358
packet1 max_rel = 6.80359e-13
cadence_hours = 0.0833333358
overall = ok
```

## Evidence

Archived under:

```text
logs/waccmx_live_multipacket_cadence_validation_20260525/
```

including:

```text
multipacket_replay_cadence.txt
multipacket_replay_cadence.json
```
