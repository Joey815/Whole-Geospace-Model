# MAGE-WACCMX D 档 MPI 文件桥推进记录

日期：2026-05-19

## 当前结论

已完成 D 档 `WACCMX_FILE` 的 MPI 化过渡原型，并完成 clean-exit 1h 基线与 `neutral_rhs` 短测：

- MAGE/Kaiju 侧使用 `voltron_mpi.x`
- WACCM-X/CESM 侧仍使用已验证的文件桥
- clean-exit 1h 基线：`7475694`，`12 cycles`，`NSRHS=off`
- `neutral_rhs / NEUTRAL_DYNAMO_RHS` 路径短测：`7477415`，`2 cycles`，`WACCMX_NSRHS_SOURCE_MODE=geo_sidecar`
- 正式稳定变量：`POT / AVG_ENG / NUM_FLUX` 和 `SIGMAP / SIGMAH`
- `neutral_rhs` 已证明文件路径接通，但当前 `geo_sidecar` 数值量级偏大，尚不能作为物理正确基线

这不是 native MPI communicator 耦合，也不是 CESM/CIME mediator 耦合；它是：

```text
MPI Voltron export -> file bridge -> CESM/WACCM-X -> file feedback -> MPI Voltron ingest/export
```

## D 档 neutral_rhs / NEUTRAL_DYNAMO_RHS 2-cycle 短测

- job id: `7477415`
- job name: `waccmxDmpiN2`
- state: `COMPLETED`
- elapsed: `00:16:32`
- resources: `1 node`, `4 CPUs`, `256G`
- batch MaxRSS: `16867900K`
- node: `qhcn066`
- output:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c2_nsrhs_geo_cleanexit_20260519_S7477415`
- output size: `881M`

运行设置：

```text
TEST_NAME=waccmx_file_d_mpi_c2_nsrhs_geo_cleanexit_20260519
NUM_CYCLES=2
KAIJU_LAUNCH_MODE=mpi_artifact_watch
KAIJU_MPI_TOTAL_RANKS=2
KAIJU_MPI_REQUIRE_CLEAN_EXIT=1
WACCMX_NSRHS_SOURCE_MODE=geo_sidecar
WACCMX_NSRHS_UNFOLDING=none
WACCMX_NSRHS_TRANSFORM=none
```

完成链路：

```text
seed_forward
cycle01: MAGE forward -> WACCM-X -> nsrhs_geo_sidecar feedback -> MPI Voltron ingest/export
cycle02: MAGE forward -> WACCM-X -> nsrhs_geo_sidecar feedback -> MPI Voltron ingest/export
final_summary.md: LONG_STABILITY_DONE
```

关键结果：

- `cycle01_feedback/mage_waccmx_nsrhs_geo_rank*.txt` 已生成。
- `cycle02_feedback/mage_waccmx_nsrhs_geo_rank*.txt` 已生成。
- `cycle01_waccmx_cesm_feedback_package.h5` 和 `cycle02_waccmx_cesm_feedback_package.h5` 的 `meta/nsrhs_source = nsrhs_geo_sidecar`。
- `nsrhs_projection = direct_mag_to_geo_2d_sidecar`。
- `nsrhs_semantics = geo_projected_rhs_sidecar`。
- `cycle01` 的 `neutral_rhs_absmax` 约为北半球 `5.6645e7 cm/s`、南半球 `5.5616e7 cm/s`。
- `cycle02` 的 `neutral_rhs_absmax` 约为北半球 `5.6043e7 cm/s`、南半球 `5.4394e7 cm/s`。
- 3 个 MPI 段全部 `clean_exit_ready=1`、`mpi_wait_status=0`、`mpi_status=0`。
- 7 个 HDF5 package 全部可读。
- 日志扫描未命中 `forrtl`、`SIGTERM`、`process killed`、`ERROR`、`FATAL`、`Traceback`、`NaN`、`MPI_ABORT`。

重要判断：

- 这次证明 `WACCM-X -> geo_sidecar -> HDF5 feedback -> MAGE/REMIX NEUTRAL_DYNAMO_RHS slot` 的工程路径已经接通。
- 这次不能证明 `NEUTRAL_DYNAMO_RHS` 的物理量级已经正确。
- 当前 `NEUTRAL_DYNAMO_RHS absmax` 在 Voltron contract 中溢出显示为 `********** cm/s`，并使下一轮 WACCM-X 的 `d_pie_set_external_epot` 出现 `input/limited absmax 11787.761 -> 150.000`。
- 下一步应优先做单位/缩放修正，而不是直接扩展到 1h `neutral_rhs` 正式跑。

## 成功作业

### D 档 MPI export smoke

- job id: `7469322`
- state: `COMPLETED`
- elapsed: `00:03:50`
- resources: `1 node`, `2 CPUs`, `64G`
- node: `qhcn183`
- output:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/d_mpi_file_smoke/waccmx_file_officialD_mpi_export_S7469322`

