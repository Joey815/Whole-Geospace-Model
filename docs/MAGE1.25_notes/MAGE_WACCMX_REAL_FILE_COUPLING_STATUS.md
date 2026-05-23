# MAGE 1.25 <-> CESM/WACCM-X Real File-Coupled Status

Date: 2026-03-28
Updated: 2026-03-30

## Current status

As of 2026-03-30, the real file-mediated bidirectional loop is still
successfully closed for single-cycle operation, and the continuation picture is
now narrower than before:

- on 2026-03-30, a new true `x1/x1/x1` multi-cycle bridge attempt using the
  current live production continuation line confirmed the split very cleanly:
  the seed `Kaiju -> CESM import` half completed successfully, but `cycle01`
  `CESM` continuation still reproduced the same `00300 -> 00600`
  `rank 0 SIGSEGV`, so the present blocker in the live path is still the
  known main-case continuation lineage rather than the formal forward variable
  bridge itself
- on the same day, the same formal variable loop was then rerun on the
  isolated `Op`-repaired continuation lineage, and that path has now completed
  **three full bidirectional bridge rounds** end-to-end:
  `03000 -> 03300 -> 03600 -> 03900` on the isolated `CESM` side, with each
  `CESM` leg exiting through `med_finalize`, and matching
  `cycle01_kaiju / cycle02_kaiju / cycle03_kaiju` feedback-ingest legs all
  producing fresh `waccmx_voltron_forward_package.h5`
- on the same day, a new **live main-flow single-cycle validation with a
  toggleable `Op` repair hook** also succeeded end-to-end:
  the real `run_long_coupling_stability.sh` entry completed
  `x1/x1/x1, num_cycles=1` in
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_repair_x1_c1_20260330_live_repair_x1c1`,
  the hook temporarily replaced only the live
  `cam.r.2005-12-31-00300.nc` before `cycle01 CESM`, the `CESM` leg then wrote
  `cam.rs.2005-12-31-00600.nc` and exited through `med_finalize`, the matching
  `cycle01_kaiju` leg completed and wrote a fresh
  `waccmx_voltron_forward_package.h5`, and the original live
  `cam.r.2005-12-31-00300.nc` was restored afterward
- that result was then extended again on 2026-03-30:
  the same real live entry with the same toggleable repair hook completed a
  full `x1/x1/x1, num_cycles=3` run in
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_repair_x1_c3_20260330_live_repair_x1c3`
  and therefore pushed the live production-line continuation chain through
  three more successful bridge rounds:
  `00600 -> 00900 -> 01200 -> 01500`
  with each `CESM` leg writing the next `cam.rs` restart and exiting through
  `med_finalize`, while the corresponding `cycle01_kaiju / cycle02_kaiju /
  cycle03_kaiju` legs all completed and produced fresh forward packages
- importantly, the repair hook log for that successful live 3-cycle run shows
  it no longer had to actively patch later restarts:
  it only skipped pointers
  `00600`, `00900`, and `01200`, so after the initial repaired `00300 -> 00600`
  rescue, the resulting live continuation lineage was able to sustain three
  further bridge rounds without additional state surgery
- those repaired-line multi-round runs also show the formal variables remain
  well-behaved across repeated exchange:
  - the isolated `CESM` summaries show external-`epot` absmax evolving only
    moderately from `12.122` to `15.813` to `15.862`
  - the matching repaired-line `Kaiju` contracts show fed-back conductance
    envelopes staying in the same non-default range, e.g. hemisphere-1
    `SIGMAP` roughly `0.130..17.235`, `0.129..17.217`, `0.127..17.147 S`
    across rounds 1 to 3
- the current main production restart lineage still reproduces a
  `00300 -> 00600` continuation crash even for `x1 baseline`
- that failure is reproducible for `all x14 + smooth2`, `epot x14 + smooth2`,
  and `x1 baseline`
- the repeated low-address backtrace maps into the CAM `FV` dycore path:
  `ModelAdvance -> cam_run1 -> stepon_run1 -> dyn_run -> cd_core -> d_sw -> tp2c/tp2d/xtpv`
- `00600` restart files are actually written to disk before the crash, so the
  current blocker is not simply “restart file missing”
- a matched-pointer pure control has also failed:
  explicit `rpointer.cam=00300`, `rpointer.cpl=00300`, and no bridge import
  files still reproduce the same `SIGSEGV`
- in that pure control log, `d_pie_set_external_epot` does not appear, so the
  reproduced crash no longer requires external `MAGE epot` injection
- the earlier quick `ionos_edyn_active=.false.` probe that reused `edyn-on`
  history restarts was indeed blocked by restart-history compatibility
  (`UI` missing from masterlist)
- however, a later **self-consistent isolated `edyn-off` seed + true
  continuation** now succeeds end-to-end to `00600`, so generic
  `CESM/WACCM-X` continuation is not universally broken
- a later **self-consistent isolated default `edyn-on` seed + true
  continuation** also succeeds end-to-end to `00600`
- a later **self-consistent isolated default `edyn-on` run with the real
  template bridge import files present** also succeeds end-to-end to `00600`
- therefore the remaining long-run blocker is now best described as the
  specific main-case `00300` restart lineage used in the production bridge
  workflow, not all continuation modes, not generic `edyn-on` by itself, and
  not bridge-import presence by itself
