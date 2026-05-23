# SAMI3 -> Voltron/RAIJU Moments Adapter Result (2026-05-23)

## Goal

Finish the first usable SAMI3 -> MAGE plasma moments adapter path without
modifying the original `kaiju` tree:

```text
SAMI3 regular output
  -> Pavg/Davg/Pstd/Dstd/tiote
  -> Voltron TubeShell field-name view
  -> RAIJU coupler/state diagnostic view
```

The work was done only in this copied tree:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523
```

The original tree remains:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju
```

## Implemented

New files in the copied tree:

```text
scripts/sami3_moments/sami3_to_voltron_moments.py
scripts/sami3_moments/sami3_moments_to_raiju_diag.py
scripts/sami3_moments/validate_sami3_mage_moments.py
scripts/sami3_moments/run_sami3_mage_moments_smoke.sh
scripts/sami3_moments/README.md
src/voltron/modelInterfaces/sami3MomentsAdapter.F90
analysis/sami3_moments_stubpayload_20260523.h5
analysis/sami3_moments_stubpayload_20260523.json
analysis/sami3_voltron_raiju_diag_stubpayload_20260523.h5
analysis/sami3_voltron_raiju_diag_stubpayload_20260523.json
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_20260523.h5
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_20260523.json
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.h5
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.json
analysis/runtime_ingest_smoke_20260523/
```

Modified files in the copied tree:

```text
src/base/io_xml_input.F90
src/base/types/volttypes.F90
src/voltron/modelInterfaces/raijuCplHelper.F90
```

`io_xml_input.F90` was corrected so XML string values are assigned directly
from the parser buffer.  This fixes string values beginning with `/`, which
otherwise list-directed Fortran `read(buf,*)` treats as end-of-record.  The
runtime SAMI3 HDF5 file path and `/RaiCplMomentsOnly` group both need this.

`sami3_to_voltron_moments.py` reads SAMI3 regular output:

```text
deni1u.dat ... deni7u.dat
ti1u.dat   ... ti7u.dat
teu.dat
```

and writes:

```text
/moments/Pavg   nPa
/moments/Davg   #/cc
/moments/Pstd   nPa, absolute
/moments/Dstd   #/cc, absolute
/moments/tiote  normalized Ti/Te
```

`sami3_moments_to_raiju_diag.py` reads the moments HDF5 and writes:

```text
/Voltron/avgP
/Voltron/avgN
/Voltron/stdP
/Voltron/stdN
/Voltron/Tiote0
/TubeShellMomentsOnly/avgP
/TubeShellMomentsOnly/avgN
/TubeShellMomentsOnly/stdP
/TubeShellMomentsOnly/stdN
/TubeShellMomentsOnly/Tiote0
/RAIJU_Coupler/Pavg
/RAIJU_Coupler/Davg
/RAIJU_Coupler/Pstd
/RAIJU_Coupler/Dstd
/RAIJU_Coupler/tiote
/RaiCplMomentsOnly/Pavg
/RaiCplMomentsOnly/Davg
/RaiCplMomentsOnly/Pstd
/RaiCplMomentsOnly/Dstd
/RaiCplMomentsOnly/tiote
/RAIJU_State/Pavg
/RAIJU_State/Davg
/RAIJU_State/Pstd
/RAIJU_State/Dstd
/RAIJU_State/tiote
```

`sami3MomentsAdapter.F90` provides Fortran read hooks:

```text
readSami3TubeShellMoments(tubeShell, ResF, gStrO)
readSami3RaiCplMoments(raiCpl, ResF, gStrO)
```

`raijuCoupler_T` now stores a default-off XML hook under `Kaiju/RAIJU`:

```xml
<sami3Moments doIngest="true"
              file="/path/to/sami3_voltron_raiju_diag.h5"
              group="/RaiCplMomentsOnly"/>
```

