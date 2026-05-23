# MAGE-WACCMX Aggressive Tests

Date:
- 2026-03-25
- 2026-03-26 continuation

## Scope

这份记录只总结在**当前真实文件桥成功基线**之上做的更激进输入压力测试。

成功基线：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a`

测试脚本：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_one_aggressive_test.sh`

## Baseline

基线 `step2` contract：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/step2_kaiju_feedback/waccmx_voltron_contract.txt`

基线 envelope：
- Hemisphere 1:
  `SIGMAP 0.138 .. 17.678 S`, `SIGMAH 0.136 .. 11.635 S`
- Hemisphere 2:
  `SIGMAP 0.109 .. 10.062 S`, `SIGMAH 0.157 .. 8.839 S`

## Test Matrix

### 1. `stress_epot_x4`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x4_20260325a`

Input scaling:
- `epot x4`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x4_20260325a/manual_cesm_stress_epot_x4.log`
- confirmed end markers:
  `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
  `med_finalize max rss=5432565760.0 MB`
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x4_20260325a/waccmx_cesm_feedback_package.h5`
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x4_20260325a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- step2 exchange:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x4_20260325a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- step2 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x4_20260325a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.136 .. 17.734 S`, `SIGMAH 0.136 .. 11.640 S`
- Hemisphere 2:
  `SIGMAP 0.111 .. 10.038 S`, `SIGMAH 0.157 .. 8.839 S`

### 2. `stress_all_x2`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x2_20260325a`

Input scaling:
- `epot x2`
- `avg_eng x2`
- `num_flux x2`

CESM result:
- success
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x2_20260325a/manual_cesm_stress_all_x2.log`
- confirmed end markers:
  `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
  `med_finalize max rss=5432340480.0 MB`
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x2_20260325a/waccmx_cesm_feedback_package.h5`
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x2_20260325a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- step2 exchange:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x2_20260325a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- step2 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x2_20260325a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.137 .. 17.696 S`, `SIGMAH 0.136 .. 11.637 S`
- Hemisphere 2:
  `SIGMAP 0.110 .. 10.054 S`, `SIGMAH 0.157 .. 8.839 S`

### 3. `epot_only_true`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/epot_only_true_20260326a`

Input branch:
- aurora import files truly omitted from the CESM run directory
- `epot x1`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/epot_only_true_20260326a/manual_cesm_epot_only_true.log`
- confirmed end markers:
  `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
  `med_finalize max rss=5431795712.0 MB`
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/epot_only_true_20260326a/waccmx_cesm_feedback_package.h5`
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/epot_only_true_20260326a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- step2 exchange:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/epot_only_true_20260326a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- step2 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/epot_only_true_20260326a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.138 .. 17.678 S`, `SIGMAH 0.136 .. 11.635 S`
- Hemisphere 2:
  `SIGMAP 0.109 .. 10.062 S`, `SIGMAH 0.157 .. 8.839 S`

### 4. `aurora_only_true`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/aurora_only_true_20260326a`

Input branch:
- global `epot` file truly omitted from the CESM run directory
- `epot x1`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/aurora_only_true_20260326a/manual_cesm_aurora_only_true.log`
- confirmed end markers:
  `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
  `med_finalize max rss=5434707968.0 MB`
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/aurora_only_true_20260326a/waccmx_cesm_feedback_package.h5`
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/aurora_only_true_20260326a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- step2 exchange:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/aurora_only_true_20260326a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- step2 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/aurora_only_true_20260326a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.141 .. 17.577 S`, `SIGMAH 0.136 .. 11.628 S`
- Hemisphere 2:
  `SIGMAP 0.108 .. 10.063 S`, `SIGMAH 0.156 .. 8.838 S`

### 5. `stress_epot_x8`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x8_20260326a`