- a later restart-transplant matrix narrowed that still further:
  transplanting only the main-case `cam.r.2005-12-31-00300.nc` into an
  otherwise successful isolated restart set is already sufficient to reproduce
  the same `rank 0 SIGSEGV`
- the same matrix showed that transplanting only the main-case
  `cam.rs + cam.rh*` or only the main-case `cpl.r` does **not** reproduce the
  crash
- therefore the current long-run blocker is now best localized to the
  main-case `cam.r.2005-12-31-00300.nc` state file, not merely to the broader
  restart bundle
- a later variable-level compare of the two `cam.r.00300` files showed:
  identical headers, no `NaN/Inf` in key fields, but substantially stronger
  `U / V / PT` extremes in the failing main-case state while `DELP / Q / PS`
  remain nearly identical
- this makes the current best engineering diagnosis:
  the blocker is tied to the dynamic state embedded in the main-case
  `cam.r.2005-12-31-00300.nc`, especially `U / V / PT`, and that is consistent
  with the mapped `FV` dycore crash path
- two repair-oriented patch probes were then run:
  - patching only `U / V / PT` into the failing main-case `cam.r` still failed
  - patching `U / V / PT / Optm1 / DTCORE / DUCORE / DVCORE` still failed
- therefore the current best diagnosis is slightly narrower than before but not
  fully solved yet:
  the issue is in the broader dycore-related state embedded in the main-case
  `cam.r.2005-12-31-00300.nc`, not just in one tiny obvious field subset
- a later single-variable isolation narrowed it one more step:
  - `all3_plus_chem` failed while `all3_plus_chem_no_short` succeeded
  - `cam_restart_compare_all` showed the only differing `cam.r` variable
    between those two patched sets is `ShortLivedSpecie`
  - transplanting only main-case `ShortLivedSpecie` into the successful
    `all3_plus_chem_no_short` restart set was already sufficient to reproduce
    the same `00300 -> 00600` `rank 0 SIGSEGV`
- a later species-aware isolation narrowed that one more step:
  - `ShortLivedSpecie(pbuf_01764,lat,lon)` was confirmed to be
    `14 x 126 levels`, matching the `pp_waccm_ma` short-lived list
  - the species-aware compare shows the dominant block difference is
    species `12 = Op`
  - transplanting only species `12 = Op` from the main-case
    `ShortLivedSpecie` into the successful isolated lineage is already
    sufficient to reproduce the same `00300 -> 00600` `rank 0 SIGSEGV`
  - transplanting all the other `13` short-lived species while explicitly
    keeping `Op` from the successful isolated lineage still continues cleanly
    to `00600`
- a later repair-oriented replay then showed:
  patching only the `Op` species block in the original main-case
  `cam.r.2005-12-31-00300.nc` with the successful-lineage `Op` is already
  sufficient to repair the previously failing `00300 -> 00600` continuation
- a follow-on repaired-lineage continuation then showed the same minimal
  repair is not merely a one-step rescue:
  the repaired main-case lineage also continues cleanly from
  `00600 -> 00900`, writes `cam.r/cam.rs.2005-12-31-00900.nc`, and exits
  through `med_finalize`
- a second follow-on repaired-lineage continuation then extended that result:
  the same repaired main-case lineage also continues cleanly from
  `00900 -> 01200`, writes `cam.r/cam.rs.2005-12-31-01200.nc`, and again
  exits through `med_finalize`
- a third follow-on repaired-lineage continuation then extended it again:
  the same repaired main-case lineage also continues cleanly from
  `01200 -> 01500`, writes `cam.r/cam.rs.2005-12-31-01500.nc`, and again
  exits through `med_finalize`
- a later aggressive repaired-lineage chain then pushed the same repaired
  main-case lineage across five more successful true continuation segments:
  `01500 -> 01800 -> 02100 -> 02400 -> 02700 -> 03000`
  with each segment writing the next `cam.r/cam.rs` restart pair and exiting
  through `med_finalize`
- therefore the current best engineering diagnosis is now:
  the decisive trigger for the production-lineage continuation crash is the
  `Op` species block inside `ShortLivedSpecie` embedded in
  `cam.r.2005-12-31-00300.nc`
- a further pre-`00300` startup-window check on `2026-03-30` narrowed the
  timing one more step:
  - successful-isolated and failing-main-case startup histories at `00000`
    are still identical for `Op / UI / VI / WI / TElec / TIon`
  - by `00300`, those same ionosphere-facing fields have already diverged
    strongly in `cam.rh0` and `cam.rh2`
  - therefore the earliest known corruption window is now the first startup
    segment `00000 -> 00300`, not the initial state itself
- the same `2026-03-30` evidence also strongly suggests, as an inference from
  logs and timestamps, that the failing main-case `cam.r.00300` is a stale
  product of an older high-`epot` clamped startup lineage, whereas the later
  isolated successful seed uses a milder `~12 kV` external-`epot` startup path
  and therefore writes a different `00300` state
