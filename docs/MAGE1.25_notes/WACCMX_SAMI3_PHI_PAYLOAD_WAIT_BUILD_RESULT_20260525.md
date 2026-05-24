# WACCM-X Sender Phi Payload Wait Support

Date: 2026-05-25

## Purpose

The current full append2 integration launcher pre-generates the Voltron/REMIX
phi payload before CESM/WACCM-X starts.  That is robust for validation, but the
final coupling direction needs to support a runtime producer that writes the
payload while the WACCM-X sender is already running.

This update adds an optional sender-side wait gate for:

```text
WXSAMI3_PHI_PAYLOAD_FILE
```

The default remains:

```text
WXSAMI3_PHI_PAYLOAD_WAIT_SECONDS = 0
```

so the already validated pre-generated payload path is unchanged unless the
new environment variable is explicitly set.

## New Environment Variables

```text
WXSAMI3_PHI_PAYLOAD_WAIT_SECONDS
  Seconds for the WACCM-X sender to wait for the phi payload file to become
  complete before opening and sending it. Default: 0.

WXSAMI3_PHI_PAYLOAD_STABLE_SECONDS
  Number of consecutive one-second size-stability checks after the expected
  payload size is reached. Default: 1.
```

The readiness check reads the binary header and requires:

```text
magic   = 20260524
version = 1
nlat    = 125
nlon    = 97
nframe >= 1
file size >= 20 + nframe * (12 + 4*nlat*nlon)
```

## Build Result

The first build attempt caught a real interface issue:

```text
shr_sys_sleep expects real(r8), not integer
```

After changing the call to:

```fortran
call shr_sys_sleep(1._r8)
```

the case rebuilt successfully:

```text
MODEL BUILD HAS FINISHED SUCCESSFULLY
```

Build evidence:

```text
logs/cesm_sender_phi_wait_build_retry_20260525.log
```

Updated executable:

```text
/home/jiaoy_group/jiaoy/data/CESM/case_output_root_online_live_neutral_20260523/mage_qpx2000_f19_sami3_live_neutral_20260523/bld/cesm.exe
timestamp = 2026-05-25 02:21:14 CST
```

## Role In Coupling Route

This does not by itself prove a direct live REMIX/Voltron-to-SAMI3 phi path.
It removes one sender-side blocker: the CESM/WACCM-X sender can now tolerate a
same-job Voltron producer that creates the versioned phi payload shortly after
the online neutral/phi receiver path has started.

Next validation should use the same full integration acceptance script, but
with a launcher that starts the Voltron phi writer concurrently and sets:

```text
WXSAMI3_PHI_PAYLOAD_WAIT_SECONDS > 0
```