Input scaling:
- `epot x8`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x8_20260326a/manual_cesm_stress_epot_x8.log`
- confirmed end markers:
  `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
  `med_finalize max rss=5431762944.0 MB`
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x8_20260326a/waccmx_cesm_feedback_package.h5`
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x8_20260326a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- step2 exchange:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x8_20260326a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- step2 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_epot_x8_20260326a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.135 .. 17.810 S`, `SIGMAH 0.136 .. 11.646 S`
- Hemisphere 2:
  `SIGMAP 0.112 .. 10.005 S`, `SIGMAH 0.157 .. 8.839 S`

### 6. `stress_all_x4`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x4_20260326a`

Input scaling:
- `epot x4`
- `avg_eng x4`
- `num_flux x4`

CESM result:
- success
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x4_20260326a/manual_cesm_stress_all_x4.log`
- confirmed end markers:
  `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
  `med_finalize max rss=5431984128.0 MB`
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x4_20260326a/waccmx_cesm_feedback_package.h5`
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x4_20260326a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- step2 exchange:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x4_20260326a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- step2 forward package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x4_20260326a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.136 .. 17.734 S`, `SIGMAH 0.136 .. 11.640 S`
- Hemisphere 2:
  `SIGMAP 0.110 .. 10.038 S`, `SIGMAH 0.157 .. 8.839 S`

### 7. `stress_all_x8`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_all_x8_A4725083_T1`

Input scaling:
- `epot x8`
- `avg_eng x8`
- `num_flux x8`

CESM result:
- success

Closed-loop result:
- success

### 8. `stress_epot_x10`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x10_A4725184_T0`

Input scaling:
- `epot x10`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success

Closed-loop result:
- success

### 9. `stress_epot_x12`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x12_A4725184_T1`

Input scaling:
- `epot x12`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success

Closed-loop result:
- success

### 10. `stress_epot_x13`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_epot_x13_A4725248_T0`

Input scaling:
- `epot x13`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success

Closed-loop result:
- success

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.133 .. 17.905 S`, `SIGMAH 0.136 .. 11.654 S`
- Hemisphere 2:
  `SIGMAP 0.113 .. 9.970 S`, `SIGMAH 0.157 .. 8.839 S`

### 11. `stress_epot_x14`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x14_A4725184_T2`

Input scaling:
- `epot x14`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- failure
- signature:
  `SIGSEGV` on `rank 3`

### 12. `stress_all_x12`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_all_x12_A4725184_T3`

Input scaling:
- `epot x12`
- `avg_eng x12`
- `num_flux x12`

CESM result:
- success

Closed-loop result:
- success

### 13. `stress_all_x16`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_all_x16_A4725248_T1`

Input scaling:
- `epot x16`
- `avg_eng x16`
- `num_flux x16`

CESM result:
- failure
- signature:
  `SIGSEGV` on `rank 3`

## Clamp-Only Mitigation

Temporary limiter implementation:
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/dpie_coupling.F90`

Limiter behavior:
- `d_pie_set_external_epot` now clips external `epot` to `150`
- the runtime log prints:
  `d_pie_set_external_epot: input/limited absmax ...`

Observed result:
- clamp alone does **not** cure the extreme-forcing failure
- `stress_epot_x14_limited_A4725516_T0` still failed
- `stress_all_x16_limited_A4725516_T1` still failed
- `stress_epot_x14_limited150_A4725561_T0` still failed even when the log confirmed:
  `184.390 -> 150.000`

Key result roots:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_limiter/stress_epot_x14_limited_A4725516_T0`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_limiter/stress_all_x16_limited_A4725516_T1`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_limiter150/stress_epot_x14_limited150_A4725561_T0`

## Smoothed EPOT Mitigation

Bridge-side test hook:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_one_aggressive_test.sh`

New behavior:
- optional 2D `epot` smoothing on the bridged WACCM-X magnetic grid
- per-test diagnostics written to:
  `inputs/mage_waccmx_epot_summary.txt`

### 1. `stress_epot_x14_smooth1`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth/stress_epot_x14_smooth1_A4725607_T0`