- that high-`epot` lineage inference was then pushed one step closer to causal
  validation with two isolated startup replays on `2026-03-30`:
  - replaying a `169.702 -> 150.000` clamped startup input set produced a
    new isolated `00300` state that is already much closer to the failing
    main-case than to the successful seed, but its isolated continuation
    failed by `te_map: Lagrangian levels are crossing` rather than the
    original `SIGSEGV`
  - replaying a more exact `178.793 -> 150.000` clamped startup input set
    produced a new isolated `00300` state that is extremely close to the
    failing main-case in both `cam.r` and ionosphere-facing `cam.rh0`
    diagnostics; for example:
    - `ShortLivedSpecie -> Op` vs main-case:
      `max_abs_diff = 1.75864739934566972e-03`
    - `cam.rh0 Op` vs main-case:
      `max_abs_diff = 1.0256851671754386e-03`
    - `cam.rh0 UI/VI/WI` vs main-case:
      `max_abs_diff = 66.82 / 18.51 / 6.20`
  - most importantly, isolated continuation from that replayed
    `178.793 -> 150.000` `00300` state reproduced the same failure class as
    the original main-case:
    it entered `med_phases_restart_read`, wrote the `00600` restart set,
    and then hit `rank 0 SIGSEGV` / `signal 11`

## Source-trace conclusion on 2026-03-30

On 2026-03-30, the source-path backtrace narrowed the likely bad-write point
one more step beyond the state-file evidence:

- `cam_comp.F90` shows the top-level order is:
  `cam_run1 = stepon_run1 -> ionosphere_run1 -> phys_run1`
  and
  `cam_run2 = phys_run2 -> stepon_run2 -> ionosphere_run2`
- inside `phys_run2 -> tphysac` in `physpkg.F90`, chemistry runs before the
  ionosphere-temperature block:
  `chem_timestep_tend` occurs earlier in the physics sequence, while
  `iondrag_calc` and `waccmx_phys_ion_elec_temp_tend` occur much later but
  still before `cam_run2` reaches `ionosphere_run2`
- therefore the late writer that can still overwrite `Op` after chemistry is
  not `chem_timestep_tend`, but `ionosphere_run2`
- `ionosphere_run2` in
  `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90`
  explicitly:
  - pulls `Op` either from advected state or from the short-lived pbuf slice
  - calls `d_pie_coupling`
  - writes the returned `opmmr_blck` directly back to either `state%q(:,:,ixop)`
    or the short-lived `ShortLivedSpecies` pbuf slice
  - also overwrites `OpTM1`
- the chemistry-side short-lived storage path is consistent with that:
  - `short_lived_species.F90` registers `ShortLivedSpecies` as a `global` pbuf
    field
  - `mo_gas_phase_chemdr.F90` reads it through `get_short_lived_species` and
    writes it back through `set_short_lived_species`
  - `chemistry.F90` maps `Op` into that short-lived list rather than the
    transported constituent list for this configuration
- the restart path is also now source-confirmed:
  - `restart_physics.F90` calls `pbuf_write_restart(File, pbuf2d)`
  - `physics_buffer.F90.in` shows `pbuf_write_restart` writes every
    `persistence_global` pbuf field to the CAM restart file
  - because `ShortLivedSpecies` is registered with `global` persistence, a bad
    `Op` stored there is naturally frozen into `cam.r.*`
- `charge_neutrality.F90` is not the direct culprit for `Op`:
  its `charge_fix_mmr` path adjusts electrons `e`, not `Op`
- the deepest currently traced write path is now:
  `ionosphere_run1 (MAGE epot injection) -> d_pie_set_external_epot ->
  cam_run2/ionosphere_run2 -> d_pie_coupling -> oplus_xport ->
  regrid_geo2phys_3d(op_geo -> opmmr) -> write back to ShortLivedSpecies/OpTM1`
- that path is physically plausible as the trigger:
  - `d_pie_coupling` converts `Op` from `mmr` to number density, runs
    electrodynamics and `oplus_xport`, converts back to `mmr`, and regrids to
    physics space
  - `oplus_xport` explicitly depends on ion drifts `ui/vi/wi`, neutral winds,
    `omega`, ambipolar diffusion, and the tridiagonal transport solve
  - the same file shows separate diagnostic terms for
    `electric field transport` and `wind transport`
- the current best source-level diagnosis is therefore:
  the most likely place where the failing `00300` lineage first diverges is not
  generic chemistry, but the late `WACCM-X` ionosphere transport path that
  overwrites short-lived `Op` after chemistry, especially under the older
  strong-`epot` startup forcing branch

The dedicated long-stability diagnostic note is:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_LONG_STABILITY_20260328.md`

The new self-consistent isolated `edyn-off` continuation controls are:

- first isolated seed root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260328_235136`
- manual true-continue verification on that seed:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260328_235136/continue_true.log`
- clean fully automated rerun:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260329_000102`

The matching self-consistent isolated default `edyn-on` continuation control is:

- clean fully automated rerun:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260329_000715`

The matching self-consistent isolated default `edyn-on` control with real
template bridge imports present is:

- clean fully automated rerun:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260329_001326`

The restart-transplant matrix that further isolates the blocker is:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_RESTART_TRANSPLANT_MATRIX_20260329.md`

The new causal-startup replay evidence is:

- `169.702 -> 150.000` isolated startup:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/causal_replays/causal_startup_169702_20260330a`
- `169.702` replayed continuation failure root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260330_causal169702_from00300`
- `178.793 -> 150.000` isolated startup:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/causal_replays/causal_startup_178793_20260330a`
- `178.793` replayed continuation failure root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260330_causal178793_from00300`
- supporting `ShortLivedSpecie` compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_maincase_vs_causal169702_20260330.txt`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_maincase_vs_causal178793_20260330.txt`
- supporting `cam.rh0` compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/rh0_compare_maincase_vs_causal178793_20260330.txt`

