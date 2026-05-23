# SAMI3 -> RAIJU/GAMERA Physics Review And Next-Step Rules (2026-05-23)

This note absorbs the 2026-05-23 review of the current
SAMI3 -> RAIJU -> GAMERA path.  It is a route-control document for the next
work phase, not a claim that the current adapter is production physical
coupling.

## Bottom Line

The current engineering route is reasonable:

```text
packRaijuCoupler_RT
  -> tubeShell2RaiCpl
  -> applySami3RaiCplMoments
  -> raiCpl2RAIJU
```

The hook is in the right place because the SAMI3-derived values are applied
after the normal Voltron-to-RAIJU packing, so they are not immediately
overwritten by `tubeShell2RaiCpl`.  It also preserves the existing MAGE
geometry, topology, potential, `Bmin`, `bvol`, and downstream RAIJU/GAMERA
path.

This path must still be described as a diagnostic/runtime scalar-moment
adapter.  It is not yet production physical coupling, and it is not full
plasma-moment coupling.

The current bridge covers only these scalar quantities:

```text
Pavg
Davg
Pstd
Dstd
tiote
```

It does not yet pass bulk velocity, momentum density, anisotropic pressure
tensor, field-aligned flow, or ExB drift.  Public/internal wording should use:

```text
SAMI3-derived scalar plasma moments for RAIJU coupling
```

and should avoid:

```text
full SAMI3 plasma moments coupled to GAMERA
```

## Keep This Architecture

The current architecture is safer than either of these alternatives:

```text
Bad route 1: inject raw SAMI3 3-D plasma arrays directly into GAMERA
Bad route 2: modify GAMERA main equations so GAMERA reads SAMI3 directly
```

The intended architecture remains:

```text
SAMI3 multi-ion plasma
  -> reduce to shell/tube scalar moments accepted by RAIJU
  -> keep using the existing MAGE inner-magnetosphere coupling route
```

## Main Physics Risks

### 1. Davg Number Density Versus Mass Loading

The current stage-1 value is:

```text
Davg = field-line average of sum(n_i)  [#/cc]
```

That is total ion number density.  SAMI3 is multi-ion, with local species
order:

```text
H+, O+, NO+, O2+, He+, N2+, N+
```

If downstream RAIJU/GAMERA treats `Davg [#/cc]` as proton density for mass
loading, using only `sum(n_i)` underestimates heavy-ion mass.  Stage 1 should
therefore emit both number density and proton-equivalent mass density:

```text
Davg_num     = <sum(n_i)>           [#/cc]
Davg_massEq  = <sum(A_i * n_i)>     [proton-equivalent #/cc]
mu_eff       = Davg_massEq / Davg_num
```

with:

```text
A_i = 1, 16, 30, 32, 4, 28, 14
```

P0 must determine whether existing RAIJU/GAMERA `Davg` means:

```text
1. pure number density
2. proton-equivalent density
3. empirical shell density not directly equal to mass density
```

If `Davg` feeds GAMERA mass loading, the safer candidate is
`Davg_massEq`, not plain `sum(n_i)`.

### 2. Pavg Ion Pressure Versus Total Thermal Pressure

The current stage-1 value is ion pressure:

```text
Pavg = <sum(n_i * Ti_i * kB)>  [nPa]
```

If the downstream `Pavg` represents total thermal pressure, electron pressure
must also be available:

```text
P_i     = sum(n_i * kB * Ti_i)
P_e     = n_e * kB * Te
P_total = P_i + P_e
```

Stage 1 should emit:

```text
Pavg_i
Pavg_e
Pavg_total
```

Stage 2 should support:

```text
--pressure-mode ion
--pressure-mode total
--pressure-mode keep_original_plus_cold
```

Do not directly overwrite original MAGE `Pavg` with SAMI3 cold plasma pressure
until the original RAIJU/GAMERA pressure semantics are confirmed.  If original
`Pavg` includes hot plasma, RCM, IMAG, or ring-current pressure information,
full replacement would erase that structure.

Conservative first physical mode:

```text
Davg: replace or blend with SAMI3-derived density
Pavg: keep original MAGE pressure, or add a controlled cold correction

Pavg_new = Pavg_original + alpha * Pavg_SAMI3_cold
```

