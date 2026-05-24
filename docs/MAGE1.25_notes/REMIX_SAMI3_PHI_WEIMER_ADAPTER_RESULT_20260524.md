# REMIX -> SAMI3 Phi-Weimer Adapter Result

Date: 2026-05-24 CST

## Goal

Start the REMIX -> SAMI3 electric-potential path without changing SAMI3's main
transport equations.  The first implementation targets SAMI3's existing
external-potential route:

```text
MAGE/REMIX POT[kV]
-> SAMI3 phi_weimer.inp
-> potential.f90:weimer
-> potpphi
-> exb(hrut, phi)
```

This is an offline adapter and format validator.  It is not yet live REMIX
forcing inside the online MPI loop.

## Source-Code Audit Result

Relevant SAMI3 code path:

```text
sami3-3.22.f90:
  master receives hipcp/hihcm/hipcphi/hid* from workers
  master calls potpphi(...) and sends phi(nnx,nny) back to workers
  workers call exb(hrut, phi)

potential.f90:
  potpphi adds dphi + corotation + Volland/Stern + phi_weimer
  if lweimer is true, weimer(...) reads phi_weimer.inp

exb_transport.f90:
  exb calls vexb_phi(phi), applies altitude taper and vexb_max clipping,
  then uses vexbp/vexbs/vexbh for perpendicular transport
```

So the least invasive REMIX entry is `phi_weimer.inp`, not a direct overwrite
of `vexb_*`.

## Added Adapter

New script:

```text
scripts/remix_sami3/remix_pot_to_sami3_phi_weimer.py
```

Input:

```text
waccmx_voltron_forward_package.h5:/NORTH_APEX/POT
units: kV
source grid: 45 x 360 REMIX/APEX high-latitude grid
theta range: 0..45 deg colatitude
magnetic latitude range: 45..90 deg
```

Target:

```text
SAMI3 weimer_grid.dat
nlat = nfp1 = 125
nlon = nlt + 1 = 97
target mlat range = 1.87674153..88.9908981 deg
target mlon range = 0..360 deg
```

Mapping policy:

```text
longitude: periodic interpolation
latitude: interpolation from REMIX magnetic latitude to SAMI3 Weimer latitude
target latitudes below the REMIX source minimum are set to zero by default
unit conversion: phi_statV = POT_kV * 1000 / 300
binary format: gfortran-style sequential unformatted records
static packet records: hour0, phi(nfp1,nlt+1), valid_until_hour
```

The low-latitude zero fill is intentional for this prototype because the REMIX
export package only carries the high-latitude shell-grid cap.  It avoids
extrapolating high-latitude potential deep into SAMI3's lower-latitude Weimer
grid.

## Validation Run

Command:

```text
/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  scripts/remix_sami3/remix_pot_to_sami3_phi_weimer.py \
  --input /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/voltron_waccmx_file_clean_exit/waccmx_file_clean_exit_20260512a/waccmx_voltron_forward_package.h5 \
  --group NORTH_APEX \
  --weimer-grid /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/weimer_grid.dat \
  --output logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.inp \
  --summary-json logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.json \
  --diagnostic-h5 logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static_diag.h5
```

Outputs:

```text
logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.inp
logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.json
logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static_diag.h5
logs/remix_sami3_phi_weimer_20260524/run_remix_pot_to_sami3_phi_weimer.log
```

Checks:

```text
phi_kV shape: 125 x 97
phi_kV min/max/mean: -13.046549885448659 / 10.838320313501898 / -0.07204556894533992
phi_statV min/max/mean: -43.4884996181622 / 36.12773437833966 / -0.24015189648446636
finite count: 12125
NaN count: 0
low-lat zero-filled target rows: 89
readback hour0: 0.0
readback valid_until_hour: 1.0000000150474662e+30
readback phi max_abs_diff: 1.8859540276139342e-06 statV
```

The first record markers also match the expected sequential-unformatted layout:

```text
record 1 length = 4 bytes
record 2 length = 48500 bytes = 125 * 97 * 4
```

## Current Limitation

This adapter proves the file-format and first-order grid bridge only.  It does
not yet prove production REMIX -> SAMI3 electrodynamic consistency.

Known limitations:

```text
uses NORTH_APEX only by default
does not yet handle a time sequence of REMIX potentials
does not yet handle southern-hemisphere sign/mirroring policy
uses direct mlat/mlon interpolation, not a full SAMI3 field-line mapping
sets target mlat < 45 deg to zero because the source package is high-lat only
has not yet run a SAMI3 smoke with this generated phi_weimer.inp
```

## Next Step

Run a controlled SAMI3 smoke with:

```text
lweimer = T
phi_weimer.inp = logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.inp
```

Compare against the current Weimer baseline:

```text
phiu.dat
vexb-related outputs if enabled
runtime log lines from potential.f90:weimer
no NaN/Inf and no EOF from phi_weimer.inp
```

If that passes, the next implementation step is to add an online sender-side
`POT` packet or sidecar update that refreshes `phi_weimer` at the coupling
cadence, while keeping the static-file path as the replay baseline.
