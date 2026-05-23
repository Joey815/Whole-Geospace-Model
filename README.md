# WACCM-X / SAMI3 / MAGE Coupling Collaboration Snapshot

Snapshot date: 2026-05-24 CST

This repository is a compact collaboration package for the local
MAGE1.25-WACCMX and WACCM-X -> SAMI3 online MPI coupling work.  It intentionally
contains code, notes, run scripts, and small verification artifacts, but not
large model outputs, compiled executables, generated payload binaries, full
CESM/MAGE/SAMI3 source trees, or input datasets.

## Current Status

The current verified WACCM-X -> SAMI3 status is:

```text
f19 online runtime live neutral-packet prototype.
Full SAMI3 smoke is validated for two packets plus done.
Receiver-stub transport is validated for three live packets plus done.
File-mode fallback regression remains validated.
Not production live WACCM-X neutral forcing yet.
```

Latest verified jobs:

```text
live two-packet smoke = 7641573, COMPLETED, exit 0:0
file-mode fallback    = 7641579, COMPLETED, exit 0:0
receiver-stub 3-pkt   = 7641623, COMPLETED, exit 0:0
N2-QC default smoke   = 7641625, COMPLETED, exit 0:0
N2-QC invalid smoke   = 7641644, COMPLETED, exit 0:0
source-flag metadata  = 7641645, COMPLETED, exit 0:0
receiver source flags = 7641669, COMPLETED, exit 0:0
```

Latest receiver checks:

```text
pkt000000 live compare = max_rel=4.86991e-13
pkt000001 live compare = max_rel=6.80359e-13
file fallback compare  = max_rel=3.26946e-13
stub packet count       = ranks 1..32 received 3 packets; ranks 0..32 got done
N2-QC default mode      = WXSAMI3_N2_NEGATIVE_MODE=floor, build and 3-pkt smoke ok
N2-QC invalid delta     = +177092 invalid samples vs floor, 3-pkt transport ok
source-flag metadata    = WACCMX_VALID=4211362, ABOVE_TOP=1642906, N2_INVALID=177092
full SAMI3 recv flags   = two packets, done=2, replay compare max_rel <= 6.76502e-13
```

The latest source-state phase diagnostic compared live packet 2 against
same-run instantaneous CAM history at 00600.  The comparison confirms matching
lat/lon and OMEGA, but T/U/V/Z/species differ because the live hook is in
`cam_run2` before the later history-write phase.  Treat CAM history as a phase
diagnostic, not as a strict same-call-site source-state reference for the
current hook.

## Layout

```text
docs/MAGE1.25_notes/
  Planning notes, status reports, handoff files, and older WACCM-X/MAGE/SAMI3
  route notes.

code/cesm_source_mods/
  Current copied-case CESM SourceMods used for the f19 WACCM-X -> SAMI3 live
  neutral sender prototype.

code/sami3_receiver/
  Current SAMI3 online receiver-side modules used in the local OpenMPI work tree.

scripts/
  C and Python helper tools for live dump reading, replay payload generation,
  runtime-map packing, source-state comparison, and receiver QC comparison.

slurm/
  Reproduction launchers for live dump, live replay, runtime live payload,
  file-mode fallback, and two-packet multipacket smoke tests.

logs/
  Small verification outputs and metadata sidecars from the latest useful runs.

manifests/
  Included-file list and large local artifacts deliberately not committed.
```

## Main Entry Points

Start with:

```text
docs/MAGE1.25_notes/mage125_waccmx_handoff_2026-05-23.md
docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_NEUTRAL_PLAN_20260523.md
docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_NEUTRAL_EXTRACTION_RESULT_20260523.md
docs/MAGE1.25_notes/WACCMX_SAMI3_SOURCE_STATE_PHASE_VALIDATION_20260524.md
docs/MAGE1.25_notes/WACCMX_SAMI3_N2_QC_CONTROL_20260524.md
docs/MAGE1.25_notes/WACCMX_SAMI3_N2_INVALID_MODE_RESULT_20260524.md
docs/MAGE1.25_notes/WACCMX_SAMI3_SOURCE_FLAGS_METADATA_20260524.md
docs/MAGE1.25_notes/WACCMX_SAMI3_RECEIVER_SOURCE_FLAGS_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_GAMERA_PHYSICS_REVIEW_20260523.md
```

For the standing remote-update rule, see:

```text
UPDATE_WORKFLOW.md
```

Current sender implementation:

```text
code/cesm_source_mods/src.cam/wxsami3_online_stub_mod.F90
code/cesm_source_mods/src.cam/cam_comp.F90
```

Current receiver implementation:

```text
code/sami3_receiver/waccmx_neutral_mod.f90
```

Latest two-packet smoke launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_multipacket_20260524.sbatch
```

Latest receiver-only three-packet transport launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_compare_20260524.sbatch
```

Latest N2 residual QC launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_n2qc_20260524.sbatch
slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_n2qc_invalid_20260524.sbatch
slurm/run_waccmx_cam_sami3_live_payload_f19_receiver_stub_3pkt_source_flags_20260524.sbatch
```

Latest full SAMI3 receiver source/fallback diagnostic launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_multipacket_n2invalid_recvflags_20260524.sbatch
```

## Known Physical Blockers

Do not describe this snapshot as production live WACCM-X neutral forcing until
these are handled:

```text
strict same-call-site offline-vs-live source-state validation
explicit WACCM-X-top SAMI3-native fallback or blending policy
receiver-side reason split for above-top vs N2-invalid fallback if needed
He native/MSIS fallback policy hardening
W-off / vertical-wind policy validation
REMIX -> SAMI3 potential/E-field forcing
SAMI3 -> RAIJU/GAMERA flux-tube weighting and L/MLT mapping
f09/finer distributed remap design
```

## Large Artifacts

Large generated files are not committed.  See:

```text
manifests/large_artifacts_not_committed.txt
```

The most important omitted artifacts include the f19 ESMF weights, runtime map,
live dump binaries, replay payload binaries, compiled executables, and full run
directories.

## GitHub Upload Note

This collaboration snapshot is pushed to:

```text
https://github.com/Joey815/Whole-Geospace-Model.git
```

Keep the repository private unless the upstream model-source and data-license
constraints have been reviewed.
