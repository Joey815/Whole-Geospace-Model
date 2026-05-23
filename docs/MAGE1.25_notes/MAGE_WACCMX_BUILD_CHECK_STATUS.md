# MAGE-WACCMX Build Check Status

This note records the current compile-validation status of the isolated
`MAGE + WACCM-X(CESM)` coupling work.

## What Worked

### 1. CAM standalone configure path

An isolated standalone CAM build-check directory was created at:

- `/home/jiaoy_group/jiaoy/data/CESM/experiments/cam_waccmx_buildcheck_20260325a`

The following configure path succeeded:

- CAM source root: `/home/jiaoy_group/jiaoy/data/CESM/cam_official_probe`
- Coupling: `-cpl nuopc`
- Dynamics: `-dyn fv`
- Physics: `-phys cam6`
- Chemistry: `-chem waccm_ma_mam5`
- WACCM-X: `-waccmx -ionosphere wxie`
- Levels: `-nlev 130`

Generated artifacts:

- `/home/jiaoy_group/jiaoy/data/CESM/experiments/cam_waccmx_buildcheck_20260325a/Filepath`
- `/home/jiaoy_group/jiaoy/data/CESM/experiments/cam_waccmx_buildcheck_20260325a/Srcfiles`
- `/home/jiaoy_group/jiaoy/data/CESM/experiments/cam_waccmx_buildcheck_20260325a/Depends`
- `/home/jiaoy_group/jiaoy/data/CESM/experiments/cam_waccmx_buildcheck_20260325a/CESM_cppdefs`
- `/home/jiaoy_group/jiaoy/data/CESM/experiments/cam_waccmx_buildcheck_20260325a/config_cache.xml`

This confirms that the current CAM/WACCM-X source edits are compatible with a
legal standalone `nuopc + waccmx + wxie` configuration at the script level.

### 2. CIME Python/runtime path

The full CESM `cime/scripts` utilities required Python `3.9+`.
This was resolved without touching the user home configuration by using:

- module: `intel/anaconda/2024.10`
- temporary HOME: `/home/jiaoy_group/jiaoy/data/CESM/experiments/cime_home_20260325a`

With that temporary HOME, `query_config` worked and confirmed that the local
CESM tree knows about WACCM-X compsets such as:

- `FX2000`
- `FXHIST`
- `FXSD`
- `QPX2000`

### 3. Real operational case rebuild path

Separate from the incomplete probe checkouts above, the active operational case
at:

- `/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_qhslurm_gnu`

was rebuilt successfully on `2026-03-26` after the `neutral_rhs` source edits.

Observed evidence:

- rebuilt executable timestamp:
  `/online1/jiaoy_group/jiaoy/cesm/scratch/mage_qpx2000_f19_qhslurm_gnu/bld/cesm.exe`
- timestamp after rebuild:
  `2026-03-26 20:27:18 +0800`
- rebuild command path:
  `./case.build --skip-provenance`

This means the currently active real bridge environment can carry the patched
`CESM/WACCM-X` code through a full executable rebuild, even though the
standalone/probe checkouts remain incomplete.

### 4. Isolated mainline-style kaiju rebuild path

An isolated mainline-style `kaiju` worktree was created at:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_mainline`

The following binary was rebuilt successfully on `2026-03-26`:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_mainline/build/bin/voltron.x`

This worktree carries the runtime-opened GEO feedback path for the
`WACCMX_STUB` backend. Its rebuild passed, and the resulting binary completed a
real file-bridge rerun at:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainline_geo_cycle_20260326a`

Observed evidence:

- `run_bidirectional_cycle.sh` exit status:
  `0`
- bridge completion marker:
  `Bidirectional CESM<->kaiju file-coupled cycle completed.`
- step 2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainline_geo_cycle_20260326a/step2_kaiju_feedback/waccmx_voltron_contract.txt`

This confirms that the `MAGE-WACCMX` source edits are not limited to the older
experimental backend tree. They also compile and run in an isolated
mainline-based `voltron.x` worktree.

### 5. Actual main repository rebuild path