Result:
- success
- CESM completed through `med_finalize`
- second `voltron` contract exists

Smoothed epot diagnostics:
- `smoothed_absmax = 178.182`
- `smoothed_lon_grad_max = 14.605`
- `smoothed_lat_grad_max = 56.491`

### 2. `stress_epot_x14_smooth2`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth/stress_epot_x14_smooth2_A4725607_T1`

Result:
- success
- CESM completed through `med_finalize`
- second `voltron` contract exists

Smoothed epot diagnostics:
- `smoothed_absmax = 169.702`
- `smoothed_lon_grad_max = 13.710`
- `smoothed_lat_grad_max = 45.426`

### 3. `stress_all_x16_smooth2`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth/stress_all_x16_smooth2_A4725607_T2`

Result:
- failure
- signature:
  `SIGSEGV` on `rank 3`

Smoothed epot diagnostics:
- `smoothed_absmax = 193.945`

### 4. `stress_epot_x15_smooth2`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup/stress_epot_x15_smooth2_A4725660_T0`

Result:
- failure
- signature:
  `te_map: Lagrangian levels are crossing`
  followed by `MPI_ABORT` on `rank 3`

Smoothed epot diagnostics:
- `smoothed_absmax = 181.824`

### 5. `stress_epot_x16_smooth2`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup/stress_epot_x16_smooth2_A4725660_T1`

Result:
- failure
- signature:
  `SIGSEGV` on `rank 3`

Smoothed epot diagnostics:
- `smoothed_absmax = 193.945`

### 6. `stress_epot_x16_smooth3`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup/stress_epot_x16_smooth3_A4725660_T2`

Result:
- failure
- signature:
  `SIGSEGV` on `rank 3`

Smoothed epot diagnostics:
- `smoothed_absmax = 185.175`

### 7. `stress_all_x14_smooth2`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_followup/stress_all_x14_smooth2_A4725660_T3`

Result:
- success
- CESM completed through `med_finalize`
- second `voltron` contract exists

Smoothed epot diagnostics:
- `smoothed_absmax = 169.702`

### 8. `stress_all_x15_smooth2`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_smooth_all15/stress_all_x15_smooth2_A4725676_T0`

Result:
- failure
- signature:
  `te_map: Lagrangian levels are crossing`
  followed by `MPI_ABORT` on `rank 3`

Smoothed epot diagnostics:
- `smoothed_absmax = 181.824`

### 9. `stress_all_x14p5_smooth2`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests/stress_all_x14p5_smooth2_20260328a`

Result:
- success
- CESM completed through `med_finalize`
- second `voltron` contract, exchange summary, and forward package all exist

Smoothed epot diagnostics:
- `smoothed_absmax = 175.763`
- `smoothed_lon_grad_max = 14.199`
- `smoothed_lat_grad_max = 47.048`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.133 .. 17.909 S`, `SIGMAH 0.136 .. 11.655 S`
- Hemisphere 2:
  `SIGMAP 0.109 .. 9.975 S`, `SIGMAH 0.156 .. 8.840 S`

## Current Practical Boundaries

Without smoothing:
- `epot x13` succeeds
- `epot x14` fails with `SIGSEGV`
- `all x12` succeeds
- `all x16` fails with `SIGSEGV`

With the current temporary `150`-V clamp plus bridge-side `epot` smoothing:
- `epot x14` succeeds
- `epot x14.5` succeeds
- `epot x15` fails with `te_map` / `MPI_ABORT`
- `epot x16` fails with `SIGSEGV`
- `all x14` succeeds
- `all x14.5` succeeds
- `all x15` fails with `te_map` / `MPI_ABORT`
- `all x16` fails with `SIGSEGV`

Engineering takeaway:
- hard clipping alone is insufficient
- moderate spatial smoothing materially improves robustness
- the next instability mode after smoothing is no longer only `SIGSEGV`; a lower-level `te_map` crossing abort appears first near `x15`
- for single-axis forcing, the practical smoothed boundary is now narrowed from
  `epot x14~x15` to approximately `epot x14.5~x15`
- for combined forcing, the practical smoothed boundary is now narrowed from
  `all x14~x15` to approximately `all x14.5~x15`

Reporting-level integer summary:
- if we stop here and do not continue finer fractional scans, the clean integer conclusion is:
  `epot x14` succeeds, `epot x15` fails
- for combined forcing, the clean integer conclusion is:
  `all x14` succeeds, `all x15` fails

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_all_x8_A4725083_T1`

