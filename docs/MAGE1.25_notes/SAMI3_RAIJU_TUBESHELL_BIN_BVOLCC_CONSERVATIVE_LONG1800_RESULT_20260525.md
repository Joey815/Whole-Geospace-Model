# SAMI3 -> RAIJU TubeShell bVol-Binned Conservative 1800s Result

Date: 2026-05-25

## Scope

This run extends the TubeShell `bin_bvol_cc` mapping prototype from the earlier
short runtime smoke to an 1800 second paired baseline/prototype run.  It uses a
more conservative scalar-moment ingest than the earlier smoke:

```text
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_cc
runtime mapping = weights
density-mode = num
pressure-mode = ion
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 0.0
moments/useStateTioteForIngest = disabled
```

The purpose is to validate the traced TubeShell bVol-binned coverage/mask path
without simultaneously changing pressure, standard-deviation, or tiote
semantics.

## Run Result

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvolcc_conservative_long1800_20260525
```

Slurm result:

```text
jobid = 7671981
jobname = sami3_bvcc_l1800
state = COMPLETED
exit = 0:0
elapsed = 01:21:54
node = qhcn075
batch MaxRSS = 1179452K
```

Both baseline and prototype reached `Fin`:

```text
baseline_raiju_writes = 362
prototype_raiju_writes = 362
baseline_gamera_writes = 364
prototype_gamera_writes = 364
fatal marker matches = 0
slurm_run_complete = 1
```

## Product Gate

The SAMI3-derived moment product was:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvolcc_20260524.h5
```

Strict product checks passed:

```text
mapping_mode = weights
finite_all_fraction = 1.0
runtime_valid_fraction = 0.7021276595744681
extrapolated_fraction = 0.0
coverage_valid_positive = valid_min 4
weight_sum_valid_max_deviation = 1.1920928955078125e-07
Pavg/Davg/Pstd/Dstd masked values finite and nonnegative
tiote masked range = 0.8739513754844666 to 1.0004502534866333
```

The invalid target cells from the bVol-binned coverage map remain masked and
therefore preserve baseline values in the runtime adapter.

## Formula Checks

Final `raiCpl` restart formula checks against baseline and the SAMI3 moment
product were exact:

```text
Pavg_formula_max_abs = 0.0
Pavg_formula_max_rel = 0.0
Davg_formula_max_abs = 0.0
Davg_formula_max_rel = 0.0
Pstd_formula_max_abs = 0.0
Pstd_formula_max_rel = 0.0
Dstd_formula_max_abs = 0.0
Dstd_formula_max_rel = 0.0
```

Because this is a density-only conservative run, final direct `Pavg_in` did not
change from baseline:

```text
State/Pavg_in max_abs = 0.0
State/Pavg_in mean_abs = 0.0
State/Pavg_in recommended_mean = 0.00043784124116159
State/Pavg_in baseline_mean = 0.00043784124116159
```

The final density blend was applied only on valid mapped cells:

```text
State/Davg_in max_abs = 887.7487304687501
State/Davg_in mean_abs = 88.57160695606206
State/Davg_in recommended_mean = 88.62593804380671
State/Davg_in baseline_mean = 0.05433108774465306
```

No checked physics restart arrays contained non-finite values:

```text
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
```

## Final-State Response

Final restart comparison:

```text
State/Density max_abs = 4.396838290990813
State/Density mean_abs = 0.18501148428176631
State/Pressure max_abs = 0.0030697298556509045
State/Pressure mean_abs = 0.00010662231571474944
GAMERA/Gas0 max_abs = 4.258161539006221
GAMERA/Gas0 mean_abs = 0.019178709335169037
```

Final history-step comparison at `Step#361`:

```text
RAIJU/Davg_in mean_abs_delta = 71.58897279996772
RAIJU/Pavg_in mean_abs_delta = 0.004634867419346093
RAIJU/Density mean_abs_delta = 0.6714553590116555
RAIJU/Pressure mean_abs_delta = 0.004039306442793553
GAMERA/D mean_abs_delta = 0.5970180072751405
GAMERA/P mean_abs_delta = 0.014636947777434826
GAMERA/SrcD_COLD mean_abs_delta = 0.06050909335483642
GAMERA/SrcP_COLD mean_abs_delta = 6.441205327476358e-06
```

## Interpretation

This is now the strongest current runtime evidence for the conservative
SAMI3-derived scalar-moment path with traced TubeShell bVol-binned geometry.
The adapter can run for 1800 seconds with naturally invalid bVol-bin cells,
mask-gated density blending, exact formula checks, and no non-finite checked
RAIJU/GAMERA physics arrays.

This still remains prototype physics.  The current map uses `lon0` TubeShell
cell-center binning and Voltron `bvol_cc`; it is not yet a production
flux-tube-volume mapper.  `Pavg`, `Pstd`, `Dstd`, and `tiote` were intentionally
left disabled in this run so their semantics can be tested separately.

## Evidence

Archived under:

```text
logs/sami3_tubeshell_bin_bvolcc_conservative_long1800_20260525/
```

including XML decks, the Slurm script, both run logs, Slurm output,
`sacct_7671981.txt`, strict longrun validator JSON, moment-product validator
JSON, summary validator JSON, and `recommended_long1800_bvolcc_cons_summary.txt`.

Large HDF5 history/restart products are intentionally not committed. They
remain in the local runtime directory listed above.