The supporting variable-level `cam.r` compare report is:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cam_r_compare_report_20260329.txt`

The supporting single-variable continuation proof is:

- patched restart set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_shortlived_only_from_maincase_20260329g`
- continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_shortlived_only`

The supporting species-level `ShortLivedSpecie -> Op` isolation is:

- species compare tool:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/tools/cam_shortlived_species_tool.c`
- case-env binary:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/tools/cam_shortlived_species_tool_caseenv`
- main-case vs successful-lineage species compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_maincase_vs_success_20260329.txt`
- `Op`-only patched restart set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_shortlived_op_only_from_maincase_20260329h`
- `Op`-only continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_op_only`
- `No-Op` patched restart set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_shortlived_no_op_from_maincase_20260329i`
- `No-Op` continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_no_op`
- main-case repaired-vs-main-case compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_maincase_repaired_vs_maincase_20260329.txt`
- main-case repaired all-variable compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cam_r_compare_all_maincase_vs_maincase_op_repaired_20260329.txt`
- main-case repaired restart set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/maincase_op_repaired_from_success_20260329j`
- main-case repaired continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_maincase_op_repaired`
- pre-`00300` startup-window compares:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/rh0_compare_maincase_vs_success_00000_20260330.txt`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/rh0_compare_maincase_vs_success_00300_20260330.txt`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/rh2_compare_maincase_vs_success_00300_20260330.txt`

The real file-mediated bidirectional loop has been executed successfully:

1. Real `kaiju/voltron.x` wrote a forward package from `MAGE/REMIX`:
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/voltron_waccmx_cesm_cycle_step1/waccmx_voltron_forward_package.h5`
2. Real `CESM/WACCM-X` consumed bridge-generated import files and completed a real `cesm.exe` run:
   `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run/manual_cesm_kaiju_cycle.log`
3. Real `CESM/WACCM-X` wrote updated conductance feedback files:
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/with_import_feedback`
4. That feedback was converted to a kaiju-compatible HDF5 feedback package:
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/waccmx_cesm_feedback_package.h5`
5. Real `kaiju/voltron.x` consumed the CESM-derived feedback and rewrote its contract:
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/voltron_waccmx_cesm_cycle_step2/waccmx_voltron_contract.txt`

As of 2026-03-26, the same real bridge has also passed additional regression
and degradation-branch tests:

- true absence of aurora import files:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/epot_only_true_20260326a`
- true absence of the external `epot` file:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/aurora_only_true_20260326a`
- stronger potential forcing:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x8_20260326a`
- stronger combined forcing:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x4_20260326a`
- compute-node parallel rerun of the same four tests under Slurm:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute`
- compute-node extreme forcing expansion:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme`
- compute-node bracket search around the `epot` failure threshold:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket`
- clamp-only mitigation tests:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_limiter`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_limiter150`
- smoothed-epot mitigation tests:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_all15`
- first real `neutral_rhs` feedback probe on a compute node:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/neutral_rhs_probe_compute/neutral_rhs_probe_A%A_T%a`

As of 2026-03-26, the same real bridge has also been rerun successfully with
an isolated mainline-style `kaiju` worktree whose non-MPI `voltron.x` now
opens the GEO feedback path at runtime for the `WACCMX_STUB` backend:

- isolated worktree root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_mainline`
- rebuilt binary:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_mainline/build/bin/voltron.x`
- completed real bridge run:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainline_geo_cycle_20260326a`

This run matters because it is no longer limited to the earlier experimental
`kaiju_waccmx_coupling` tree. The same file bridge now closes with a
mainline-based `voltron.x` worktree that can ingest GEO-side `neutral_rhs`
feedback.

The isolated mainline-style binary has also passed a compute-node probe under
Slurm:

- job:
  `4726857`
- node:
  `qhcn185`
- elapsed:
  `00:06:08`
- result root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_mainline/mainline_geo_probe_A4726857_T0`

As of 2026-03-26, the same GEO-feedback path has also been merged into the
actual main repository at:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju`

and validated with the rebuilt main-repo binary:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr/bin/voltron.x`

First smoke-validation run root:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_mainrepo_smoke/mainrepo_geo_smoke_20260326a`

Observed smoke artifacts:

- contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_mainrepo_smoke/mainrepo_geo_smoke_20260326a/waccmx_voltron_contract.txt`
- exchange summary:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_mainrepo_smoke/mainrepo_geo_smoke_20260326a/waccmx_voltron_exchange.md`
- forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_mainrepo_smoke/mainrepo_geo_smoke_20260326a/waccmx_voltron_forward_package.h5`

Observed contract values:

- Hemisphere 1:
  `SIGMAP 0.138 .. 17.678 S`, `SIGMAH 0.136 .. 11.635 S`,
  `NEUTRAL_DYNAMO_RHS absmax 41591.066 cm/s`
- Hemisphere 2:
  `SIGMAP 0.109 .. 10.062 S`, `SIGMAH 0.157 .. 8.839 S`,
  `NEUTRAL_DYNAMO_RHS absmax 43965.227 cm/s`

