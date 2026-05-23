# SAMI3 to Voltron Plasma Moments Contract, 2026-05-23

Timestamp: 2026-05-23 04:00 CST

## Goal

Build the next adapter on the existing MAGE/Voltron moments path:

```text
SAMI3 plasma state -> Voltron TubeShell moments -> RAIJU/GAMERA diagnostics
```

The first milestone is diagnostic coupling only. It must not feed raw SAMI3 3-D
state directly into GAMERA equations, and it must not re-open the mistaken
WACCM-X -> SAMI3 live neutral payload branch.

## Verified SAMI3 State

Target SAMI3 tree inspected:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/work/sami3-3.22_online_mpi_openmpi
```

Grid and species facts:

- `numwork = 32`, `nf = 124`, `nz0 = 304`, `nz = 304`, `nl = 5`, and
  `nlt = numwork * (nl - 2) = 96` are set in `parameter_mod.f90:4-32`.
- `nion = 7` is set in `parameter_mod.f90:39-48`.
- SAMI3 ion order is:

```text
1 H+
2 O+
3 NO+
4 O2+
5 He+
6 N2+
7 N+
```

Primary plasma arrays:

- `deni(nz,nf,nl,nion)`, `ne(nz,nf,nl)`, and neutral `denn(...)` are declared
  in `variable_mod.f90:7`.
- `vsi(nz,nf,nl,nion)` is the ion parallel velocity array in
  `variable_mod.f90:10-11`.
- `te(nz,nf,nl)` and `ti(nz,nf,nl,nion)` are declared in
  `variable_mod.f90:12`.
- The restart gather arrays are `deniout`, `tiout`, `vsiout`, and `teout` in
  `sami3-3.22.f90:63-68`.

Output/restart availability:

- Regular output writes `deni1u.dat` to `deni7u.dat`, `deneu.dat`,
  `ti1u.dat` to `ti7u.dat`, `teu.dat`, and `vsi1u.dat` to `vsi7u.dat`
  from `output.f90:13-48` and `output.f90:211-311`.
- Restart writes `deni.rst`, `ti.rst`, and `te.rst` in
  `sami3-3.22.f90:640-652`.
- `vsi.rst` is opened but both `read(212) vsiout` and `write(212) vsiout` are
  commented out in `sami3-3.22.f90:158-170` and `sami3-3.22.f90:640-652`.
  Therefore adapter v1 must not depend on `vsi.rst`; use regular output or add
  a dedicated moments output later.

Geometry and averaging support:

- `vol(nz,nf,nl)` is defined as the SAMI3 cell volume/area proxy in
  `com3_bak.f90:71-76` and documented as "volume (i.e., area) of cell" in
  `com3_bak.f90:112`.
- SAMI3 perpendicular transport already treats `deni * vol`, `ti * vol`, and
  `te * vol` as conserved quantities, then divides by `vol` after updates in
  `exb_transport.f90:156-176` and `exb_transport.f90:304-350`.
- For the adapter, volume-weighted moments should use `vol` over the selected
  SAMI3 cells mapped to one Voltron tube/shell cell.

Unit notes:

- SAMI3 uses cgs constants: `bolt = 1.38044e-16`, `amu = 1.67252e-24`, and
  `evtok = 1.1604e+04` in `parameter_mod.f90:81-85`.
- Neutral source comments state densities in `cm-3`, and neutral winds are
  converted from `m/sec` to `cm/sec` in the official extract
  `neutral.f90:40-50` and `neutral.f90:70-71,135-136`.
- The density and temperature units below are therefore treated as code-backed
  inferences consistent with SAMI3 cgs use, not as a separate in-code unit
  annotation on `deni` itself:

```text
deni: #/cm^3, equivalent to #/cc
ti, te: K
pressure: dyn/cm^2 before conversion
```

## Verified Voltron/RAIJU Target Interface

MAGE target tree inspected:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju
```

Existing interface facts:

- `Tube_T` stores `avgP`, `avgN`, `stdP`, and `stdN` as
  `0:MAXTUBEFLUIDS`, with units documented as pressure `[nPa]` and density
  `[#/cc]` in `voltCplTypes.F90:40-47`.
- `TubeShell_T` stores shell-grid versions `avgP`, `avgN`, `stdP`, `stdN`, and
  `TioTe0` in `voltCplTypes.F90:79-92`.
- `MAXTUBEFLUIDS = 5` in `voltCplTypes.F90:12`, so the existing fixed-size
  TubeShell path cannot carry all seven SAMI3 ion species separately without a
  schema change.
- `BLK = 0` in `gdefs.F90:9`; existing code uses fluid index 0 as the aggregate
  MHD/black-box moment channel.
- Voltron computes existing moments with `FLThermo` and `FLStdev`, then assigns
  `bTube%avgP/stdP/avgN/stdN` in `tubehelper.F90:166-176`.
- Existing standard deviations are volume-weighted absolute standard
  deviations, not pre-normalized, as shown by `FLStdev` in
  `streamline.F90:369-427`.
- TubeShell restart I/O already writes and reads `avgP`, `avgN`, `stdP`,
  `stdN`, and `Tiote0` in `tubehelper.F90:475-532`.
- RAIJU allocates `Pavg/Davg/Pstd/Dstd` over `0:nFluidIn` in
  `raijuCplHelper.F90:72-82`.
- Voltron -> RAIJU maps `TubeShell%avgP/avgN/stdP/stdN/TioTe0` into
  `raiCpl%Pavg/Davg/Pstd/Dstd/tiote` in `raijuCplHelper.F90:143-150`.
- RAIJU copies `Pavg/Davg` directly but normalizes `Pstd/Dstd` by the copied
  mean in `raijuCplHelper.F90:211-219`.
- RAIJU state comments confirm final units: `Pavg [nPa]`, `Davg [#/cc]`,
  `Pstd/Dstd` normalized after ingestion, and `tiote` as `Ti/Te` in
  `raijuTypes.F90:439-449`.
- Typical local RAIJU XML uses `nFluidsIn="1"` and maps `fluidIn1 imhd="0"`
  to `flav="2"` (`F_HOTP`) with excess to plasmasphere, e.g.
  `run_inputs/tinyCase_smoke.xml:46-47`.

## Moment Contract

Adapter v1 should emit the current MAGE moments, not a new raw SAMI3 schema:

```text
avgP/stdP -> TubeShell%avgP/stdP -> raiCpl%Pavg/Pstd
avgN/stdN -> TubeShell%avgN/stdN -> raiCpl%Davg/Dstd
TioTe0    -> TubeShell%TioTe0    -> raiCpl%tiote
```

Recommended channel policy for v1:

- Channel `0` (`BLK`) is required and should carry total ion plasma moments:
  all SAMI3 ion species summed for density and pressure.
- Channel `1` may carry `H+` only if the downstream case has a matching
  `nFluidsIn >= 1` mapping. For the existing local RAIJU default, the XML maps
  MHD index 0 to hot protons, so the safest diagnostic path is still to keep
  channel 0 aggregate and mark the species interpretation explicitly.
- Do not attempt to expose all seven SAMI3 ions through TubeShell in v1 because
  `MAXTUBEFLUIDS=5` is a real local limit.

Per-cell formulas before Voltron-shell interpolation:

```text
n_s = deni(:,:,:,s)                         [#/cc]
p_s_nPa = deni(:,:,:,s) * ti(:,:,:,s) * 1.38044e-8
p_total_nPa = sum_s p_s_nPa
n_total = sum_s n_s
```

The pressure factor is:

```text
pressure_dyn_cm2 = n_cm3 * k_B_cgs * T_K
1 dyn/cm^2 = 1.0e8 nPa
k_B_cgs * 1.0e8 = 1.38044e-8
```

