# MAGE-WACCMX Report-Driven Registration

This note turns the report
`MAGE耦合WACCM-X：模型体系、耦合机制、实现与可复现性研究报告.docx`
into a concrete implementation draft for the isolated `CESM/CMEPS` and `CAM/WACCM-X` probes.

## Confirmed Exchange Categories From The Report

- `REMIX -> WACCM-X`: high-latitude electric forcing and particle precipitation.
- `WACCM-X -> REMIX`: neutral wind, conductance, outflowing ions, and neutral moments.

The report also makes two implementation constraints explicit:

- `REMIX` remains the geospace-side electrodynamics hub; `CPL7/CIME` is not the magnetosphere-ionosphere coupler.
- `MAGE` seconds-level coupling and `WACCM-X` minutes-level timestepping must be bridged by accumulation, averaging, or subcycling. That problem is not solved by field registration alone.

## Registration Draft

The isolated draft maps the report-confirmed exchange categories into mediator-facing field names:

`MAGE -> WACCM-X`

- `Sx_mage_epot`
- `Sx_mage_avg_energy`
- `Faxx_mage_numflux`

`WACCM-X -> MAGE`

- `Sa_mage_sigmap`
- `Sa_mage_sigmah`
- `Sa_mage_nwind_u`
- `Sa_mage_nwind_v`
- `Faxa_mage_ion_outflow`
- `Sa_mage_neutral_temperature`
- `Sa_mage_neutral_density`

This is intentionally a minimal draft:

- Electric forcing is carried as potential because `WACCM-X` already has internal electrodynamics pathways keyed to electrostatic forcing.
- Precipitation is represented by mean energy plus number flux, matching the existing MAGE-TIEGCM style and the current isolated prototype contract.
- "Neutral moments" are represented only by temperature and density placeholders in this first pass because the report confirms the category but does not provide a machine-readable full state vector.

## Source Entry Points Patched

`CMEPS field dictionary`

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cmeps/mediator/fd_cesm.yaml`

`CAM NUOPC import/export registration`

- `/home/jiaoy_group/jiaoy/data/CESM/cam_official_probe/src/cpl/nuopc/atm_import_export.F90`

`CAM/WACCM-X aurora ingest stub`

- `/home/jiaoy_group/jiaoy/data/CESM/cam_official_probe/src/ionosphere/waccmx/mage_waccmx_ingest_stub.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cam_official_probe/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cam_official_probe/src/ionosphere/waccmx/ionosphere_interface.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cam_official_probe/src/physics/cam/physpkg.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cam_official_probe/src/physics/waccm/mo_aurora.F90`

Current state:

- The new mediator-facing fields are advertised and realized in `atm_import_export.F90`.
- `Sx_mage_avg_energy` and `Faxx_mage_numflux` are now cached in a dedicated ingest stub.
- `ionosphere_interface.F90` maps those cached fields into `AUREFX/AURKEV`.
- `mo_aurora.F90` now accepts that stub auroral forcing even when `prescribed_period` is not coming from AMIE/LTR.
- `Sx_mage_epot` is now source-hooked into the `WACCM-X` electrodynamics path through `d_pie_set_external_epot(...)`, which writes `phihm` and `prescr_phihm`.
- The current `epot` hook is still a draft contract: it assumes a flat magnetic-grid payload sized either `nmlon*nmlat` or `nmlonp1*nmlat`, and it has not yet been validated in a full `CAM/CESM` build.
- If MAGE electric potential is present but MAGE aurora is not, `ionosphere_interface.F90` now backfills `AUREFX/AURKEV` from AMIE/LTR when available, or zeros them explicitly so the aurora path remains well-defined.
- `physpkg.F90` now captures `PedConduct/HallConduct` before `pbuf_deallocate(pbuf2d, 'physpkg')` runs.
- `mage_waccmx_feedback_stub.F90` column-integrates those conductivities on the CAM column layout and keeps a minimal cache alive until `atm_import_export.F90:export_fields(...)` runs.
- `atm_import_export.F90` now fills `Sa_mage_sigmap` and `Sa_mage_sigmah` from that cache instead of leaving those fields registration-only.

`Isolated MAGE/REMIX return stub`

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_backend.F90`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/mixsolver.F90`

Current state:

- The isolated prototype now injects a `neutral_dynamo_rhs` proxy through the existing `NEUTRAL_WIND` slot.
- `mixsolver.F90` adds a small source term from `NEUTRAL_WIND` into the RHS, so a minimal `WACCM-X -> REMIX` electrodynamic feedback now exists in the isolated worktree.
- This is a controlled stub, not a physically complete neutral-wind dynamo implementation.
- The ingest/adaptor contract has also been extended to `sidecars_v2`, adding explicit return groups for `outflowing ions` and `neutral moments`.
- A dedicated outflow payload driver now compresses `/return_outflow_north` and `/return_outflow_south` into an `IMAG/MHD`-style 5-scalar payload in fixed order:
  `im_d_ring, im_p_ring, im_d_cold, im_p_cold, im_tscl`.

## What Still Needs Real Wiring

- Replace the current flat magnetic-grid `Sx_mage_epot` stub contract with a real mediator/grid-aware field path that is valid under distributed `CESM/CMEPS` execution.
- Build-verify the new conductance cache path and confirm that the column-integrated proxy is the right mediator-facing quantity.
- Extend the same export-side mapping pattern beyond conductance to WACCM-X wind, outflow, and neutral state diagnostics in `Sa_mage_*` and `Faxa_mage_*`.
- A cadence bridge between seconds-level MAGE electrodynamics and the typical `~300 s` WACCM-X step noted in the report.
- Final definitions for ion outflow species content, reference altitude, and the full neutral-moments payload.
- Real sidecar packaging/transport for `outflowing ions` and `neutral moments`, which should not be forced into the 2-D `gcm_T -> REMIX` path.

## Immediate Next Step

Use the real-source entry points already identified in the isolated probes to move from the current stubs to a broader round-trip:

1. Thread `Sx_mage_epot` into the WACCM-X-side electrodynamics path rather than leaving it as a cached field.
2. Replace the current source-only `epot` hook with a build-verified, grid-aware CAM/WACCM-X implementation.
3. Build-verify the new `Sa_mage_sigmap` and `Sa_mage_sigmah` export path and confirm its grid and unit semantics.
4. Keep `neutral wind` feedback on the `REMIX` RHS path, but keep `outflow` and `neutral moments` on the new sidecar/payload path rather than the 2-D `gcm_T` contract.
