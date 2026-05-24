# WACCM-X/SAMI3 Append2 Archive Workflow

Date: 2026-05-25

## Scope

This checkpoint adds a small post-run archiver for the WACCM-X -> SAMI3 full
append2 integration runs.  It is meant to be run immediately after the queued
append2 or direct-wait Slurm job finishes, before committing the result to the
collaboration repository.

New script:

```text
scripts/archive_wxsami3_append2_result.py
```

It runs both validators:

```text
scripts/validate_wxsami3_append2_run.py
scripts/validate_wxsami3_live_packet_contract.py
scripts/validate_wxsami3_topblend_policy.py
scripts/validate_wxsami3_runtime_map.py
```

and copies only lightweight evidence:

```text
slurm-*.out / slurm-*.err
waccmx_cesm.out
sami3_online_receiver.out
phi_payload_summary.txt
live_dump_summary_pkt*.txt
replay_builder_pkt*.out
recv_qc_compare_pkt*.txt
wxsami3_live_meta.json
sacct_<jobid>.txt
validator JSON/text outputs
archive_summary.json
```

It deliberately skips large binary products such as `.bin`, `.nc`, `.h5`, and
`.npz`.

## Smoke Test

Smoke-tested on the already completed Voltron phi two-frame runtime:

```text
python3 scripts/archive_wxsami3_append2_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_2frame_20260525_0000 \
  --archive-dir /tmp/wxsami3_append2_archive_smoke_20260525 \
  --job-id 7659383 \
  --expected-phi-frames 2 \
  --expected-live-packets 1 \
  --expected-sami3-workers 32
```

Result:

```text
append2_validator_returncode = 0
phi_payload_contract_returncode = 0
time_axis_returncode = 0
live_packet_contract_returncode = 0
copied_files = 9
overall = ok
```

## Use On Queued Append2 Job

For the current pre-generated append2 full integration job:

```text
jobid = 7659727
run_dir = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525_0000
```

after completion:

```text
python3 scripts/archive_wxsami3_append2_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525_0000 \
  --archive-dir logs/waccmx_append2_full_20260525 \
  --job-id 7659727 \
  --expected-phi-frames 2 \
  --expected-live-packets 1 \
  --expected-sami3-workers 32 \
  --require-nonzero-phi \
  --require-receiver-phi-values \
  --require-changing-phi-frames \
  --expect-top-blend-mode linear \
  --expect-blend-bottom-km 600 \
  --expect-blend-top-km 720 \
  --min-total-blend-cells 1 \
  --require-zero-unknown-source-flags \
  --require-he-native \
  --require-w-zero \
  --weights-nc /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc \
  --expected-runtime-map-nsource 13824
```

## Use On Direct-Wait Job

For the queued direct-wait successor:

```text
jobid = 7661005
run_dir = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000
```

after completion:

```text
python3 scripts/archive_wxsami3_append2_result.py \
  --run-dir /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000 \
  --archive-dir logs/waccmx_append2_directwait_20260525 \
  --job-id 7661005 \
  --expected-phi-frames 2 \
  --expected-live-packets 1 \
  --expected-sami3-workers 32 \
  --expect-phi-wait-marker \
  --expect-direct-wait-mode \
  --require-nonzero-phi \
  --require-receiver-phi-values \
  --require-changing-phi-frames \
  --expect-top-blend-mode linear \
  --expect-blend-bottom-km 600 \
  --expect-blend-top-km 720 \
  --min-total-blend-cells 1 \
  --require-zero-unknown-source-flags \
  --require-he-native \
  --require-w-zero \
  --weights-nc /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc \
  --expected-runtime-map-nsource 13824
```

## Acceptance Meaning

Passing this workflow means:

```text
Voltron/REMIX phi payload has the expected two-frame binary schema
phi payload frames are finite, time-ordered, valid-until ordered, and nonzero
Voltron/REMIX phi payload frames evolve between frames
SAMI3 `WACCMX_PHI_RECV` frame hour/valid-until/min/max match the payload
WACCM-X sender sent the expected phi frames
direct-wait runs show a same-job Voltron writer PID and sender wait marker
top-blend diagnostics show linear 600-720 km blending and nonzero blend cells
source-flag unknown counts remain zero
He remains native and W remains zero for valid payload cells
live dump fields have zero bad counts and plausible ranges for T/U/V/pressure/height/major species
runtime map header and row/col/weight arrays match the ESMF weights file
SAMI3 received the expected phi frames
SAMI3 reached MASTER: All Done!
WACCM-X reached END OF MODEL RUN
neutral receiver QC matches replay payload from same-call-site live dump
small evidence bundle is ready for GitHub
```

It still does not close the production physics blockers around top-blend
policy, He fallback, W/vertical-wind policy, f09 distributed remap, and
production SAMI3 -> RAIJU/GAMERA mapping.

The older pre-append writer two-frame payload remains useful as a nonzero
schema check, but it is not sufficient for the final REMIX -> SAMI3 time-gated
potential path. The queued append2/direct-wait jobs must pass
`--require-changing-phi-frames`.