The same actual main-repo binary has now also completed a full real bridge
cycle through the standard driver:

- bridge driver:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`
- run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainrepo_geo_cycle_20260326a`
- bridge exit status:
  `0`
- bridge completion marker:
  `Bidirectional CESM<->kaiju file-coupled cycle completed.`

Observed full-cycle artifacts:

- step 1 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainrepo_geo_cycle_20260326a/step1_kaiju_forward/waccmx_voltron_forward_package.h5`
- CESM feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainrepo_geo_cycle_20260326a/waccmx_cesm_feedback_package.h5`
- step 2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainrepo_geo_cycle_20260326a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- step 2 exchange summary:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainrepo_geo_cycle_20260326a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- step 2 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainrepo_geo_cycle_20260326a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

Observed step 2 contract values:

- Hemisphere 1:
  `SIGMAP 0.138 .. 17.678 S`, `SIGMAH 0.136 .. 11.635 S`,
  `NEUTRAL_DYNAMO_RHS absmax 41591.066 cm/s`
- Hemisphere 2:
  `SIGMAP 0.109 .. 10.062 S`, `SIGMAH 0.157 .. 8.839 S`,
  `NEUTRAL_DYNAMO_RHS absmax 43965.227 cm/s`

## Evidence that the loop is closed

Step 1 kaiju contract, before CESM feedback:

- Hemisphere 1: `SIGMAP 5.000 .. 14.966 S`, `SIGMAH 2.000 .. 7.980 S`
- Hemisphere 2: `SIGMAP 5.000 .. 14.966 S`, `SIGMAH 2.000 .. 7.980 S`

Step 2 kaiju contract, after CESM feedback:

- Hemisphere 1: `SIGMAP 0.141 .. 17.577 S`, `SIGMAH 0.136 .. 11.628 S`
- Hemisphere 2: `SIGMAP 0.108 .. 10.063 S`, `SIGMAH 0.156 .. 8.838 S`

This proves the second real `voltron.x` run did not keep the default oval conductance. It ingested the CESM-derived feedback package.

## Evidence that `neutral_rhs` is now in the real loop

The first bridge version only reserved `neutral_rhs` as a zero placeholder.
As of 2026-03-26, that path has been replaced by a first real proxy:

- CESM feedback rank files now write six columns:
  `cid lat lon sigmap sigmah neutral_rhs`
- the converted feedback package now contains nonzero GEO-side
  `feedback_geo_north/neutral_rhs` and `feedback_geo_south/neutral_rhs`
- the second real `voltron.x` run now reports nonzero
  `NEUTRAL_DYNAMO_RHS absmax` values in its contract summary

Reproducible probe run:

- Slurm job:
  `4726230`
- completed result root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/neutral_rhs_probe_compute/neutral_rhs_probe_A%A_T%a`
- CESM rank feedback sample:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/neutral_rhs_probe_compute/neutral_rhs_probe_A%A_T%a/feedback/mage_waccmx_feedback_rank000000.txt`
- converted feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/neutral_rhs_probe_compute/neutral_rhs_probe_A%A_T%a/waccmx_cesm_feedback_package.h5`
- step 2 kaiju contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/neutral_rhs_probe_compute/neutral_rhs_probe_A%A_T%a/step2_kaiju_feedback/waccmx_voltron_contract.txt`

Observed values in that probe:

- rank feedback file column count:
  `6`
- sample first-row `neutral_rhs`:
  `-5.7723449815178610E+03`
- `feedback_geo_north/neutral_rhs_absmax`:
  `41591.06642700681`
- `feedback_geo_south/neutral_rhs_absmax`:
  `43965.226930983554`
- step 2 contract:
  - Hemisphere 1 `NEUTRAL_DYNAMO_RHS absmax = 41591.066 cm/s`
  - Hemisphere 2 `NEUTRAL_DYNAMO_RHS absmax = 43965.227 cm/s`

Current definition of this real proxy:

- CESM side quantity:
  Pedersen-conductance-weighted zonal neutral wind
- unit written to bridge:
  `cm/s`
- kaiju side mapping:
  GEO feedback `neutral_rhs` -> `NEUTRAL_WIND` slot in the experimental
  `WACCMX_STUB` backend

This means `neutral_rhs` is no longer a zero placeholder in the real bridge.
It is now a first-order real feedback proxy. What remains incomplete is the
final physical closure, not the basic data path.

## Evidence that the isolated mainline-style kaiju worktree now closes the GEO path

The isolated mainline-style worktree rerun completed through the same bridge
entry point:

- bridge driver:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`
- run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainline_geo_cycle_20260326a`
- bridge exit status:
  `0`
- bridge completion marker:
  `Bidirectional CESM<->kaiju file-coupled cycle completed.`

Step 1 contract, before CESM feedback:

- Hemisphere 1:
  `SIGMAP 5.000 .. 14.966 S`, `SIGMAH 2.000 .. 7.980 S`,
  `NEUTRAL_DYNAMO_RHS absmax 2491.476 cm/s`
- Hemisphere 2:
  `SIGMAP 5.000 .. 14.966 S`, `SIGMAH 2.000 .. 7.980 S`,
  `NEUTRAL_DYNAMO_RHS absmax 2491.476 cm/s`