Existing runs are unchanged unless `sami3Moments/doIngest` is explicitly true.
When enabled, `raijuCpl_init` parses and checks the input file.  The actual
read is applied in `packRaijuCoupler_RT` after the usual `tubeShell2RaiCpl`
packing and before `raiCpl2RAIJU`, so the SAMI3 moments are not immediately
overwritten by the standard Voltron-to-RAIJU pack.

The channel-array shape is:

```text
(nf, nlt, nFluidIn + 1) = (124, 96, 1)
```

for the verified default `--n-fluid-in 0` run.

`TubeShellMomentsOnly` uses the fixed MAGE TubeShell moment slot count:

```text
(nf, nlt, MAXTUBEFLUIDS + 1) = (124, 96, 6)
```

The local common `nFluidIn=1` allocation was also smoke-tested.  In that
diagnostic product, channel 0 contains the bulk SAMI3 moment and channel 1 is a
zero placeholder:

```text
RAIJU_State/Pavg shape = (124, 96, 2)
channel 0 mean         = 0.7830304503440857
channel 1 max abs      = 0.0
```

For runtime `ReadInSGV` ingestion, `/RaiCplMomentsOnly` can also be written in
the Fortran-compatible HDF5 order inferred from a real `raiCpl` template:

```text
template output Pavg shape = (2, 188, 45)  # HDF5 order: channel, j, i
Fortran target shape       = (45, 188, 2)  # i, j, channel
```

This runtime-layout product is:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.h5
```

## Verified Run

Input SAMI3 smoke directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000
```

Stage 1:

```bash
/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/sami3_to_voltron_moments.py \
  /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000 \
  --out /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523 \
  --format hdf5
```

Stage 2:

```bash
/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523.h5 \
  --out /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_20260523 \
  --n-fluid-in 0
```

Stage 2 runtime-layout product for the current RAIJU smoke grid:

```bash
/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523.h5 \
  --n-fluid-in 1 \
  --out /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.h5 \
  --raicpl-template /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_smoke_20260523/sami3_moments_base_control.raiCpl.Res.00000.h5
```

Numerical validation from the verified run:

```text
Pavg: min=0.004729345440864563 max=2.0364253520965576 mean=0.7830304503440857
Davg: min=1641.177490234375 max=109530.53125 mean=49818.8671875
Pstd absolute: min=0.0018463247688487172 max=2.7519729137420654 mean=1.2812246084213257
Dstd absolute: min=585.6715087890625 max=141351.25 mean=75490.8046875
tiote: min=0.13054083287715912 max=1.0003948211669922 mean=0.9015442132949829
RAIJU_State.Pstd normalized: min=0.3531407846198924 max=1.9337904320821773 mean=1.455078550979336
RAIJU_State.Dstd normalized: min=0.3521828148046795 max=1.7525325005393901 mean=1.3428616555745496
```

All required arrays were finite for the tested sample:

```text
finite = 11904 / 11904
```

The one-command smoke test passed:

```bash
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/run_sami3_mage_moments_smoke.sh
```

It regenerates stage 1, regenerates stage 2 for `nFluidIn=0` and `nFluidIn=1`,
and validates units, shapes, bulk-channel values, `TubeShellMomentsOnly`
6-channel layout, and RAIJU normalized standard deviations.

The Fortran read hook was syntax-checked:

```bash
/apps/support/intel_spr_rocky8.9/oneapi/2023.2.0/compiler/2023.2.0/linux/bin/intel64/ifort \
  -c \
  -I/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr/modules \
  -I/apps/support/intel_spr_rocky8.9/hdf5/1.13.0/intel2023.2_impi/include \
  -module /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/fortran_check \
  -o /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/fortran_check/sami3MomentsAdapter.o \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/src/voltron/modelInterfaces/sami3MomentsAdapter.F90
```

The compile check exited cleanly.