结果：

- `voltron_mpi.x` 成功进入 `WACCMX_FILE`
- 写出 `waccmx_voltron_contract.txt`
- 写出 `waccmx_voltron_exchange.md`
- 写出 `waccmx_voltron_forward_package.h5`

说明：

- `mpiexec_wait_status=143` 是 artifact 写出后由 watcher 主动终止 MPI 进程导致
- 顶层 Slurm 作业为 `COMPLETED`
- 该状态作为当前 MPI export smoke 的成功标准

### D 档 MPI bridge 1-cycle

- job id: `7469461`
- state: `COMPLETED`
- elapsed: `00:13:31`
- resources: `1 node`, `4 CPUs`, `256G`
- node: `qhcn225`
- output:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c1_20260519_S7469461`

完成链路：

```text
seed_forward: MPI Voltron -> WACCMX_FILE forward package
cycle01_inputs: bridge -> CESM import files
manual_cesm_cycle01.log: CESM/WACCM-X one continuation segment
cycle01_waccmx_cesm_feedback_package.h5: WACCM-X feedback -> MAGE package
cycle01_kaiju: MPI Voltron feedback ingest/export
final_summary.md: LONG_STABILITY_DONE
```

最终 contract：

- Hemisphere 1 `SIGMAP`: `0.147 .. 17.925 S`
- Hemisphere 1 `SIGMAH`: `0.176 .. 11.720 S`
- Hemisphere 2 `SIGMAP`: `0.112 .. 9.808 S`
- Hemisphere 2 `SIGMAH`: `0.199 .. 8.808 S`
- `NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s`

HDF5 检查：

- `seed_forward/waccmx_voltron_forward_package.h5` 可读
- `cycle01_waccmx_cesm_feedback_package.h5` 可读
- `cycle01_kaiju/waccmx_voltron_forward_package.h5` 可读

### D 档 MPI bridge 3-cycle

- job id: `7469546`
- state: `COMPLETED`
- elapsed: `00:42:03`
- resources: `1 node`, `4 CPUs`, `256G`
- batch MaxRSS: `20713676K`
- node: `qhcn039`
- output:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c3_20260519_S7469546`

完成链路：

```text
seed_forward: MPI Voltron -> WACCMX_FILE forward package
cycle01: CESM/WACCM-X + MPI Voltron feedback ingest/export
cycle02: CESM/WACCM-X + MPI Voltron feedback ingest/export
cycle03: CESM/WACCM-X + MPI Voltron feedback ingest/export
final_summary.md: LONG_STABILITY_DONE
```

最终 contract：

- Hemisphere 1 `SIGMAP`: `0.150 .. 18.255 S`
- Hemisphere 1 `SIGMAH`: `0.214 .. 11.769 S`
- Hemisphere 2 `SIGMAP`: `0.133 .. 9.496 S`
- Hemisphere 2 `SIGMAH`: `0.248 .. 8.697 S`
- `NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s`

HDF5 检查：

- `seed_forward/waccmx_voltron_forward_package.h5` 可读
- `cycle01_waccmx_cesm_feedback_package.h5` 可读
- `cycle02_waccmx_cesm_feedback_package.h5` 可读
- `cycle03_waccmx_cesm_feedback_package.h5` 可读
- `cycle03_kaiju/waccmx_voltron_forward_package.h5` 可读

输出规模：

- `1.2G`

## 当前推进计划：D 档 MPI bridge 12-cycle / 1h

目标：

- 使用已通过 `1 cycle` 和 `3 cycles` 的同一 D 档 MPI 文件桥机制
- `NUM_CYCLES=12`
- 每个 cycle 对应约 `300 s` WACCM-X/CESM 模拟时间
- 总模拟时间约 `3600 s = 1 h`
- `NSRHS=off`
- `KAIJU_GCM_BACKEND=WACCMX_FILE`
- `KAIJU_LAUNCH_MODE=mpi_artifact_watch`
- `KAIJU_MPI_TOTAL_RANKS=2`