Step 2 contract, after real CESM feedback:

- Hemisphere 1:
  `SIGMAP 0.138 .. 17.678 S`, `SIGMAH 0.136 .. 11.635 S`,
  `NEUTRAL_DYNAMO_RHS absmax 41591.066 cm/s`
- Hemisphere 2:
  `SIGMAP 0.109 .. 10.062 S`, `SIGMAH 0.157 .. 8.839 S`,
  `NEUTRAL_DYNAMO_RHS absmax 43965.227 cm/s`

Key artifacts:

- step 1 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainline_geo_cycle_20260326a/step1_kaiju_forward/waccmx_voltron_contract.txt`
- step 2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainline_geo_cycle_20260326a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- step 2 exchange summary:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainline_geo_cycle_20260326a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- step 2 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/mainline_geo_cycle_20260326a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

This shows that GEO-side `neutral_rhs` feedback is no longer confined to the
older experimental backend tree. It now participates in a full real bridge
cycle with the isolated mainline-style `voltron.x` worktree as well.

## Evidence that CESM response changed under MAGE input

Two real CESM runs were compared:

- With MAGE import files:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/with_import_feedback`
- Without MAGE import files:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/no_import_feedback`

Column-by-column comparison over all `13824` feedback rows:

- `changed_sigmap = 13824`
- `changed_sigmah = 13824`
- `sigmap_absmax = 14.631452122190241`
- `sigmah_absmax = 18.199177972255455`
- `sigmap_absmean = 0.801927794406084`
- `sigmah_absmean = 0.9792118427302425`
- `sigmap_absmedian = 0.006761064321084476`
- `sigmah_absmedian = 0.0004364470013804578`

So the real `CESM/WACCM-X` feedback changed everywhere when driven by the bridged `MAGE` input.

## What is complete vs incomplete

Complete now:

- Real `kaiju` main loop participation
- Real `CESM/WACCM-X` executable participation
- Real bidirectional exchange, mediated through files
- Real bidirectional exchange also revalidated with an isolated mainline-style
  `voltron.x` worktree that opens GEO-side `neutral_rhs` feedback at runtime
  for `WACCMX_STUB`
- Reproducible bridge scripts in:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge`
- Full end-to-end script-driven cycle completed successfully with the real bridge entry point
  - command path:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`
  - completed run root:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a`
  - step 1 forward package:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/step1_kaiju_forward/waccmx_voltron_forward_package.h5`
  - CESM feedback package:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/waccmx_cesm_feedback_package.h5`
  - step 2 feedback-ingested contract:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
  - step 2 feedback-ingested exchange summary:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
  - step 2 forward package after CESM feedback:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`
- Full end-to-end script-driven cycle re-run succeeded again from the same real entry point
  - completed run root:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a`
  - step 1 forward package:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/step1_kaiju_forward/waccmx_voltron_forward_package.h5`
  - CESM feedback package:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/waccmx_cesm_feedback_package.h5`
  - step 2 feedback-ingested contract:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
  - step 2 feedback-ingested exchange summary:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
  - step 2 forward package after CESM feedback:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`
- Real external `MAGE epot` validation under `CESM/WACCM-X`
  - validated log:
    `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run/manual_cesm_kaiju_cycle_fixepot_v3.log`
  - confirmed end marker:
    `med_finalize max rss=5432299520.0 MB`
  - no `MAGE epot size mismatch`
  - no `edyn_esmf_set2d_phys: Error return from ESMF_FieldGet, rc = 51`
  - output files written through:
    `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run/mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
- Real feedback-ingested second `voltron.x` run using the `fixepot_v3` CESM feedback package
  - feedback package:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/waccmx_cesm_feedback_package_fixepot_v3.h5`
  - second-run artifacts:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/voltron_waccmx_cesm_fixepot_v3_step2/waccmx_voltron_contract.txt`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/voltron_waccmx_cesm_fixepot_v3_step2/waccmx_voltron_exchange.md`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/voltron_waccmx_cesm_fixepot_v3_step2/waccmx_voltron_forward_package.h5`
