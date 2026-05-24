# WACCM-X -> SAMI3 Runtime Map Dynamic Source Count

Date: 2026-05-25

## Scope

`scripts/pack_wxsami3_runtime_map.c` no longer hard-codes the WACCM-X/CAM
source column count as `13824`.

The packer now reads the ESMF weight-file source dimension:

```text
n_a
```

and writes that value into runtime-map header slot 8:

```text
header = magic, version, nz, nf, nlt, npoints, n_s, nsource
```

It also validates every ESMF `col` entry against the discovered source count.

## Why This Matters

The current validated online neutral prototype is f19:

```text
source grid = 144 x 96
nsource = 13824
```

For f09 or finer grids, this hard-coded value would be wrong even if the rest
of the ESMF weight file was valid.  The sender already reads `nsource` from the
runtime-map header, so the packer was the brittle point.

This change does not complete the f09/distributed-remap production work.  It
removes a concrete f19-only assumption from the runtime-map artifact schema.

## Validation

Syntax check with the available NetCDF module:

```bash
source /etc/profile.d/modules.sh
module load intel/netcdf/4.7.4/gcc8.5.0_ompi5.0.3
gcc $(nc-config --cflags) -fsyntax-only scripts/pack_wxsami3_runtime_map.c
```

Temporary f19 pack test:

```text
wrote runtime map: /tmp/wxsami3_runtime_map_dynamic_nsource_f19_20260525.bin
npoints = 3618816
n_s = 14475264
nsource = 13824
```

Header check:

```text
original header = (20260524, 1, 304, 124, 96, 3618816, 14475264, 13824)
dynamic test header = (20260524, 1, 304, 124, 96, 3618816, 14475264, 13824)
```

The temporary map itself is not committed.

## Evidence

Archived under:

```text
logs/waccmx_runtime_map_dynamic_nsource_20260525/
```