Input scaling:
- `epot x8`
- `avg_eng x8`
- `num_flux x8`

CESM result:
- success
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_all_x8_A4725083_T1/manual_cesm_stress_all_x8.log`
- confirmed end markers:
  `Opened file mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
  `med_finalize max rss=5431840768.0 MB`
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- feedback package:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_all_x8_A4725083_T1/waccmx_cesm_feedback_package.h5`
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_all_x8_A4725083_T1/step2_kaiju_feedback/waccmx_voltron_contract.txt`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.135 .. 17.810 S`, `SIGMAH 0.136 .. 11.646 S`
- Hemisphere 2:
  `SIGMAP 0.111 .. 10.005 S`, `SIGMAH 0.157 .. 8.839 S`

### 8. `stress_epot_x16`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_epot_x16_A4725083_T0`

Input scaling:
- `epot x16`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- failed
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_epot_x16_A4725083_T0/manual_cesm_stress_epot_x16.log`
- failure signature:
  `Program received signal SIGSEGV: Segmentation fault - invalid memory reference.`
  `prterun noticed that process rank 3 ... exited on signal 11`
- crash occurs after restart/history output files are opened
- no step2 feedback ingestion was reached

### 9. `stress_epot_x10`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x10_A4725184_T0`

Input scaling:
- `epot x10`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x10_A4725184_T0/step2_kaiju_feedback/waccmx_voltron_contract.txt`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.134 .. 17.848 S`, `SIGMAH 0.136 .. 11.649 S`
- Hemisphere 2:
  `SIGMAP 0.112 .. 9.989 S`, `SIGMAH 0.157 .. 8.839 S`

### 10. `stress_epot_x12`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x12_A4725184_T1`

Input scaling:
- `epot x12`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x12_A4725184_T1/step2_kaiju_feedback/waccmx_voltron_contract.txt`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.133 .. 17.886 S`, `SIGMAH 0.136 .. 11.653 S`
- Hemisphere 2:
  `SIGMAP 0.113 .. 9.976 S`, `SIGMAH 0.157 .. 8.839 S`

### 11. `stress_epot_x14`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x14_A4725184_T2`

Input scaling:
- `epot x14`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- failed
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x14_A4725184_T2/manual_cesm_stress_epot_x14.log`
- failure signature:
  `Program received signal SIGSEGV: Segmentation fault - invalid memory reference.`
  `prterun noticed that process rank 3 ... exited on signal 11`
- crash occurs after restart/history output files are opened
- no step2 feedback ingestion was reached

### 12. `stress_all_x12`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_all_x12_A4725184_T3`

Input scaling:
- `epot x12`
- `avg_eng x12`
- `num_flux x12`

CESM result:
- success
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_all_x12_A4725184_T3/step2_kaiju_feedback/waccmx_voltron_contract.txt`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.133 .. 17.887 S`, `SIGMAH 0.136 .. 11.653 S`
- Hemisphere 2:
  `SIGMAP 0.112 .. 9.976 S`, `SIGMAH 0.157 .. 8.839 S`

### 13. `stress_epot_x13`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_epot_x13_A4725248_T0`

Input scaling:
- `epot x13`
- `avg_eng x1`
- `num_flux x1`