- Re-run confirmation of the closed loop with changed post-feedback conductance
  - step 1 contract:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/step1_kaiju_forward/waccmx_voltron_contract.txt`
  - step 2 contract:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
  - step 1 conductance envelope:
    `SIGMAP 5.000 .. 14.966 S`, `SIGMAH 2.000 .. 7.980 S`
  - step 2 conductance envelope:
    `SIGMAP 0.138 .. 17.678 S`, `SIGMAH 0.136 .. 11.635 S`
- Regression/robustness coverage on the same real file bridge
  - `epot_only_true_20260326a`
    - CESM end markers:
      `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
      `med_finalize max rss=5431795712.0 MB`
    - no `size mismatch`, no `rc = 51`, no `MPI_ABORT`
    - step 2 envelope:
      `SIGMAP 0.138 .. 17.678 S`, `SIGMAH 0.136 .. 11.635 S`
  - `aurora_only_true_20260326a`
    - CESM end markers:
      `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
      `med_finalize max rss=5434707968.0 MB`
    - no `size mismatch`, no `rc = 51`, no `MPI_ABORT`
    - step 2 envelope:
      `SIGMAP 0.141 .. 17.577 S`, `SIGMAH 0.136 .. 11.628 S`
  - `stress_epot_x8_20260326a`
    - CESM end markers:
      `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
      `med_finalize max rss=5431762944.0 MB`
    - no `size mismatch`, no `rc = 51`, no `MPI_ABORT`
    - step 2 envelope:
      `SIGMAP 0.135 .. 17.810 S`, `SIGMAH 0.136 .. 11.646 S`
  - `stress_all_x4_20260326a`
    - CESM end markers:
      `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
      `med_finalize max rss=5431984128.0 MB`
    - no `size mismatch`, no `rc = 51`, no `MPI_ABORT`
    - step 2 envelope:
      `SIGMAP 0.136 .. 17.734 S`, `SIGMAH 0.136 .. 11.640 S`
- Compute-node parallel validation under Slurm
  - first array attempt:
    `job 4721803`
    failed with `OUT_OF_MEMORY` at `32G` per task
  - second array attempt:
    `job 4721810`
    completed successfully at `64G` per task
  - array script:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/run_aggressive_parallel_array.sbatch`
  - helper scripts:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/prepare_cesm_rundir_clone.sh`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_aggressive_parallel.sh`
  - completed compute-node result roots:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute/epot_only_true_A4721810_T0`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute/aurora_only_true_A4721810_T1`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute/stress_epot_x8_A4721810_T2`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute/stress_all_x4_A4721810_T3`
  - third array attempt:
    `job 4725083`
    extended the forcing range
    - `stress_all_x8` completed successfully
    - `stress_epot_x16` failed with CESM-side `SIGSEGV` on `rank 3`
  - fourth array attempt:
    `job 4725184`
    bracketed the `epot` instability threshold
    - `stress_epot_x10` completed successfully
    - `stress_epot_x12` completed successfully
    - `stress_epot_x14` failed with CESM-side `SIGSEGV` on `rank 3`
    - `stress_all_x12` completed successfully
  - fifth array attempt:
    `job 4725248`
    refined the threshold and pushed combined forcing further
    - `stress_epot_x13` completed successfully
    - `stress_all_x16` failed with CESM-side `SIGSEGV` on `rank 3`
  - current practical stability bracket:
    `epot x13` succeeds, `epot x14` fails, so the present threshold lies between them
  - current practical combined-forcing bracket:
    `all x12` succeeds, `all x16` fails
  - clamp-only mitigation result:
    even `184.390 -> 150.000` did not eliminate the `rank 3` failure
  - smoothed-epot mitigation result:
    `epot x14 smooth1/smooth2` succeeded and `all x14 smooth2` succeeded
  - next practical smoothed bracket:
    `epot x14.5 smooth2` succeeds, `epot x15 smooth2` aborts with
    `te_map: Lagrangian levels are crossing`, and `epot x16` still fails
    with `SIGSEGV`
  - next practical combined-forcing smoothed bracket:
    `all x14.5 smooth2` succeeds, `all x15 smooth2` aborts with `te_map`, and
    `all x16 smooth2` still fails with `SIGSEGV`
  - reporting-level integer summary:
    if we stop the bracket search here and report only integer multiples, then
    `epot x14` succeeds while `epot x15` fails, and `all x14` succeeds while
    `all x15` fails
  - long-stability continuation result:
    three independent long-run checks all failed at the first real
    `00300 -> 00600` continuation step, after entering
    `med_phases_restart_read` and after opening the new `00600` restart files:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_all_x14_smooth2_c4_20260328_190627`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_epot_x14_smooth2_c4_20260328_191116`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_baseline_x1_c1_20260328_191538`
    This shows the current blocker for multi-cycle stability is the
    continuation/restart path itself, not only the forcing amplitude
  - bridge-script robustness improvement:
    the forward/feedback converters and main bridge scripts now ignore
    `mage_waccmx_feedback_rank*_summary.txt` sidecars and only consume the real
    `rank000000.txt`-style payload files
  - additional compute-node result roots:
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_all_x8_A4725083_T1`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_epot_x16_A4725083_T0`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x10_A4725184_T0`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x12_A4725184_T1`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x14_A4725184_T2`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_all_x12_A4725184_T3`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_epot_x13_A4725248_T0`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_all_x16_A4725248_T1`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth/stress_epot_x14_smooth1_A4725607_T0`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth/stress_epot_x14_smooth2_A4725607_T1`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth/stress_all_x16_smooth2_A4725607_T2`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup/stress_epot_x15_smooth2_A4725660_T0`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup/stress_epot_x16_smooth2_A4725660_T1`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup/stress_epot_x16_smooth3_A4725660_T2`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup/stress_all_x14_smooth2_A4725660_T3`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_all15/stress_all_x15_smooth2_A4725676_T0`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x14p5_smooth2_20260328a`
    `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x14p5_smooth2_20260328a`
- No leftover `cesm.exe` or relevant `voltron.x` processes remained after the
  2026-03-26 regression batch

Still incomplete:

- This is not yet online `MPI` coupling like `voltron_mpi.x <-> tiegcm.x`
- The bridge still uses text/HDF5 files instead of a mediator-connected live in-memory exchange
- `neutral_rhs` is now only a first-order proxy, not yet a finalized
  neutral-dynamo closure