提交脚本：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_d_mpi_file_1h.sh`

计划资源：

- `1 node`
- `4 CPUs`
- `256G`
- walltime override: `04:00:00`

采用 `04:00:00` 的原因：

- `3 cycles` 已实测 `00:42:03`
- 简单线性外推 `12 cycles` 约 `2.8 h`
- 默认 `02:00:00` 存在被 Slurm walltime 杀掉的风险

验收标准：

- 顶层 Slurm 作业为 `COMPLETED`
- `final_summary.md` 出现 `LONG_STABILITY_DONE`
- `cycle01` 到 `cycle12` 均生成 WACCM-X feedback package
- `cycle12_kaiju/waccmx_voltron_forward_package.h5` 可读
- 最终 contract 中 `SIGMAP / SIGMAH` 为非默认有效值
- `NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s`，确认当前仍为 `NSRHS=off`
- 日志中不出现 `SIGSEGV`、`forrtl`、`Traceback`、`NaN`
- 允许 MPI 子步出现 artifact-watch 主动终止导致的 `143`，但顶层作业必须成功

当前提交：

- job id: `7469881`
- submit time: `2026-05-19 02:27 CST`
- state at first check: `RUNNING`
- node: `qhcn227`
- Slurm job name: `waccmxDmpi1h`
- Slurm walltime: `04:00:00`
- output:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_1h_20260519_S7469881`

早期检查：

- preflight passed
- `seed_forward/waccmx_voltron_forward_package.h5` 已生成且可读
- HDF5 root groups:
  `Meta,NORTH_APEX,NORTH_GEO,NORTH_GRID,SOUTH_APEX,SOUTH_GEO,SOUTH_GRID`
- `seed_forward/mpi_artifact_watch_summary.txt`:
  `launch_mode=mpi_artifact_watch`, `mpi_total_ranks=2`, `artifacts_ready=1`, `mpi_wait_status=143`
- `cycle01_inputs` 已生成 4 个 CESM rank import 文件
- `manual_cesm_cycle01.log` 已开始，WACCM-X/CESM 正在读取 `2005-12-31-00300` restart

`2026-05-19 02:42 CST` 更新：

- `cycle01_waccmx_cesm_feedback_package.h5` 已生成且可读
- `cycle01_kaiju/waccmx_voltron_forward_package.h5` 已生成且可读
- `cycle01` 已完成一次完整闭环：
  `WACCM-X/CESM -> feedback package -> MPI Voltron ingest/export -> next forward package`
- `cycle02_inputs` 已生成 4 个 CESM rank import 文件
- `manual_cesm_cycle02.log` 已开始
- 截至该检查点，未发现：
  `SIGSEGV`, `forrtl`, `Traceback`, `NaN`, `ERROR`, `FATAL`

`2026-05-19 10:16 CST` 更新：

- job id `7469881` 顶层状态：`TIMEOUT`
- elapsed: `04:00:27`
- walltime: `04:00:00`
- node: `qhcn227`
- resources: `4 CPUs`, `256G`
- batch MaxRSS: `22341192K`
- `final_summary.md`: 未生成
- 完整完成的 feedback cycles:
  `01 02 03 04 05 06 07 08`
- 完整完成的 MPI Kaiju ingest/export cycles:
  `01 02 03 04 05 06 07 08`
- `manual_cesm_cycle09.log` 已生成，说明作业进入第 9 个 CESM/WACCM-X 段后被 walltime 杀掉
- 已完成的 8 个 WACCM-X feedback HDF5 package 均可读
- 已完成的 8 个 MPI Kaiju forward HDF5 package 均可读
- `cycle08_kaiju/waccmx_voltron_contract.txt` 最终有效值：
  - Hemisphere 1 `SIGMAP`: `0.167 .. 17.690 S`
  - Hemisphere 1 `SIGMAH`: `0.244 .. 11.657 S`
  - Hemisphere 2 `SIGMAP`: `0.163 .. 8.931 S`
  - Hemisphere 2 `SIGMAH`: `0.306 .. 8.434 S`
  - `NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s`

判断：

- 这不是数值崩溃，也不是文件桥变量失败
- 这是 walltime 不足导致的中断
- 目前可确认 `8 cycles = 40 min` 模拟时间的 D 档 MPI file-bridge 闭环成功
- `12 cycles = 1 h` 尚未完成，需要更长 walltime 或降低每 cycle 开销后重跑

