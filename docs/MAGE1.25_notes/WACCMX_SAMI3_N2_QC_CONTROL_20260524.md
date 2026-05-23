# WACCM-X -> SAMI3 N2 Residual QC Control (2026-05-24)

This note records the first P1 QC hardening change after the f19 live sender
and receiver-stub validation.

## Motivation

The f19 live sender derives N2 from residual closure when CAM does not expose a
usable N2 constituent:

```text
q_N2_residual = 1 - q_H - q_O - q_O2 - q_N - q_NO
```

The diagnostic run showed negative residual samples:

```text
packet 0 negative residual samples = 178219
packet 1 negative residual samples = 177900
packet 2 negative residual samples = 177092
```

The old behavior silently floored negative residual N2 to `1e-20`.  That is
acceptable as a smoke-test default, but it must be explicitly controlled for
physical experiments.

## Code Change

Updated file:

```text
code/cesm_source_mods/src.cam/wxsami3_online_stub_mod.F90
```

New runtime control:

```text
WXSAMI3_N2_NEGATIVE_MODE=floor|invalid|fail
```

Modes:

```text
floor
  Default. Preserve previous behavior. Negative residual N2 is floored to
  1e-20 so existing smoke tests and receiver transport remain unchanged.

invalid
  Treat a sample with negative residual N2 as invalid.  The SAMI3 receiver
  then keeps native/MSIS/HWM neutral state for that sample, consistent with
  the above-live-top fallback behavior.

fail
  Abort the CAM sender if residual N2 is negative.  This is useful for strict
  debugging runs where any composition closure violation should stop the case.
```

Metadata updates:

```text
payload metadata now records fallback_policy.N2_negative_mode
diagnostic metadata now records n2_negative_mode
live dump metadata now labels raw physics_state%ps as state_ps_pa_r8
live dump metadata now notes that SAMI3 forcing uses profile PMID_Pa
```

The `state_ps_pa_r8` metadata change does not alter the binary record order;
it only prevents the raw `physics_state%ps` snapshot from being mistaken for
CAM history surface pressure.

## Build Verification

Build command used from the copied case:

```bash
env PATH=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/python311_first:/home/jiaoy_group/jiaoy/data/CESM/experiments/cime_home_v3/bin:/usr/local/bin:/usr/bin:/bin \
  HOME=/home/jiaoy_group/jiaoy/data/CESM/experiments/cime_home_v3 \
  CIME_MODEL=cesm \
  ./case.build --skip-provenance
```

Result:

```text
MODEL BUILD HAS FINISHED SUCCESSFULLY
Total build time: 72.383444 seconds
```

The first build attempt without the Python shim failed because the shell
default Python was 3.6 and CIME requires 3.9+.

## Runtime Verification

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_n2qc_20260524.sbatch
```

Explicit runtime setting:

```text
WXSAMI3_N2_NEGATIVE_MODE=floor
```

Job:

```text
job id: 7641625
state: COMPLETED
exit: 0:0
elapsed: 00:02:13
node: qhcn078
```

Sender markers:

```text
WXSAMI3 N2 negative residual mode: floor
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

Packet-2 metadata:

```text
fallback_policy.N2 = CAM N2 if finite, otherwise residual closure from major species
fallback_policy.N2_negative_mode = floor
runtime_qc.n2_residual_used = 4388454
runtime_qc.n2_residual_negative = 177092
runtime_qc.n2_residual_min = -5.2729643343870897E-02
runtime_qc.n2_residual_max = 8.1303163077207719E-01
```

## Artifacts Included In This Repo

```text
logs/n2_qc_20260524/wxsami3_live_meta.json
logs/n2_qc_20260524/wxsami3_physstate_meta.json
logs/n2_qc_20260524/slurm_7641625_n2qc.out
logs/n2_qc_20260524/receiver_stub_7641625.out
```

Large binary live dump files are not committed.

## Current Interpretation

This change does not make the WACCM-X -> SAMI3 neutral forcing production
ready.  It makes the most risky current composition fallback explicit and
runtime-selectable.

Recommended use:

```text
communication smoke: WXSAMI3_N2_NEGATIVE_MODE=floor
physical prototype:  WXSAMI3_N2_NEGATIVE_MODE=invalid
strict QC debug:     WXSAMI3_N2_NEGATIVE_MODE=fail
```

The next physical QC step should add explicit top blending/source flags, then
run the same receiver-stub matrix with `floor` and `invalid` so the effect of
negative residual N2 fallback is quantified before any full SAMI3 physics run.
