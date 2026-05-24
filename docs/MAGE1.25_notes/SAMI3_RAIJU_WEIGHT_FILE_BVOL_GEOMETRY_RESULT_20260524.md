# SAMI3 -> RAIJU Weight File Target Geometry

Date: 2026-05-24

## Scope

This checkpoint extends the explicit SAMI3-to-RAIJU mapping weight file so it
carries RAIJU target-side geometry diagnostics from the `raiCpl` template.

The sparse weights are still the prototype `l_mlt_separable` weights.  This
does not make the mapping a production Voltron traced-tube mapping.  It does
make the weight artifact aware of the RAIJU geometry that the runtime path
actually uses: `bvol`, `bvol_cc`, `topo`, and `Bmin`.

## Source Path Confirmed

The relevant runtime source path in `raijuCplHelper.F90` is:

```text
tubeShell2RaiCpl:
  tubeShell%bVol -> raiCpl%bvol
  raiCpl%bvol_cc(i,j) = toCenter2D(raiCpl%bvol(i:i+1,j:j+1))
  tubeShell%topo -> raiCpl%topo, converted to RAIJUOPEN/RAIJUCLOSED

raiCpl2RAIJU:
  State%bvol      = raiCpl%bvol
  State%bvol_cc   = raiCpl%bvol_cc only where all four topo corners are closed
  State%Pavg/Davg = raiCpl%Pavg/Davg only where all four topo corners are closed
```

So the target-cell closed mask must follow the same rule:

```text
closed_field_mask(j,i) = all four surrounding RAIJU topo corners are RAIJUCLOSED
```

## Code

Updated active files:

```text
scripts/sami3_moments/build_sami3_to_raiju_weights.py
scripts/sami3_moments/sami3_moments_to_raiju_diag.py
scripts/sami3_moments/validate_sami3_mage_moments.py
```

Archived collaboration snapshot:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/
```

## Weight File Schema

The mapping-weight file schema is now:

```text
schema_version = 2
mapping_mode = l_mlt_separable
physical_validity = prototype
```

The current generated file is archived under:

```text
logs/sami3_weightfile_bvol_geometry_20260524/sami3_to_raiju_weights_l_mlt_20260524.h5
```

New target-side datasets:

```text
/dst/bvol_corner        shape = (189, 46)
/dst/bvol_cc            shape = (188, 45)
/dst/topo_corner        shape = (189, 46)
/dst/topo_mask          shape = (189, 46)
/dst/Bmin_corner        shape = (3, 189, 46)
/dst/Bmin_mag_corner    shape = (189, 46)
/dst/Bmin_mag_cc        shape = (188, 45)
/dst/xyzMincc           shape = (3, 188, 45)
/dst/thcon_corner       shape = (189, 46)
/dst/phcon_corner       shape = (189, 46)
/dst/vaFrac_corner      shape = (189, 46)
/dst/Tb                 shape = (188, 45)
```

The quality group now uses the target topology-derived mask:

```text
/quality/closed_field_mask shape = (188, 45)
```

For the current tiny RAIJU template:

```text
closed_field_cell_count = 8460
closed_field_fraction = 1.0
bvol_cc_min = 0.00016075602010707862
bvol_cc_max = 32.672893056940694
```

This all-closed result is a property of this smoke template, not a general
assumption of the schema.

## Stage-2 Propagation

When the stage-2 adapter consumes the weight file through:

```text
--mapping-mode weights
--mapping-weight-file sami3_to_raiju_weights_l_mlt_20260524.h5
```

it now mirrors the target geometry into `/MappingQuality`:

```text
/MappingQuality/target_bvol_cc
/MappingQuality/target_bvol_corner
/MappingQuality/target_Bmin_mag_cc
/MappingQuality/target_Bmin_mag_corner
/MappingQuality/target_topo_corner
/MappingQuality/closed_field_mask
```

The Fortran runtime reader still ignores `/MappingQuality`; these fields are
for audit and plotting.

## Verification

Commands:

```text
python -m py_compile \
  scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  scripts/sami3_moments/build_sami3_to_raiju_weights.py \
  scripts/sami3_moments/validate_sami3_mage_moments.py

bash -n scripts/sami3_moments/run_sami3_mage_moments_smoke.sh

scripts/sami3_moments/run_sami3_mage_moments_smoke.sh \
  > analysis/sami3_weightfile_bvol_geometry_20260524.log 2>&1
```

Result:

```text
SAMI3 MAGE moments smoke passed
runtime_mapping=weights
runtime_mapping_quality finite_all_fraction=1.0
```

The moment mapping remains equivalent to the old inline `l_mlt` path:

```text
RaiCplMomentsOnly/Pavg  max_abs = 1.4901161193847656e-08  max_rel = 1.4901161193847656e-08
RaiCplMomentsOnly/Davg  max_abs = 0.001953125             max_rel = 1.1794265085779101e-07
RaiCplMomentsOnly/Pstd  max_abs = 2.9802322387695312e-08  max_rel = 2.9802322387695312e-08
RaiCplMomentsOnly/Dstd  max_abs = 0.00390625              max_rel = 1.189390305446135e-07
RaiCplMomentsOnly/tiote max_abs = 5.960464477539063e-08   max_rel = 5.960464477539063e-08
```

Overall:

```text
weight-file mapping equivalence max_abs = 0.00390625
weight-file mapping equivalence max_rel = 1.189390305446135e-07
```

The added geometry does not perturb the scalar moment mapping.

## Interpretation

The mapping artifact now carries the target geometry needed to audit the next
physical step.  The remaining blocker is no longer the file contract; it is the
actual source-to-target physics:

```text
replace the current l_mlt_separable sparse weights with weights built from
Voltron traced-tube topology and bvol-consistent flux-tube geometry
```

The next implementation step should use this schema as the stable interface and
replace only the weight-generation method.

## Evidence

Archived under:

```text
logs/sami3_weightfile_bvol_geometry_20260524/
```

including the schema-2 weight HDF5 file, metadata JSON, stage-2 diagnostic JSON,
and the smoke log.