## 速度诊断

`7469881` 的速度慢主要来自两类开销。

第一类是当前 file-bridge 结构性开销：

- 每个 cycle 只推进 `300 s = 5 min` 模拟时间
- 每个 cycle 都要重新准备输入、启动 CESM/WACCM-X continuation 段、读 restart、写 feedback package
- 当前不是 native MPI mediator 耦合，而是串行化的：
  `MPI Voltron export -> files -> CESM/WACCM-X -> files -> MPI Voltron ingest/export`
- 因此 MAGE/Kaiju 与 WACCM-X 不是长期并行驻留，而是在每个 cycle 反复启动/同步

第二类是当前 MPI artifact-watch 的实现问题：

- `sacct` 显示 `7469881.0` 到 `7469881.8` 的 `hydra_bstrap_proxy` step 都一直存活到 `06:27:54/06:27:55`
- 这说明 artifact 写出后，当前脚本只杀掉了外层 `mpiexec`/subshell，没有干净回收 Hydra/Voltron 的 Slurm step
- 结果是后续 cycles 叠加了越来越多的残留 MPI step，导致资源竞争和 walltime 消耗

实测时间戳：

```text
02:31:36 seed forward package
02:37:04 cycle01 feedback
02:40:33 cycle01 Kaiju forward
02:48:10 cycle02 feedback
02:54:56 cycle02 Kaiju forward
03:07:08 cycle03 feedback
03:16:35 cycle03 Kaiju forward
03:32:34 cycle04 feedback
03:40:00 cycle04 Kaiju forward
03:58:21 cycle05 feedback
04:10:40 cycle05 Kaiju forward
04:34:15 cycle06 feedback
04:45:33 cycle06 Kaiju forward
05:13:14 cycle07 feedback
05:22:52 cycle07 Kaiju forward
05:53:46 cycle08 feedback
06:08:33 cycle08 Kaiju forward
06:23:50 cycle09 CESM log
06:27:54 Slurm time limit
```

速度趋势：

- 前 1-2 个 cycle 尚可
- 后面每个 cycle 的等待间隔明显拉长
- 这与残留 `hydra_bstrap_proxy` step 累积高度一致

优先修复：

1. 先修 MPI artifact-watch 的清理方式，确保每轮 export 后 Hydra/Voltron 子进程和 Slurm step 被干净结束
2. 再重跑 `12 cycles`
3. 如果仍慢，再提高 CESM/WACCM-X 任务数或改成长驻/mediator 方式

不建议只把 walltime 盲目拉长：

- 单纯把 walltime 从 `04:00:00` 拉到 `08:00:00` 可能完成 12 cycles
- 但残留 MPI step 仍会堆积，不能作为正式方案

## 优化记录

对比基线：

```text
旧 direct/file 12-cycle:
  job 7270337, COMPLETED, 01:02:15, 4 CPUs, 256G
  每个 cycle 的 CESM feedback 时间间隔约 5 min

旧 live_repair 12-cycle:
  job 4747824, COMPLETED, 01:09:34, 4 CPUs, 256G

当前未优化 MPI 12-cycle:
  job 7469881, TIMEOUT, 04:00:27, 4 CPUs, 256G
  只完成 8 个完整 cycles，进入 cycle09 后 walltime 到期
```

已做优化：

- `KAIJU_MPI_HYDRA_BOOTSTRAP` 默认改为 `fork`
- MPI artifact-watch 使用 `setsid` 启动 `mpiexec`
- artifact 写出后使用进程组方式清理 MPI/Voltron 子进程
- 每轮 artifact 后 grace time 从 `10 s` 降到 `2 s`

验证作业：