Weighted means over a mapped SAMI3 subset `M`:

```text
Davg = sum_M(w * n_total) / sum_M(w)
Pavg = sum_M(w * p_total_nPa) / sum_M(w)
```

Use `w = vol` when the adapter is operating on native SAMI3 grid cells. If the
first implementation maps through a pre-existing Voltron shell/cell sample
without available SAMI3 `vol`, it must label the result as simple-sampled and
not as a flux-tube-volume moment.

Absolute standard deviations to write into TubeShell:

```text
Dstd_abs = sqrt( sum_M(w * (n_total - Davg)^2) / sum_M(w) )
Pstd_abs = sqrt( sum_M(w * (p_total_nPa - Pavg)^2) / sum_M(w) )
```

Do not pre-normalize `Dstd` or `Pstd` in the adapter. RAIJU normalizes them when
copying into `State%Dstd/Pstd`.

Representative temperature ratio:

```text
Ti_eff = sum_M,sum_s(w * n_s * ti_s) / sum_M,sum_s(w * n_s)
Te_eff = sum_M(w * ne * te) / sum_M(w * ne)
tiote = Ti_eff / max(Te_eff, tiny)
```

If `ne` is unavailable from the chosen output artifact, use
`ne_proxy = sum_s deni_s` and record that proxy in the adapter metadata.

## Implementation Target

The lowest-risk implementation path is:

1. Read SAMI3 regular unformatted outputs, not `vsi.rst`.
   Required v1 inputs are `deni1u.dat` to `deni7u.dat`, `ti1u.dat` to
   `ti7u.dat`, `teu.dat`, `time.dat`, and a grid/weight source.
2. Build a sidecar adapter that computes `avgP/Davg/Pstd/Dstd/tiote` and writes
   either a TubeShell-compatible HDF5 group or an intermediate HDF5/NetCDF file
   that a small Voltron import hook can read.
3. Prefer reusing the existing TubeShell names and units:

```text
/TubeShell/avgP   [nPa]
/TubeShell/avgN   [#/cc]
/TubeShell/stdP   [nPa]
/TubeShell/stdN   [#/cc]
/TubeShell/Tiote0 [normalized]
```

4. Keep all GAMERA equation paths unchanged in v1. The first verification is
   that RAIJU/Voltron can read or compare the diagnostic moments and produce
   finite output fields.

## Open Items Before Coding

- Confirm the exact grid mapping from SAMI3 `(nz,nf,nlt)` to Voltron shell-grid
  `(theta, phi)` cells. Existing SAMI3 output has geographic and magnetic grid
  files such as `zaltu.dat`, `glatu.dat`, `glonu.dat`, `baltu.dat`,
  `blatu.dat`, and `blonu.dat`, written in `sami3-3.22.f90:2307-2327`.
- Decide whether v1 writes a true TubeShell restart HDF5 directly or an
  intermediate diagnostic file plus a reader. Direct TubeShell HDF5 is cleaner
  for RAIJU, but requires matching ShellGrid metadata.
- Decide whether the first diagnostic should be aggregate only (`BLK`) or also
  carry `H+` as channel 1. Aggregate only is safer with the existing local
  `nFluidsIn=1` cases.
- If true species-resolved SAMI3 -> RAIJU is required later, extend or replace
  `MAXTUBEFLUIDS=5` and add explicit RAIJU species mapping for at least `H+`
  and `O+`.

## Acceptance For Adapter v1

The v1 adapter is acceptable when:

- It reads a completed SAMI3 output directory and records the exact input files.
- It writes finite `Pavg`, `Davg`, `Pstd`, `Dstd`, and `tiote` fields.
- Units are `nPa`, `#/cc`, absolute std before RAIJU, and normalized `Ti/Te`.
- The adapter metadata states whether `vol` weighting or simple sampling was
  used.
- A Voltron/RAIJU diagnostic read path can inspect the fields without changing
  GAMERA physics.