## 2026-03-30 update: `NSRHS geo_sidecar` zero-field blocker is fixed

The later `neutral_rhs / NSRHS` line had temporarily stalled at the conclusion
that live `geo_sidecar` runs completed but exported only a zero field.

That conclusion is now outdated.

The upstream issue was traced to CESM-side cache timing:

- `mage_waccmx_capture_conductance()` ran in `phys_run2`
- `d_pie_coupling()` updated `rhs_bothhem` later in `ionosphere_run2`
- so the original `NSRHS GEO sidecar` capture happened too early on the
  continuation path

The current CESM fix is:

- add `mage_waccmx_refresh_edyn_rhs()` in
  `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90`
- call it immediately after `d_pie_coupling(...)` in
  `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90`

After rebuilding CESM, the isolated continuation rerun

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh`

produced nonzero `edyn rhs` diagnostics on every rank.

Representative summaries:

- rank 0:
  - `edyn_rhs_absmax = 4.4036454298272066E+07`
  - `edyn_rhs_geo_absmax = 4.9739641809171423E+07`
- rank 3:
  - `edyn_rhs_absmax = 5.3296008092669755E+07`
  - `edyn_rhs_geo_absmax = 5.3296008092668504E+07`

The resulting bridge package

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/waccmx_cesm_feedback_package_postrefresh.h5`

now carries nonzero GEO-side `neutral_rhs`:

- `feedback_geo_north/neutral_rhs absmax = 5.32960080926685e+07`
- `feedback_geo_south/neutral_rhs absmax = 4.973964180917142e+07`

The final `Kaiju step2` rerun

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/kaiju_step2_postrefresh_rerun`

did write a new contract:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/kaiju_step2_postrefresh_rerun/waccmx_voltron_contract.txt`

and that contract shows:

- `SIGMAP/SIGMAH` updated normally
- `NEUTRAL_DYNAMO_RHS absmax` no longer zero
- the printed value overflowed the legacy `f10.3` format and appears as
  `**********`, which is consistent with the raw `~5e7` magnitude carried by
  the postrefresh package

So the state of the experimental `NSRHS` line is now:

- the previous zero-field blocker is fixed
- `CESM -> bridge -> Kaiju` now carries nonzero `geo_sidecar` end-to-end
- the next real problem is magnitude/unit calibration, not missing data or
  broken wiring

That calibration step has now also been partially advanced.

Using the new postrefresh source field, three short `phase2 NSRHS` probes were
run in:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a`

Packages:

- raw geo:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_transform_tests_20260330a/postrefresh_raw_geo.h5`
- coupler-like:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_transform_tests_20260330a/postrefresh_coupler_like.h5`
- crossmodel:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_transform_tests_20260330a/postrefresh_coupler_crossmodel.h5`

Probe workpoints:

- raw control:
  `scale = 0`
- coupler-like:
  `KAIJU_NSRHS_SCALE = 4.18378699684e5`
- crossmodel:
  `KAIJU_NSRHS_SCALE = 4.18378699684e5`

All three probes completed successfully.

Key results:

- raw control preserved the large direct package amplitude
  - H1 `NSRHS absmax = 5.3296E+07`
  - H2 `NSRHS absmax = 4.9740E+07`
- coupler-like stayed in the expected transformed corridor
  - H1 `NSRHS absmax = 1.2739E-06`
  - H2 `NSRHS absmax = 1.1889E-06`
- crossmodel stayed in the same corridor
  - H1 `NSRHS absmax = 1.2753E-06`
  - H2 `NSRHS absmax = 1.1902E-06`

The transformed workpoints also produced clear `POT` shifts relative to the raw
`scale=0` control, while remaining mutually very close:

- raw control:
  - North `POT = -13.1430 .. 10.9712 kV`
  - South `POT = -15.8848 .. 13.6946 kV`
- coupler-like:
  - North `POT = -9.40238 .. 18.1043 kV`
  - South `POT = -15.4911 .. 15.3800 kV`
- crossmodel:
  - North `POT = -9.39842 .. 18.1181 kV`
  - South `POT = -15.4908 .. 15.3819 kV`

This means the latest nonzero postrefresh source field is compatible with the
existing `phase2` workpoint logic. The open question is no longer whether
`postrefresh` can be used on the transformed branch. It is now which of the
nearly equivalent transformed branches should be kept as the main experimental
baseline for later `TIEGCM gnsrhs` semantic alignment.

That branch-selection question has now been narrowed further with a dedicated
three-point scan on the latest `postrefresh` crossmodel package:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_POSTREFRESH_XMODEL_SCALE_SCAN_20260330.md`

Result:

- `solver_to_tiegcm_coupler_crossmodel`
  remains a stable single-branch experimental baseline
- `KAIJU_NSRHS_SCALE = 4.18378699684e5`
  remains the most balanced workpoint among
  `1e5`, `4.18e5`, and `1e6`
- `1e5` is still visibly active but weaker
- `1e6` is still stable but already clearly stronger than desired for a
  baseline calibration point

## Reproducible entry point

Use:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`

The script now:

1. runs real kaiju until the forward artifacts exist
2. converts kaiju output to CESM import files
3. runs real CESM once
4. snapshots CESM feedback and converts it to kaiju HDF5 feedback
5. runs real kaiju again until the feedback-ingested artifacts exist