- job id: `7474875`
- test name: `waccmx_file_d_mpi_c2_cleanup_20260519`
- state: `COMPLETED`
- elapsed: `00:15:25`
- resources: `4 CPUs`, `256G`
- MaxRSS: `17145836K`
- cycles: `2`
- output:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c2_cleanup_20260519_S7474875`

验证结论：

- `sacct` 只有 `job/batch/extern`，没有残留 `hydra_bstrap_proxy` step
- `seed_forward`, `cycle01_kaiju`, `cycle02_kaiju` 的 summary 均显示 `mpi_hydra_bootstrap=fork`
- `2 cycles` 总耗时 `15m25s`
- 对比旧 direct 2-cycle `13m32s`，优化后 MPI 版仍慢约 `14%`，但已经消除了未优化版本的残留 step 叠加问题

下一步：

- 用优化后的 `submit_d_mpi_file_1h.sh` 重跑 `12 cycles`
- 当前 1h wrapper 默认：
  - `TEST_NAME=waccmx_file_d_mpi_1h_cleanup_20260519`
  - `NUM_CYCLES=12`
  - `SBATCH_TIME_LIMIT=03:00:00`
  - `KAIJU_MPI_HYDRA_BOOTSTRAP=fork`
  - `KAIJU_MPI_POST_ARTIFACT_GRACE_SECONDS=2`

优化版 12-cycle 提交：

- job id: `7474987`
- submit time: `2026-05-19 11:57 CST`
- state at first check: `RUNNING`
- node: `qhcn075`
- Slurm job name: `waccmxDmpi1h`
- walltime: `03:00:00`
- resources: `4 CPUs`, `256G`
- output target:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_1h_cleanup_20260519_S7474987`

早期检查：

- `2026-05-19 12:06 CST`: job 仍为 `RUNNING`
- `sacct` 仍只有 `job/batch/extern`，未出现旧问题中的 `hydra_bstrap_proxy` step 堆积
- `seed_forward/mpi_artifact_watch_summary.txt`:
  `mpi_hydra_bootstrap=fork`, `artifacts_ready=1`, `mpi_status=0`
- `cycle01_waccmx_cesm_feedback_package.h5` 已生成
- `cycle01_kaiju/waccmx_voltron_forward_package.h5` 已生成
- `manual_cesm_cycle02.log` 已生成，说明优化版 12-cycle 已进入第 2 个 CESM/WACCM-X 段
- 到 `cycle01_kaiju` 完整闭环约 `9 min`

完成结果：

- job id: `7474987`
- state: `COMPLETED`
- elapsed: `01:05:01`
- resources: `4 CPUs`, `256G`
- batch MaxRSS: `18066480K`
- node: `qhcn075`
- output:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_1h_cleanup_20260519_S7474987`
- output size: `3.8G`
- `final_summary.md`: 已生成
- `cycle01` 到 `cycle12` 的 WACCM-X feedback package 全部生成
- `cycle01_kaiju` 到 `cycle12_kaiju` 的 MPI Kaiju forward package 全部生成
- 12 个 feedback HDF5 + 12 个 forward HDF5 全部可读
- `sacct` 只有 `job/batch/extern`，没有残留 `hydra_bstrap_proxy` step

最终 contract:

- Hemisphere 1 `SIGMAP`: `0.186 .. 17.051 S`
- Hemisphere 1 `SIGMAH`: `0.249 .. 11.462 S`
- Hemisphere 2 `SIGMAP`: `0.173 .. 8.647 S`
- Hemisphere 2 `SIGMAH`: `0.301 .. 8.192 S`
- `NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s`

速度对比：

```text
旧 direct/file 12-cycle job 7270337: 01:02:15
旧 live_repair 12-cycle job 4747824: 01:09:34
未优化 MPI 12-cycle job 7469881: 04:00:27 TIMEOUT, only 8 cycles
优化 MPI 12-cycle job 7474987: 01:05:01 COMPLETED
```

结论：

- D 档 MPI file-bridge 12-cycle / 1h 已完成
- 优化后速度恢复到旧 direct/file 12-cycle 的同一量级
- 当前仍有 artifact-watch 主动终止 Voltron 导致的 `forrtl error (78): process killed (SIGTERM)` 记录，但不再导致 Slurm step 残留，也不影响顶层 `COMPLETED`

## Clean-exit 修复验证

目标：

- 不再依赖 artifact-watch 在 artifact 写出后主动 `SIGTERM` Voltron/MPI 进程组。
- 保留 artifact-watch 作为外层监督，但让 `voltron_mpi.x` 自然走到 `MPI_FINALIZE`。
- 验证范围先限定在 D 档 `WACCMX_FILE` 1-cycle，不直接覆盖 1h 基线结论。

源码修复：

- `src/voltron/mpi/modelInterfaces/gamCouple_mpi_G2V.F90`
  - 给 GAMERA-side coupler 增加 `stopRequested` 状态。
  - 当收到 Voltron 发送的停止哨兵 coupling time 时，将 GAMERA `Model%tFin` 收缩到当前时间并返回。
- `src/voltron/mpi/modelInterfaces/gamCouple_mpi_V2G.F90`
  - 增加 `sendGameraStopMpi`，由 Voltron-side coupler 发送最终停止哨兵。
- `src/voltron/mpi/voltapp_mpi.F90`
  - `waccmxStopAfterExport` 且 `waccmxExportDone` 后，先收尾正在进行的 GAMERA 更新，再发送停止哨兵，然后退出 Voltron loop。
- `run_long_coupling_stability.sh`
  - 增加测试开关 `KAIJU_MPI_REQUIRE_CLEAN_EXIT=1`。
  - 开关启用时，artifact-watch 不立即 kill，而是等待 MPI 自然退出；超时才判失败并清理。

构建：

```text
target: voltron_mpi.x
result: [100%] Built target voltron_mpi.x
binary: /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_mpi_build/bin/voltron_mpi.x
binary timestamp: 2026-05-19 13:28:19 +0800
```

验证作业：

```text
job id: 7475589
job name: waccmxDmpiCE1
state: COMPLETED
elapsed: 00:10:38
resources: 4 CPUs, 256G
batch MaxRSS: 16149620K
node: qhcn045
test name: waccmx_file_d_mpi_c1_cleanexit_20260519
num_cycles: 1
output: /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c1_cleanexit_20260519_S7475589
```

clean-exit 证据：

```text
seed_forward:
  clean_exit_required=1
  clean_exit_ready=1
  mpi_wait_status=0
  mpi_status=0

