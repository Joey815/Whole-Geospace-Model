# WACCM-X -> SAMI3 N2 Invalid-Mode Result (2026-05-24)

This note records the `WXSAMI3_N2_NEGATIVE_MODE=invalid` receiver-stub
validation and the direct comparison against the prior `floor` baseline.

## Objective

The previous `floor` mode preserved smoke-test behavior by flooring negative
residual N2 to `1e-20`.  The next physical-QC candidate is `invalid`, where a
sample with negative residual N2 is marked invalid so the SAMI3 receiver keeps
its native/MSIS/HWM neutral state for that sample.

The validation goal was narrow:

```text
Keep the same f19 receiver-stub 3-packet setup.
Change only WXSAMI3_N2_NEGATIVE_MODE from floor to invalid.
Check transport, done tag, metadata, and QC deltas.
```

## Run

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_n2qc_invalid_20260524.sbatch
```

Local run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_n2qc_invalid_20260524_0000
```

Job:

```text
job id: 7641644
state: COMPLETED
exit: 0:0
elapsed: 00:02:12
node: qhcn078
```

Runtime setting:

```text
WXSAMI3_N2_NEGATIVE_MODE=invalid
```

Sender markers:

```text
WXSAMI3 N2 negative residual mode: invalid
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

## Floor vs Invalid

Packet 2 metadata comparison:

```text
metric                                floor                 invalid               delta
runtime_qc.invalid                    1642906               1819998               +177092
runtime_qc.above_live_top             1642906               1642906               0
runtime_qc.n2_residual_used           4388454               4388454               0
runtime_qc.n2_residual_negative       177092                177092                0
sender_checksum.valid_i               4388454               4211362               -177092
sender_checksum.invalid_i             1642906               1819998               +177092
```

This is the expected behavior: `invalid` mode moves exactly the negative
residual N2 samples into the invalid/native-fallback path.  The above-live-top
count is unchanged, so the new invalid samples are specifically from N2
closure, not from the vertical coverage fallback.

Checksum changes:

```text
sum_denni delta = -1.461390819328e12
sum_tni   delta = -1.9934078738031006e8
sum_ui    delta =  3.31689163539124e8
sum_vi    delta = -5.472385718509989e8
```

These deltas are expected because invalid samples carry sentinel/default
payload values and are intended to trigger SAMI3-native fallback.

## Interpretation

`invalid` mode is transport-stable in the receiver-stub path:

```text
3 packets delivered to worker ranks 1..32
done tag delivered to ranks 0..32
no sender abort
no receiver abort
```

For physical prototype work, `invalid` is a better default than `floor` because
it does not invent a small positive N2 where the major-species residual is
negative.  The cost is that more SAMI3-grid samples are left to native/MSIS/HWM
neutral state.

Recommended mode split:

```text
floor   = communication smoke and backward-compatible regression
invalid = physical prototype default
fail    = strict composition-closure debugging
```

## Artifacts Included In This Repo

```text
logs/n2_qc_invalid_20260524/wxsami3_live_meta.json
logs/n2_qc_invalid_20260524/wxsami3_physstate_meta.json
logs/n2_qc_invalid_20260524/slurm_7641644_n2qc_invalid.out
logs/n2_qc_invalid_20260524/receiver_stub_7641644.out
logs/n2_qc_invalid_20260524/floor_vs_invalid_compare.txt
```

Large binary live dump files are not committed.

## Next Step

The next implementation target should be explicit source/fallback flags for
the live neutral payload:

```text
WACCMX_VALID
SAMI3_NATIVE_ABOVE_TOP
SAMI3_NATIVE_N2_INVALID
SAMI3_NATIVE_HE
SAMI3_NATIVE_W
```

This should first be represented in metadata and receiver-stub QC, then wired
into the SAMI3 receiver so post-run diagnostics can distinguish top fallback
from composition-closure fallback.