### 3. Pstd/Dstd Semantics

The current diagnostic values are computed as field-line standard deviations:

```text
Dstd = std_along_field_line(sum(n_i))
Pstd = std_along_field_line(sum(pressure_i))
```

RAIJU's original `Pstd/Dstd` may instead mean shell population spread,
Voltron tube-shell ensemble statistics, reconstruction statistics, or an
internal normalized perturbation shape parameter.

P0 must inspect the original `tubeShell2RaiCpl` and related Voltron/RAIJU
usage.  Until this is confirmed, runtime should allow these choices:

```text
1. keep original MAGE Pstd/Dstd
2. use SAMI3-derived Pstd/Dstd
3. alpha-blend original and SAMI3 values
```

Do not make SAMI3 `std over nz` a mandatory overwrite in physical runs.

### 4. Simple Along-Field Mean Is Smoke-Only

The current simple average over SAMI3 `nz` proves the data path but is not a
physical flux-tube average:

```text
<Q> = simple mean over nz
```

Physical mode should use flux-tube-volume weighting:

```text
<Q> = integral(Q dV) / integral(dV)
dV  proportional to ds / B

<Q> = sum(Q_k * delta_s_k / B_k) / sum(delta_s_k / B_k)
```

Stage 1 should expose explicit weighting modes:

```text
--weight-mode simple      # smoke only
--weight-mode ds_over_B   # physical prototype
--weight-mode voltron     # final target, aligned with MAGE/Voltron volume
```

HDF5 outputs should include:

```text
moment_weighting  = simple / ds_over_B / voltron
physical_validity = smoke_only / prototype / production
```

### 5. Index-Space Resize Is A Physical Blocker

Current diagnostic resampling:

```text
SAMI3 (124,96) -> RAIJU (45,188) by index-space resize
```

is acceptable for smoke testing only.  Production work needs a real geometry
map:

```text
SAMI3 nf,nlt
  -> L_src, MLT_src, footpoint, apex, Bmin
  -> RAIJU shell, MLT
  -> L/MLT/flux-tube geometry interpolation
```

Minimum requirements:

```text
1. MLT-periodic interpolation and 0/24 seam handling
2. L-shell or shell-coordinate interpolation
3. closed-field mask
4. extrapolation flag
5. mapping coverage diagnostics
```

Recommended independent map product:

```text
sami3_to_raiju_weights.h5

/src/L
/src/MLT
/src/nf
/src/nlt

/dst/L
/dst/MLT
/dst/shell
/dst/mlt_index

/map/src_index
/map/dst_index
/map/weight

/quality/closed_field_mask
/quality/extrapolation_flag
/quality/coverage_count
```

Stage 2 should eventually do:

```text
SAMI3 moments(nf,nlt)
  -> apply geometry weights
  -> RAIJU moments(shell,mlt)
```

instead of index-space resizing.

## Stage-1 Diagnostics To Add

Stage 1 should be extended before adding more runtime coupling variables.  The
next diagnostic payload should include:

```text
Davg_num
Davg_massEq
mu_eff

Pavg_i
Pavg_e
Pavg_total

Ti_eff
Te_eff
tiote

f_H
f_O
f_He
f_NO
f_O2
f_N2
f_N
f_molecular
```

`deneu.dat` should be used as quality control if it is present:

```text
ne_file  = deneu
ne_sum   = sum(n_i)
rel_diff = (ne_file - ne_sum) / ne_sum
```

If `deneu.dat` is absent, use:

```text
ne = sum(n_i)
```

Large `ne_file` versus `ne_sum` mismatch should be treated as a diagnostic
warning for possible unit, species-order, dimension, time-index, or boundary
handling problems.

## Unit Rules

Stage 1 should make temperature units explicit:

```text
--temperature-unit K|eV
```

If temperature is in Kelvin:

```text
P[nPa] = n[#/cc] * T[K] * 1.380649e-8
```

If temperature is in eV:

```text
P[nPa] = n[#/cc] * T[eV] * 1.602176634e-4
```

HDF5 attributes should record:

