# MAGE1.25 WACCM-X/SAMI3/RAIJU/GAMERA Four-Way Coupling Plan

Generated: 2026-05-27

## Current Status

The current four-way coupling work has passed the integrated prototype stage, but it is not yet production-ready for science conclusions.

The validated prototype evidence supports this statement:

```text
WACCM-X CAM phys_state(:) live neutral packets reach SAMI3.
REMIX/Voltron runtime POT reaches SAMI3 as direct-MPI phi frames.
SAMI3-derived scalar moments can be ingested by RAIJU/GAMERA with conservative blending.
The downstream SAMI3 -> RAIJU/GAMERA adapter remains diagnostic/prototype because of the RAIJU target-domain source-volume issue.
```

Primary evidence archive:

```text
logs/integrated_prototype_20260527/
```

Key completed prototype runs:

```text
WACCM-X -> SAMI3 live neutral + Voltron/REMIX -> SAMI3 phi
  job: 7697673
  run_dir: /online1/jiaoy_group/jiaoy/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_maxstep2800_20260526_0000
  status: COMPLETED
  neutral packets: 24
  phi frames: 24
  validators: ok

SAMI3 -> RAIJU/GAMERA scalar moments
  job: 7678667
  run_dir: /online1/jiaoy_group/jiaoy/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526
  status: COMPLETED
  runtime: 1800 s class, history through Step#361
  modes: density-only and density+tiote
  validators: diagnostic ok, production readiness fail
```

## Current Boundary

The current 2024-10-03 flare/no-flare jobs are not SAMI3 four-way runs.

They are:

```text
MAGE/RAIJU/GAMERA <-> WACCM-X online
```

They do not include SAMI3. They are useful for WACCM-X replacing the earlier TIEGCM-style MAGE coupling path and for the flare/no-flare FISM comparison, but they do not remove the four-way coupling blocker below.

## Main Blocker

The critical blocker is in the SAMI3 -> RAIJU/GAMERA production gate.

Current integrated evidence reports:

```text
production_readiness: FAIL
source bVol skipped above target Lmax: 0.999595965103914
runtime valid fraction: 0.9574468085106383
```

Interpretation:

```text
SAMI3/Voltron source flux-tube volume and the RAIJU/GAMERA target shell domain are not yet reconciled well enough for production physical coupling.
```

This does not mean the runtime hook is broken. It means the current mapping/masking semantics are still diagnostic and must become target-domain aware before science claims.

## Target

Upgrade the four-way chain from:

```text
integrated prototype / diagnostic adapter
```

to:

```text
production-ready short-window coupling suitable for 2024-10-03 flare/no-flare science comparison
```

The intended production chain is:

```text
WACCM-X/CAM phys_state(:)
  -> SAMI3 neutral forcing

REMIX/Voltron potential/E-field
  -> SAMI3 electrodynamic forcing

SAMI3 plasma state
  -> scalar plasma moments Pavg/Davg/Pstd/Dstd/tiote
  -> RAIJU/GAMERA conservative runtime ingest

RAIJU/GAMERA/MAGE state
  -> WACCM-X online exchange where applicable
```

## Plan

### P0: Fix the SAMI3 -> RAIJU/GAMERA target-domain/source-volume gate

Goal:

```text
Make the production-readiness validator domain-aware and remove the false/real mismatch behind source bVol skipped above target Lmax.
```

Tasks:

1. Audit SAMI3 source L/MLT coverage.
2. Audit Voltron tube-shell source coverage and bVol semantics.
3. Audit RAIJU target shell/MLT admissible domain.
4. Classify source tubes into:
   - admissible target-domain contributors
   - physically outside target domain
   - invalid/extrapolated contributors
5. Update validators so production checks are applied to the admissible target subset, not to source regions that RAIJU cannot physically consume.
6. Preserve diagnostics for excluded source volume:
   - excluded above Lmax
   - outside target shell
   - no closed-field target
   - extrapolated/invalid

Acceptance criteria:

```text
diagnostic_contract: ok
production_readiness: ok or explicitly blocked by a remaining physical mismatch
target-domain conservation/coverage checks pass on admissible subset
excluded source-volume fractions are reported by reason
no NaN/Inf in RAIJU/GAMERA output
alpha=0 returns baseline within validator tolerance
```

### P1: Stabilize SAMI3 scalar moment semantics

Goal:

```text
Keep the RAIJU/GAMERA ingest physically interpretable before expanding variables.
```

Current coupled scalar moments:

```text
Pavg
Davg
Pstd
Dstd
tiote
```

Tasks:

1. Keep `Davg` mode explicit:
   - number density
   - mass-equivalent density