CESM result:
- success
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Closed-loop result:
- success
- step2 contract:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_epot_x13_A4725248_T0/step2_kaiju_feedback/waccmx_voltron_contract.txt`

Post-feedback envelope:
- Hemisphere 1:
  `SIGMAP 0.133 .. 17.905 S`, `SIGMAH 0.136 .. 11.654 S`
- Hemisphere 2:
  `SIGMAP 0.113 .. 9.970 S`, `SIGMAH 0.157 .. 8.839 S`

### 14. `stress_all_x16`

Test root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_all_x16_A4725248_T1`

Input scaling:
- `epot x16`
- `avg_eng x16`
- `num_flux x16`

CESM result:
- failed
- log:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_all_x16_A4725248_T1/manual_cesm_stress_all_x16.log`
- failure signature:
  `Program received signal SIGSEGV: Segmentation fault - invalid memory reference.`
  `prterun noticed that process rank 3 ... exited on signal 11`
- crash occurs after restart/history output files are opened
- no step2 feedback ingestion was reached

## Interpretation

这两轮结果说明：

- 当前真实文件桥闭环对更强外部 forcing 具有一定鲁棒性。
- `epot x4` 没有重新触发此前最脆弱的两类错误：
  - `epot size mismatch`
  - `edyn_esmf_set2d_phys ... rc = 51`
- `epot x2 + aurora x2` 的联合作用也没有把闭环推垮。
- 两组压力测试后的 `step2` conductance envelope 与基线相比只发生了温和变化，没有出现结构性失稳。
- 两个真正的退化分支也成立：
  - `epot_only_true` 说明即使不向 CESM 提供 aurora rank import 文件，闭环仍可完成。
  - `aurora_only_true` 说明即使不向 CESM 提供全局 `epot` 文件，闭环仍可完成。
- `stress_epot_x8` 进一步把最敏感的 `epot` 通道推高到 `x8`，`CESM` 和第二轮 `voltron` 仍都跑完。
- `stress_all_x4` 说明把 `epot + aurora` 一起推到 `x4` 时，闭环仍然维持稳定，并没有比 `stress_all_x2` 明显恶化。
- `stress_all_x8` 与 `stress_all_x12` 说明当前真实文件桥在更强的联合 forcing 下仍可闭环成功。
- `stress_all_x16` 说明联合 forcing 再推到 `x16` 后也会在 CESM 端复现同类 `SIGSEGV`，所以联合 forcing 的安全区间目前可保守记为 `<= all x12`。
- `stress_epot_x14` 与 `stress_epot_x16` 都在真实 CESM 端复现了 `rank 3` 的 `SIGSEGV`，而 `stress_epot_x13` 已通过，所以当前 `epot` 稳定阈值已经被压缩到 `x13 <= threshold < x14`。
- `stress_epot_x10`、`stress_epot_x12` 与 `stress_epot_x13` 都通过，说明单独电势放大到 `x13` 仍在当前桥接实现的稳定区间内。
- 当前 `step2` conductance envelope` 对更强 forcing 的响应变化仍然温和，说明反馈链条存在明显饱和/钳制特征。
- `aurora_only_true`、`epot_only_true`、`stress_epot_x8`、`stress_all_x4`、`stress_all_x8`、`stress_epot_x10`、`stress_epot_x12`、`stress_epot_x13`、`stress_all_x12` 跑完后，没有残留 `cesm.exe` 或相关 `voltron.x` 后台进程。

## Important Note

`step2` 的 `launcher.log` 末尾可能看到 `forrtl: error (78): process killed (SIGTERM)`。

这里不是失败，而是测试驱动逻辑在检测到下面三个关键产物都已经写出后，主动结束第二轮 `voltron.x`：
- `waccmx_voltron_contract.txt`
- `waccmx_voltron_exchange.md`
- `waccmx_voltron_forward_package.h5`

这和主桥接脚本：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`

采用的是同一种“产物齐备后结束 smoke run”的策略。
