# SAMI3 -> RAIJU tiote Debug Output Result

Date: 2026-05-25

## Scope

This is a short diagnostic smoke to verify direct `State%tiote` visibility in
RAIJU output.  No Fortran change was required: `raijuIO.F90` already writes
`tiote` when RAIJU debug output is enabled.

Runtime settings:

```text
tFin = 11.5 s
RAIJU/output doDebug = T
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
moments/useStateTioteForIngest = T
```

## Run Result

```text
jobid = 7673602
jobname = sami3_tiote_dbg
state = COMPLETED
exit = 0:0
elapsed = 00:01:04
node = qhcn075
batch MaxRSS = 1197564K
```

## Direct tiote Evidence

The debug `raiju.h5` product contains `tiote` at the last history step:

```text
last_step = Step#3
last_step_keys_with_tiote = ["tiote"]
tiote_shape = [180, 37]
tiote_finite = true
tiote_min = 0.8914262056350708
tiote_max = 4.0
tiote_nondefault_count = 4680
```

The source product gate remained:

```text
product_tiote_mask_count = 5940
product_tiote_masked_min = 0.8739513754844666
product_tiote_masked_max = 1.0004502534866333
```

The RAIJU debug output shape is the local non-ghost output domain, so it is not
a direct shape match to the full product mask.  The key result is that
`State%tiote` is directly visible without a Fortran code change, making future
tiote diagnostics stronger than log-only evidence.

## Evidence

Archived under:

```text
logs/sami3_tubeshell_bin_bvolcc_tiote_debug_20260525/
```

including XML, Slurm script, runtime log, Slurm output, sacct output, and
`validate_tiote_debug_output.json/txt`.