cycle01_kaiju:
  clean_exit_required=1
  clean_exit_ready=1
  mpi_wait_status=0
  mpi_status=0
```

日志检查：

- `seed_forward/launcher_mpi.log` 出现 `Fin Voltron Mpi`
- `cycle01_kaiju/launcher_mpi.log` 出现 `Fin Voltron Mpi`
- 未检出 `forrtl`
- 未检出 `SIGTERM`
- 未检出 `process killed`
- 未检出 `Timed out`
- 未检出 `ERROR/FATAL/Traceback/NaN`

HDF5 可读性：

```text
seed_forward/waccmx_voltron_forward_package.h5:
  Meta,NORTH_APEX,NORTH_GEO,NORTH_GRID,SOUTH_APEX,SOUTH_GEO,SOUTH_GRID

cycle01_waccmx_cesm_feedback_package.h5:
  feedback_apex_north,feedback_apex_south,feedback_geo_north,feedback_geo_south,meta

cycle01_kaiju/waccmx_voltron_forward_package.h5:
  Meta,NORTH_APEX,NORTH_GEO,NORTH_GRID,SOUTH_APEX,SOUTH_GEO,SOUTH_GRID
```

最终 contract：

```text
Hemisphere 1 SIGMAP: 0.147 .. 17.925 S
Hemisphere 1 SIGMAH: 0.176 .. 11.720 S
Hemisphere 2 SIGMAP: 0.112 .. 9.808 S
Hemisphere 2 SIGMAH: 0.199 .. 8.808 S
NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s
```

结论：

- D 档 `WACCMX_FILE` 1-cycle 已验证 MPI clean-exit。
- `forrtl error (78): process killed (SIGTERM)` 在 clean-exit 测试中已消失。
- 1h 基线 `7474987` 仍是已完成的变量闭环基线；clean-exit 补丁已通过短测，下一步可选择重跑 12-cycle 生成新的 clean-exit 1h 基线。

## Clean-exit 版 12-cycle / 1h 基线

在 `7475589` 的 1-cycle clean-exit 短测通过后，已用同一补丁重跑 `12 cycles = 1 h`：

```text
job id: 7475694
job name: waccmxDmpiCE1h
state: COMPLETED
elapsed: 01:10:54
resources: 4 CPUs, 256G
batch MaxRSS: 19830732K
node: qhcn181
test name: waccmx_file_d_mpi_1h_cleanexit_20260519
num_cycles: 12
output: /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_1h_cleanexit_20260519_S7475694
output size: 3.8G
```

完成状态：

- `final_summary.md` 已生成。
- `cycle01` 到 `cycle12` 的 WACCM-X feedback package 全部生成。
- `cycle01_kaiju` 到 `cycle12_kaiju` 的 MPI Kaiju forward package 全部生成。
- `seed_forward` 加 `cycle01_kaiju` 到 `cycle12_kaiju` 共 13 个 MPI 段全部有 `mpi_artifact_watch_summary.txt`。
- 13 个 MPI 段全部为 `clean_exit_ready=1`、`mpi_wait_status=0`、`mpi_status=0`、`artifacts_ready=1`。
- 12 个 WACCM-X feedback HDF5 和 12 个 Kaiju forward HDF5 全部可读。
- 错误关键字扫描未检出 `forrtl`、`SIGTERM`、`process killed`、`Timed out`、`ERROR`、`FATAL`、`Traceback`、`NaN`、`MPI_ABORT`。

最终 contract：

```text
Hemisphere 1
  Grid: 360 x 45
  SIGMAP min/max: 0.186 / 17.051 S
  SIGMAH min/max: 0.249 / 11.462 S
  NEUTRAL_DYNAMO_RHS absmax: 0.000 cm/s