```text
density_unit        = cm^-3
temperature_unit    = K or eV
pressure_unit       = nPa
pressure_conversion = explicit formula used
```

## Runtime Blending And Guards

The current full overwrite behavior is useful for smoke testing.  Physical
runtime mode should use per-variable blending:

```text
X_new = (1 - alpha) * X_original + alpha * X_SAMI3
```

Required controls:

```text
use_sami3_raicpl_moments
sami3_alpha_Davg
sami3_alpha_Pavg
sami3_alpha_Dstd
sami3_alpha_Pstd
sami3_alpha_tiote
sami3_density_floor
sami3_pressure_floor
sami3_tiote_min
sami3_tiote_max
```

Recommended early settings:

```text
alpha_Davg = 1.0
alpha_Pavg = 0.0 or 0.2
alpha_std  = 0.0
```

Runtime modes to support:

```text
density-only coupling
density + tiote coupling
density + cold pressure correction
full overwrite, smoke or upper-bound test only
```

Always enforce finite-value checks, floors, and `tiote` bounds before applying
the values to RAIJU state.

## Revised Priority

### P0: Moment-Semantics Audit

Audit the actual MAGE/RAIJU/GAMERA meaning and downstream use of:

```text
Davg
Pavg
Dstd
Pstd
tiote
```

Questions:

```text
Does Davg feed number density, proton-equivalent mass loading, or an empirical shell density?
Does Pavg represent cold pressure, hot/ring-current pressure, or total pressure?
What is the original construction and use of Pstd/Dstd?
Is tiote used to reconstruct Ti, Te, or only as a diagnostic/control factor?
```

Deliverable:

```text
SAMI3_RAIJU_moment_semantics_20260523.md
```

### P1: Extended Stage-1 Diagnostics

Add number/mass-equivalent densities, ion/electron/total pressures, effective
temperatures, species fractions, `deneu.dat` QC, explicit temperature-unit
handling, and HDF5 validity attributes.

### P2: Flux-Tube-Volume Weighting

Demote simple `nz` mean to smoke mode.  Implement at least `ds/B` weighting,
then align final weighting with Voltron `bvol` semantics.

### P3: L/MLT Geometry Mapping

Replace index-space resize with SAMI3-to-RAIJU geometry weights.  The first
physical map must handle MLT periodicity, shell/L interpolation, closed-field
masking, extrapolation flags, and coverage diagnostics.

### P4: Runtime Blending And Component Switches

Add per-variable alpha controls, floors, `tiote` limits, and selectable
coupling modes.  Keep alpha-zero exact-baseline behavior as a hard regression
test.

## Verification Matrix

Minimum run set:

```text
Run 0: baseline MAGE, no SAMI3
Run 1: SAMI3 adapter, alpha=0
Run 2: SAMI3 density only, alpha_D=1, alpha_P=0
Run 3: SAMI3 density + cold pressure correction, alpha_D=1, alpha_P=0.2
Run 4: full overwrite, alpha=1, smoke/upper-bound only
```

Check:

```text
RAIJU Pavg/Davg maps
Davg_num versus Davg_massEq
Pavg_i versus Pavg_total
mu_eff
f_O, f_H, f_molecular
GAMERA inner-magnetosphere rho
GAMERA Alfven speed
GAMERA pressure
NaN/Inf/floor hits
```

Regression expectations:

```text
alpha=0 must exactly return to baseline
model response should change continuously as alpha increases
mapping must not show MLT seam errors
mapping must not reverse shell order
mapping must not flip dawn/dusk
```

## Operating Rule For Next Work

Do not start by adding more SAMI3 variables.  The next useful work is:

```text
1. audit RAIJU/GAMERA semantics for Pavg/Davg/Pstd/Dstd/tiote
2. make Davg number-density and mass-equivalent modes explicit
3. make Pavg ion/electron/total/cold-correction modes explicit
4. replace simple nz averaging with flux-tube-volume weighting
5. replace index-space resize with L/MLT/flux-tube geometry mapping
```

The engineering chain is in acceptable shape.  The current highest risk is
whether the values being passed through `Pavg/Davg/Pstd/Dstd/tiote` are the
physical quantities RAIJU/GAMERA actually expects.