2. Keep `Pavg` mode explicit:
   - ion pressure
   - total pressure
   - original pressure plus cold correction
3. Keep conservative blending controls:
   - density may be enabled first
   - pressure and std should not be overwritten by default
   - tiote can be enabled after density-only continuity is verified
4. Keep floors and finite-value checks:
   - density floor
   - pressure floor
   - tiote min/max
   - NaN/Inf rejection

Recommended initial production-style setting:

```text
alpha_Davg = 0.05 or controlled density-only mode
alpha_Pavg = 0.0
alpha_Dstd = 0.0
alpha_Pstd = 0.0
alpha_tiote = 0.0 until density-only response is stable
```

Acceptance criteria:

```text
blend formula max_abs = 0.0 for active fields
inactive fields remain baseline-equivalent
density-only and density+tiote runs differ continuously
RAIJU/GAMERA history and restart products remain finite
```

### P2: Build one single-workflow four-way smoke run

Goal:

```text
Move from separate validated components to one coordinated runtime smoke workflow.
```

The smoke workflow should launch:

```text
WACCM-X live neutral sender
SAMI3 online receiver
Voltron/REMIX phi sender
RAIJU/GAMERA moments ingest
```

This is not yet the science run. It is a choreography and contract test.

Required checks:

```text
neutral packet cadence
phi frame cadence
SAMI3 done tags
WACCM-X done tags
Voltron/REMIX phi done tags
RAIJU/GAMERA history/restart output
time-axis consistency
alpha=0 baseline recovery
no NaN/Inf
strict validator pass
```

Acceptance criteria:

```text
all components terminate normally
all expected packets/frames are received
strict runtime validators pass
HDF5 outputs exist and are readable
run can be archived in logs/
```

### P3: Move from f19 prototype to the 2024-10-03 event configuration

Goal:

```text
Use the four-way machinery on the flare/no-flare event configuration without mixing resolutions or incompatible runtime maps.
```

Current state:

```text
WACCM-X -> SAMI3 live neutral evidence: f19, 144 x 96 source columns
2024-10-03 flare/no-flare WACCM-X science cases: f09, 288 x 192 source columns
```

Near-term route:

```text
Run an f19 event smoke if fast iteration is needed.
```

Production science route:

```text
Build and validate f09 runtime map.
Port live neutral SourceMods/configuration to f09 flare/no-flare cases.
Validate f09 source columns, species registry, units, top blending, and packet contract.
```

Acceptance criteria:

```text
f09 runtime map source_columns = 288 * 192 = 55296
WACCM-X f09 live packet metadata matches f09 source grid
flare/noflare only differ in intended FISM inputs and controlled runtime settings
SAMI3 receiver validates f09 packet contract
```

### P4: Run the 2024-10-03 12:00-13:00 four-way flare/no-flare pair

Prerequisites:

```text
P0 production gate passes
P1 scalar moment semantics are fixed and documented
P2 single-workflow smoke passes
P3 event configuration is validated
```

Run pair:

```text
flare:
  solar_euv_data_file = fism2_flare_bands_20241003_x9_waccmx.nc

noflare:
  solar_euv_data_file = fism2_noflare_bands_20241003_x9_removed_waccmx.nc
```

Science-window target:

```text
2024-10-03 12:00:00 UT to 13:00:00 UT
```

Required post-run products:

```text
WACCM-X history outputs
SAMI3 receiver and plasma diagnostics
RAIJU/GAMERA HDF5 histories/restarts
flare-minus-noflare quicklooks
packet/frame/moment validator reports
archived run configs and logs
```

Acceptance criteria:

```text
both flare and noflare complete normally
both use intended FISM files
four-way validators pass for both
flare-minus-noflare differences are computed from matched time axes
known limitations are documented before any science interpretation
```

## Immediate Next Action

Start with P0.

Concrete first step:

```text
Re-open the SAMI3 -> RAIJU/GAMERA target-domain/source-volume validator path and turn the current source bVol skipped above target Lmax failure into a reason-coded, domain-aware production gate.
```

Priority files/logs to inspect first:

```text
logs/integrated_prototype_20260527/status.json
logs/integrated_prototype_20260527/summary.md
logs/integrated_prototype_20260527/limitations.md
logs/sami3_raiju_production_contract_target_subset_20260526/
logs/sami3_raiju_source_l_coverage_20260526/
logs/sami3_raiju_target_admissible_subset_20260526/
logs/sami3_raiju_target_closure_domainaware_20260526/
code/kaiju_sami3_moments/scripts/sami3_moments/
```

Do not start a 2024-10-03 four-way science run until the SAMI3 -> RAIJU/GAMERA production gate is resolved or explicitly reclassified with a defensible physical exclusion policy.