Hemisphere 2
  Grid: 360 x 45
  SIGMAP min/max: 0.173 / 8.647 S
  SIGMAH min/max: 0.301 / 8.192 S
  NEUTRAL_DYNAMO_RHS absmax: 0.000 cm/s
```

HDF5 检查：

```text
seed forward packages: 1 readable
WACCM-X feedback packages: 12 readable
Kaiju forward packages: 12 readable
total checked HDF5 packages: 25 readable
```

结论：

- `7475694` 是当前最完整的 D 档 MAGE-WACCMX MPI file-bridge 1h 基线。
- 它同时满足变量闭环和 MPI clean-exit 两个条件。
- 相比 `7474987`，该版本去除了 artifact-watch 主动终止导致的 `forrtl/SIGTERM` 日志。
- 当前仍是 file-bridge 耦合，不是 native MPI communicator 或 CESM/CIME mediator。
- `neutral_rhs / NEUTRAL_DYNAMO_RHS` 仍为 `off`。

## 修改内容

新增：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/run_waccmx_file_officialD_mpi_export.sbatch`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_waccmx_file_officialD_mpi_export.sh`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_d_mpi_file_c1.sh`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_d_mpi_file_1h.sh`

增强：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_long_coupling_stability.sh`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh`

新增可选模式：

```text
KAIJU_LAUNCH_MODE=mpi_artifact_watch
KAIJU_VOLTRON_BIN=.../voltron_mpi.x
KAIJU_MPI_TOTAL_RANKS=2
SBATCH_TIME_LIMIT=04:00:00
SBATCH_JOB_NAME=waccmxDmpi1h
```

默认 `direct` 路径保持兼容，原有非 MPI 文件桥不应受影响。

## 诊断记录

失败/诊断作业：

- `7469217`: 2-rank + pin helper，不适合 D 档最小布局，`taskset` affinity 失败
- `7469231`: 2-rank 无 pin，能写出 artifact，但 MPI 进程不 clean exit
- `7469270`: 1-rank `doSerial=F`，卡在 Voltron 初始化后
- `7469296`: 1-rank `doSerial=T`，同样未推进到 export
- `7469368`: bridge driver 缺少 `libiomp5.so` runtime 路径
- `7469411`: bridge driver 使用了 Slurm `mpiexec`，不是 oneAPI `mpiexec.hydra`

解决：

- 对 D 档 MPI smoke 使用 `2 ranks`, `doSerial=F`, `no pin`
- 使用 oneAPI `mpiexec.hydra -f hostfile`
- 补入 oneAPI compiler runtime、oneAPI MPI runtime、HDF5 runtime library path
- 使用 artifact-watch 作为当前过渡期退出机制

## 当前边界

已经完成：

- D 档 MPI `voltron_mpi.x` 可以生成 `WACCMX_FILE` forward package
- D 档 MPI Kaiju 可以接收 WACCM-X feedback package 并再次导出 forward package
- CESM/WACCM-X 一轮可夹在两个 MPI Kaiju 段之间完成变量闭环
- `12 cycles = 1 h` 已完成变量闭环基线验证
- `1 cycle` 已完成 MPI clean-exit 短测验证
- clean-exit 版 `12 cycles = 1 h` 已完成，job `7475694`

尚未完成：

- 原生 MPI communicator 变量交换
- CESM/CIME mediator 接入
- `neutral_rhs / NEUTRAL_DYNAMO_RHS` 物理正式闭环

## Neutral RHS 当前进展

`neutral_rhs / NEUTRAL_DYNAMO_RHS` 已完成两类 D 档 2-cycle 工程短测：

```text
job_id = 7477415
test_name = waccmx_file_d_mpi_c2_nsrhs_geo_cleanexit_20260519
transform = none
state = COMPLETED
result = path connected, but RHS too large
```

该测试证明：

- WACCM-X 可以输出 `mage_waccmx_nsrhs_geo_rank*.txt`。
- bridge 可以把它打包进 `waccmx_voltron_feedback_package.h5`。
- MAGE/Voltron 可以读取 `NEUTRAL_DYNAMO_RHS` slot。
- 但 `neutral_rhs_absmax` 约 `5.4e7` 到 `5.7e7`，量级过大。
- WACCM-X 后续出现 potential clamp：`11787.761 -> 150.000`。

随后完成缩放短测：

```text
job_id = 7479764
test_name = waccmx_file_d_mpi_c2_nsrhs_geo_tiegcm_scale_20260519
transform = solver_to_tiegcm_coupler_like
state = COMPLETED
elapsed = 00:15:27
output = /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c2_nsrhs_geo_tiegcm_scale_20260519_S7479764
```

该测试结果：

- 三个 MPI 段全部 clean exit。
- `cycle01` 和 `cycle02` HDF5 均可读，且 `nsrhs_transform=solver_to_tiegcm_coupler_like`。
- `cycle01 neutral_rhs_absmax` 约北半球 `1.3539e-6`、南半球 `1.3293e-6`。
- `cycle02 neutral_rhs_absmax` 约北半球 `1.3395e-6`、南半球 `1.3001e-6`。
- WACCM-X 不再触发 potential clamp：`12.047 -> 12.047` 和 `14.313 -> 14.313`。

当前判断：

- `neutral_rhs` 工程链路已经打通。
- `none` 量级过强，`solver_to_tiegcm_coupler_like` 数值稳定但可能过弱。
- `scale=1e-2` 是当前最好的 2-cycle 候选，已经产生明显响应且未触发 WACCM-X limiter。

## Neutral RHS Scale Bracket

新增了非破坏性的 `WACCMX_NSRHS_SCALE` 参数：

```text
default = 1.0
location = cesm_feedback_to_kaiju_feedback.py + run_long_coupling_stability.sh
```

该参数应用在 `WACCMX_NSRHS_TRANSFORM` 之后。默认值为 `1.0`，所以不会改变已有运行。

已完成第一档 bracket：

```text
job_id = 7480741
test_name = waccmx_file_d_mpi_c2_nsrhs_geo_scale1e2_20260519
transform = none
scale = 1e-2
state = COMPLETED
elapsed = 00:15:26
output = /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c2_nsrhs_geo_scale1e2_20260519_S7480741
```

结果：

- 三个 MPI 段全部 clean exit。
- HDF5 meta 正确记录 `nsrhs_scale=0.01`。
- `cycle01 neutral_rhs_absmax` 约北半球 `5.6645e5`、南半球 `5.5616e5`。
- `cycle02 neutral_rhs_absmax` 约北半球 `5.6043e5`、南半球 `5.4394e5`。
- `cycle01` WACCM-X external potential 为 `12.047 -> 12.047`。
- `cycle02` WACCM-X external potential 为 `113.883 -> 113.883`。
- 未检出 `forrtl`、`SIGTERM`、`process killed`、`ERROR`、`FATAL`、`Traceback`、`NaN`、`MPI_ABORT`。

判断：

- `scale=1e-2` 比 `solver_to_tiegcm_coupler_like` 的 `~1e-6` RHS 更有动力学影响。
- `scale=1e-2` 仍低于 WACCM-X `150` limiter，没有被截断。
- 当前不建议继续增大到接近 limiter；应先用 `scale=1e-2` 做更长 cycle 稳定性验证。

## 下一步建议

1. 将 `7475694` 作为当前 D 档 clean-exit 1h 正式基线。
2. 将 `7479764` 作为 `neutral_rhs` 过弱缩放参考。
3. 将 `7480741` 作为当前 `neutral_rhs` 最佳 2-cycle 候选。
4. 用 `scale=1e-2` 扩展到 4-cycle 或 12-cycle，检查是否累积触发 limiter。
5. 稳定后再扩展为 1h `neutral_rhs` 候选基线。
6. 在 D 档文件桥稳定后，开始把文件交换替换成 pipe/socket/MPI side-channel。
7. 最后再评估原生 MPI communicator 或 CESM/CIME mediator 接入。