The same GEO-feedback edits were then merged into the actual repository:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju`

and rebuilt through the existing main-repo `voltron.x` build tree:

- build tree:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr`
- rebuilt binary:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr/bin/voltron.x`

This rebuild required restoring the HDF5 module include path in the shell:

- `CPATH=/apps/support/intel_spr_rocky8.9/hdf5/1.13.0/intel2023.2_impi/include`
- `INCLUDE=/apps/support/intel_spr_rocky8.9/hdf5/1.13.0/intel2023.2_impi/include`

Without those two variables, the existing main-repo build tree already failed
earlier than the new WACCM-X edits at:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/base/ioH5Types.F90`

After restoring the HDF5 include path, the main-repo rebuild passed. The new
binary first completed a smoke-validation run at:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_mainrepo_smoke/mainrepo_geo_smoke_20260326a`

with the expected nonzero GEO-feedback contract:

- Hemisphere 1 `NEUTRAL_DYNAMO_RHS absmax = 41591.066 cm/s`
- Hemisphere 2 `NEUTRAL_DYNAMO_RHS absmax = 43965.227 cm/s`

The same rebuilt binary then completed a full real file-bridge cycle through:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`

with completed run root:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainrepo_geo_cycle_20260326a`

This means the actual main repository is now beyond source-only integration or
smoke validation. It has completed the same real `kaiju -> CESM -> kaiju`
bridge cycle that was previously proven in the isolated worktree.

### 6. NSRHS phase-2 experimental rebuild path

On `2026-03-27`, the explicit `NSRHS` phase-2 line also completed repeated
real rebuilds of the active operational CESM case:

- case:
  `/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_qhslurm_gnu`

The rebuilds covered:

- `mage_waccmx_feedback_stub.F90` sidecar export changes
- `edynamo.F90` folded-RHS handling changes

The successful rebuilds required keeping the isolated temporary HOME workaround:

- `HOME=/home/jiaoy_group/jiaoy/data/CESM/experiments/home_nsrhs_build`

This avoids the incompatible legacy user file:

- `/home/jiaoy_group/jiaoy/.cime/config_machines.xml`

from being validated against the newer CIME schema used by the active case.

The latest successful phase-2 rebuild completed before the mirrored-NSRHS
verification run `nsrhs_cycle_20260327d`.

## What Blocked The Real Compile

### 1. The standalone CAM checkout is incomplete for a full build

The standalone CAM probe at:

- `/home/jiaoy_group/jiaoy/data/CESM/cam_official_probe`

contains an empty `cime/` directory.

That means the old standalone build flow can be configured far enough to write
`Filepath/Srcfiles/Depends`, but it does not have the complete dependency tree
needed to carry a full executable build through `MCT/PIO/CIME` integration.

### 2. The full CESM checkout is also incomplete

The full CESM probe at:

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe`

has complete source for:

- `components/cam`
- `components/cmeps`

but several other required component trees are effectively empty in the local
checkout, for example:

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/clm`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cice`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cdeps`

`create_newcase` therefore fails before build stage when it tries to load
component configuration files such as:

- `components/clm/cime_config/config_component.xml`
- `components/cdeps/docn/cime_config/config_component.xml`

So the current blocker is not the new MAGE/WACCM-X source edits themselves.
The blocker is that the local CESM component checkout is incomplete.

## Practical Conclusion

Current status is:

- source-level CAM/WACCM-X coupling edits: in place
- standalone configure validation: passed
- probe-checkout case/build validation: blocked by incomplete CESM checkout
- active operational case rebuild: passed
- isolated mainline-style `kaiju` rebuild and real bridge rerun: passed
- actual main-repo `kaiju` rebuild and smoke validation: passed

## Next Required Step

Before a real `MAGE + WACCM-X(CESM)` compile can complete, one of the following
must happen:

1. Populate the missing CESM component source trees in
   `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe`.
2. Provide a different complete CESM checkout and reuse the current source
   patches there.

Until then, the environment can support source-level and configure-level
validation in the incomplete probe trees. The active operational case already
supports full rebuilds and executable links for the current real bridge work.
