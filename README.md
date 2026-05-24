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

The current verified SAMI3 -> RAIJU/GAMERA scalar-moment status is:

```text
ds_over_B field-line weighting prototype is available.
L/MLT RAIJU mapping prototype is available.
Explicit /MappingQuality datasets are available for runtime L/MLT products.
MappingQuality product runtime ingest smoke is validated with the extra group
present and the Fortran hook reading only /RaiCplMomentsOnly.
Explicit sparse SAMI3-to-RAIJU mapping weight files are implemented and
validated: the current l_mlt_separable file reproduces the inline L/MLT mapper
with max_rel=1.19e-7.
The mapping weight schema now carries RAIJU target bvol/topo/Bmin geometry and
derives closed_field_mask from the same four-corner topology rule used by
RAIJU.
Schema v3 Voltron-shell intermediate mapping weights are implemented and
validated: SAMI3 -> Voltron TubeShell ShellGrid -> RAIJU ShellGrid reproduces
the inline L/MLT product with max_rel=1.19e-7 while carrying Voltron
TubeShell bVol/topo/Lb/bmin/nTrc geometry.
The Voltron-shell stage-2 product also passes a runtime ingest smoke: job
7649439 completed 0:0, final raiCpl blend formula checks are exact, and checked
physics fields contain no NaN/Inf.
An additional `voltron_tubeshell_l_mlt` prototype maps SAMI3 onto Voltron
TubeShell cell-centered `Lb + lon0/lonc` before the Voltron->RAIJU step; both
longitude choices validate with finite MappingQuality, and lon0/lonc differ
only at roundoff for the current template.
Runtime blending is validated with alpha=0 exact baseline recovery.
Density alpha scan is finite and continuous through alphaDavg=0.20.
Pressure alpha scan at alphaDavg=0.05 is finite for alphaPavg=0.05 and 0.10.
RAIJU moment semantics audit is complete for Pavg/Davg/Pstd/Dstd/tiote.
Gridded State%tiote can now be enabled for moment-to-eta mapping with
moments/useStateTioteForIngest=T; default behavior remains unchanged.
Recommended short prototype is validated with alphaDavg=0.05, alphaPavg=0.05,
alphaTiote=1, alphaPstd=0, alphaDstd=0, and useStateTioteForIngest=T.
Recommended prototype also passes a 60 second baseline/control smoke with no
non-finite physics fields.
Recommended prototype now also passes a 300 second Slurm baseline/control smoke:
job 7648350 completed 0:0, both runs reached Fin, final raiCpl blend formula
checks are exact, and checked physics fields contain no NaN/Inf.
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
reason flag sidecar   = 7645354, COMPLETED, exit 0:0
file tag212 regression= 7645380, COMPLETED, exit 0:0
stub tag212 runtime   = 7645415, COMPLETED, exit 0:0
sami3 raiju long300   = 7648350, COMPLETED, exit 0:0
sami3 mapq runtime    = 7648737, COMPLETED, exit 0:0
sami3 volshell runtime= 7649439, COMPLETED, exit 0:0
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
reason flag sidecar     = tag 212, full SAMI3 receiver diff=[0,0,0,0,0]
file tag212 regression  = valid=4494609, other_invalid=1536751, unknown=0
stub tag212 runtime     = 3 packets, done=3, packet2 diff=[0,0,0,0,0]
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
docs/MAGE1.25_notes/WACCMX_SAMI3_SOURCE_REASON_FLAGS_RESULT_20260524.md
docs/MAGE1.25_notes/WACCMX_SAMI3_TOP_BLEND_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_WEIGHTING_CONTRACT_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_EXTENDED_DIAGNOSTICS_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_DS_OVER_B_WEIGHTING_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_L_MLT_MAPPING_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_MAPPING_QUALITY_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_MAPPING_QUALITY_RUNTIME_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_EXPLICIT_WEIGHT_FILE_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_WEIGHT_FILE_BVOL_GEOMETRY_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_VOLTRON_SHELL_WEIGHT_FILE_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_VOLTRON_SHELL_RUNTIME_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_VOLTRON_TUBESHELL_WEIGHT_FILE_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_RUNTIME_BLEND_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_STAGE2_SOURCE_MODES_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_DSB_LMLT_RUNTIME_BLEND_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_DSB_LMLT_ALPHA_SCAN_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_DSB_LMLT_PRESSURE_SCAN_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_MOMENT_SEMANTICS_TIOTE_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_RECOMMENDED_PROTOTYPE_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_RECOMMENDED_LONG60_RESULT_20260524.md
docs/MAGE1.25_notes/SAMI3_RAIJU_RECOMMENDED_LONG300_RESULT_20260524.md
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
code/sami3_receiver/Makefile
```

Current SAMI3 -> RAIJU scalar-moments adapter snapshot:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/
code/kaiju_sami3_moments/src/voltron/modelInterfaces/
code/kaiju_sami3_moments/src/raiju/
code/kaiju_sami3_moments/src/base/types/
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

Latest full SAMI3 source-reason sidecar diagnostic launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_multipacket_reasonflags_20260524.sbatch
```

Latest full SAMI3 WACCM-X-top blending diagnostic launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_multipacket_topblend_20260524.sbatch
```

Latest SAMI3 -> RAIJU/GAMERA recommended prototype runtime evidence:

```text
logs/sami3_dsB_lmlt_recommended_long300_20260524/
```

Latest SAMI3 -> RAIJU/GAMERA mapping quality evidence:

```text
logs/sami3_mapping_quality_20260524/
logs/sami3_mapping_quality_runtime_20260524/
logs/sami3_weightfile_mapping_20260524/
logs/sami3_weightfile_bvol_geometry_20260524/
logs/sami3_voltron_shell_weightfile_20260524/
logs/sami3_voltron_shell_runtime_20260524/
logs/sami3_voltron_tubeshell_weightfile_20260524/
```

## Known Physical Blockers

Do not describe this snapshot as production live WACCM-X neutral forcing until
these are handled:

```text
strict same-call-site offline-vs-live source-state validation
production choice of WACCM-X-top blending heights and per-variable policy
He native/MSIS fallback policy hardening
W-off / vertical-wind policy validation
REMIX -> SAMI3 potential/E-field forcing
production SAMI3 -> RAIJU/GAMERA Voltron-consistent flux-tube weighting
replace prototype l_mlt_separable mapping weights with Voltron traced-tube or bvol-aligned weights
production SAMI3 -> RAIJU/GAMERA geometry/mask coverage policy
longer runtime scans for density, pressure, and tiote blending
longer-duration stability scan beyond the 300 second recommended prototype
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