A standalone GR-style build was also configured from the copied tree:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523
```

Configuration required the HDF5 include path explicitly:

```bash
source /apps/support/intel_spr_rocky8.9/oneapi/2023.2.0/setvars.sh >/dev/null 2>&1
/apps/support/intel_spr_rocky8.9/cmake/3.26.3/bin/cmake \
  -S /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523 \
  -B /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523 \
  -DCMAKE_Fortran_COMPILER=/apps/support/intel_spr_rocky8.9/oneapi/2023.2.0/compiler/2023.2.0/linux/bin/intel64/ifort \
  -DCMAKE_C_COMPILER=/usr/bin/cc \
  -DHDF5_Fortran_COMPILER_EXECUTABLE=/apps/support/intel_spr_rocky8.9/hdf5/1.13.0/intel2023.2_impi/bin/h5pfc \
  -DCMAKE_Fortran_FLAGS=-I/apps/support/intel_spr_rocky8.9/hdf5/1.13.0/intel2023.2_impi/include \
  -DENABLE_MPI=OFF \
  -DENABLE_OMP=ON \
  -DENABLE_MKL=OFF \
  -DALLOW_INVALID_COMPILERS=ON
```

The following build targets completed, including after the XML hook was added:

```bash
/apps/support/intel_spr_rocky8.9/cmake/3.26.3/bin/cmake \
  --build /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523 \
  --target voltlib -j 8

/apps/support/intel_spr_rocky8.9/cmake/3.26.3/bin/cmake \
  --build /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523 \
  --target voltron.x -j 8
```

Build evidence:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/modules/sami3momentsadapter.mod
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/src/voltron/libvoltlib.a
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/bin/voltron.x
```

## Runtime Voltron/RAIJU Ingest Smoke

Runtime smoke directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_smoke_20260523
```

The runtime XML is:

```text
tinyCase_sami3_moments.xml
```

It enables the default-off hook:

```xml
<sami3Moments doIngest="T"
              file="/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.h5"
              group="/RaiCplMomentsOnly"/>
```

Interactive OpenMP runs require a large worker stack for this local smoke:

```bash
export OMP_NUM_THREADS=8
export KMP_STACKSIZE=512M
export OMP_STACKSIZE=512M
```

Without that, the base control smoke also segfaults in `kaiomp::CheckStack`;
that failure is unrelated to the SAMI3 adapter.

The enabled runtime smoke completed:

```text
model.log contains:
SAMI3 moments ingest applied after RAIJU realtime pack
SAMI3 moments Pavg(0) min/max: 0.004738224670290947 2.01816010475159
SAMI3 moments Davg(0) min/max: 1641.24194335938 108565.023437500
SAMI3 moments tiote min/max: 0.131028518080711 1.00037968158722
Fin
```

The output `raiCpl` restart matches the input runtime moments exactly for the
four persisted coupler arrays:

```text
output = runtime_ingest_smoke_20260523/sami3_moments_smoke.raiCpl.Res.00000.h5
input  = analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.h5:/RaiCplMomentsOnly

Pavg max_abs_diff = 0.0
Davg max_abs_diff = 0.0
Pstd max_abs_diff = 0.0
Dstd max_abs_diff = 0.0
```

## Compatibility Notes

This is a diagnostic adapter product, not a complete production restart.

It preserves the existing MAGE field semantics:

```text
Voltron stdP/stdN and RAIJU_Coupler Pstd/Dstd are absolute.
RAIJU_State Pstd/Dstd are normalized by Pavg/Davg, matching raiCpl2RAIJU.
```

It intentionally does not change GAMERA equations and does not write a full
`TubeShell` or `raiCpl` restart.  A production restart still needs ShellGrid
topology, magnetic geometry, potentials, masks, timing, and real traced-tube
weights.

If no `--weight-file` is supplied, stage 1 uses a simple along-field mean over
SAMI3 `nz`.  That is valid for diagnostics but must not be called a true
Voltron flux-tube-volume moment.

## Original Tree Check

The original tree did not receive the new adapter directory or output products:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/scripts/sami3_moments  absent
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/analysis/sami3*         absent
```
