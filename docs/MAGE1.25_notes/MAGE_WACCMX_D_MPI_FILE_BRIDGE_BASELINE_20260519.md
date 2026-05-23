# MAGE-WACCMX D 档 MPI File-Bridge 1h 基线

日期：2026-05-19

## 基线定义

基线名称：`D_MPI_FILE_BRIDGE_1H_V1`

该基线表示当前已经验证成功的 MAGE1.25-WACCMX 耦合状态：

```text
MAGE/Kaiju Voltron MPI export
  -> WACCM-X file bridge
  -> CESM/WACCM-X continuation segment
  -> WACCM-X feedback HDF5
  -> MAGE/Kaiju Voltron MPI ingest/export
```

边界：

- 这是 D 档 `WACCMX_FILE` 文件桥闭环。
- MAGE/Kaiju 侧使用 `voltron_mpi.x` 和 `mpiexec`。
- WACCM-X/CESM 侧没有进入同一个 MPI communicator。
- 当前不是 CESM/CIME mediator 耦合，也不是 native MPI model-to-model 耦合。
- `neutral_rhs / NEUTRAL_DYNAMO_RHS` 当前保持关闭，`NSRHS=off`。

## 成功作业

Slurm 作业：

```text
job_id      = 7474987
job_name    = waccmxDmpi1h
state       = COMPLETED
elapsed     = 01:05:01
alloc_cpus  = 4
requested_memory = 256G
batch_maxrss = 18066480K
node        = qhcn075
```

输出目录：

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_1h_cleanup_20260519_S7474987
```

输出规模：

```text
3.8G
```

## 可复现入口

提交脚本：

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_d_mpi_file_1h.sh
```

主驱动：

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_long_coupling_stability.sh
```

Voltron MPI 可执行文件：

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_mpi_build/bin/voltron_mpi.x
```

关键运行参数：

```text
TEST_NAME=waccmx_file_d_mpi_1h_cleanup_20260519
NUM_CYCLES=12
SBATCH_TIME_LIMIT=03:00:00
KAIJU_LAUNCH_MODE=mpi_artifact_watch
KAIJU_MPI_TOTAL_RANKS=2
KAIJU_DO_SERIAL=F
KAIJU_MPI_HYDRA_BOOTSTRAP=fork
KAIJU_MPI_POST_ARTIFACT_GRACE_SECONDS=2
KAIJU_GCM_BACKEND=WACCMX_FILE
WACCMX_NSRHS_SOURCE_MODE=off
```

重跑命令：

```bash
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_d_mpi_file_1h.sh
```

## 交换变量

MAGE/Voltron 到 WACCM-X：

```text
POT
AVG_ENG
NUM_FLUX
```

WACCM-X 到 MAGE/REMIX：

```text
SIGMAP
SIGMAH
```

当前 contract 中也保留了 `NEUTRAL_DYNAMO_RHS` 槽位，但本基线中为关闭状态：

```text
NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s
```

## 验收结果

`final_summary.md` 已生成，`num_cycles=12`。

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

文件完整性：

- `cycle01` 到 `cycle12` 的 WACCM-X feedback package 全部生成。
- `cycle01_kaiju` 到 `cycle12_kaiju` 的 MPI Kaiju forward package 全部生成。
- 12 个 feedback HDF5 和 12 个 forward HDF5 均已验证可读。
- `sacct` 只显示 `job/batch/extern`，没有旧问题中的残留 `hydra_bstrap_proxy` step。

## 性能对比

```text
旧 direct/file 12-cycle job 7270337: 01:02:15 COMPLETED
旧 live_repair 12-cycle job 4747824: 01:09:34 COMPLETED
未优化 MPI 12-cycle job 7469881: 04:00:27 TIMEOUT, only 8 cycles
优化 MPI 12-cycle job 7474987: 01:05:01 COMPLETED
```

结论：

- 优化后的 D 档 MPI file-bridge 1h 运行速度已经恢复到旧 direct/file 12-cycle 的同一量级。
- 旧的慢速问题来自 MPI artifact-watch 清理不完整导致 Hydra/Voltron step 残留累积。
- 当前 `fork + setsid + process-group cleanup` 已消除残留 Slurm step。

## 已知限制

当前仍可在 MPI launcher 日志中看到：

```text
forrtl: error (78): process killed (SIGTERM)
```

解释：

- 这是 artifact-watch 在 forward package 写出后主动终止 Voltron/MPI 进程组导致的日志。
- 它不再造成 Slurm step 残留。
- 它不影响 `7474987` 顶层作业 `COMPLETED`。
- 但这还不是正式 clean-exit，后续应把 `stopAfterExport=T` 的 MPI 退出路径做成自然退出，而不是外部 kill。

## Post-baseline Clean-exit

`7474987` 保持为最早完成的 D 档 1h 变量闭环基线。

在该基线之后，已完成一个独立的 clean-exit 短测：

```text
job_id = 7475589
test_name = waccmx_file_d_mpi_c1_cleanexit_20260519
num_cycles = 1
state = COMPLETED
elapsed = 00:10:38
```

该短测中：

- `seed_forward` 和 `cycle01_kaiju` 均为 `clean_exit_ready=1`。
- `mpi_wait_status=0`。
- `mpi_status=0`。
- 日志出现 `Fin Voltron Mpi`。
- 未检出 `forrtl`、`SIGTERM` 或 `process killed`。

因此 clean-exit 补丁已通过 1-cycle 验证；如需把基线也升级为无 `SIGTERM` 版本，需要重跑 `12 cycles = 1 h`。

clean-exit 版 12-cycle / 1h 已随后完成：

```text
job_id = 7475694
test_name = waccmx_file_d_mpi_1h_cleanexit_20260519
num_cycles = 12
state = COMPLETED
elapsed = 01:10:54
output = /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_1h_cleanexit_20260519_S7475694
```

该运行中：

- 13 个 MPI 段全部 `clean_exit_ready=1`。
- 13 个 MPI 段全部 `mpi_wait_status=0`、`mpi_status=0`。
- 12 个 WACCM-X feedback HDF5 和 12 个 Kaiju forward HDF5 全部可读。
- 未检出 `forrtl`、`SIGTERM`、`process killed`。

因此当前推荐把 `7475694` 作为 D 档 clean-exit 1h 正式基线。

## Neutral RHS 2-cycle Probe

在 `7475694` 之后，已完成一个独立的 `neutral_rhs / NEUTRAL_DYNAMO_RHS` 路径短测：

```text
job_id = 7477415
test_name = waccmx_file_d_mpi_c2_nsrhs_geo_cleanexit_20260519
num_cycles = 2
state = COMPLETED
elapsed = 00:16:32
output = /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c2_nsrhs_geo_cleanexit_20260519_S7477415
```

运行模式：

```text
WACCMX_NSRHS_SOURCE_MODE=geo_sidecar
WACCMX_NSRHS_UNFOLDING=none
WACCMX_NSRHS_TRANSFORM=none
KAIJU_MPI_REQUIRE_CLEAN_EXIT=1
```

工程验收：

- `cycle01` 和 `cycle02` 均生成 `mage_waccmx_nsrhs_geo_rank*.txt`。
- `cycle01_waccmx_cesm_feedback_package.h5` 和 `cycle02_waccmx_cesm_feedback_package.h5` 均为 `nsrhs_source=nsrhs_geo_sidecar`。
- `nsrhs_projection=direct_mag_to_geo_2d_sidecar`。
- `seed_forward`、`cycle01_kaiju`、`cycle02_kaiju` 三个 MPI 段全部 clean exit。
- 7 个 HDF5 package 全部可读。
- 未检出 `forrtl`、`SIGTERM`、`process killed`、`ERROR`、`FATAL`、`Traceback`、`NaN`、`MPI_ABORT`。

物理/数值限制：

- `cycle01` 的 `neutral_rhs_absmax` 约为北半球 `5.6645e7 cm/s`、南半球 `5.5616e7 cm/s`。
- `cycle02` 的 `neutral_rhs_absmax` 约为北半球 `5.6043e7 cm/s`、南半球 `5.4394e7 cm/s`。
- Voltron contract 中 `NEUTRAL_DYNAMO_RHS absmax` 因量级过大显示为 `********** cm/s`。
- cycle02 WACCM-X 日志出现 `d_pie_set_external_epot: input/limited absmax 11787.761 -> 150.000`。

结论：

- `neutral_rhs` 工程路径已接通。
- 该短测不是新的物理正式基线，因为 `NEUTRAL_DYNAMO_RHS` 单位/缩放还需要修正。

## Neutral RHS Scaled 2-cycle Probe

随后完成了一个 `solver_to_tiegcm_coupler_like` 缩放短测：

```text
job_id = 7479764
test_name = waccmx_file_d_mpi_c2_nsrhs_geo_tiegcm_scale_20260519
num_cycles = 2
state = COMPLETED
elapsed = 00:15:27
output = /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c2_nsrhs_geo_tiegcm_scale_20260519_S7479764
```

运行模式：

```text
WACCMX_NSRHS_SOURCE_MODE=geo_sidecar
WACCMX_NSRHS_UNFOLDING=none
WACCMX_NSRHS_TRANSFORM=solver_to_tiegcm_coupler_like
KAIJU_MPI_REQUIRE_CLEAN_EXIT=1
```

工程验收：

- Slurm 状态为 `COMPLETED 0:0`。
- `seed_forward`、`cycle01_kaiju`、`cycle02_kaiju` 三个 MPI 段全部 `clean_exit_ready=1`。
- 三个 MPI 段全部 `mpi_wait_status=0`、`mpi_status=0`。
- `cycle01_waccmx_cesm_feedback_package.h5` 和 `cycle02_waccmx_cesm_feedback_package.h5` 均为 `nsrhs_source=nsrhs_geo_sidecar`、`nsrhs_transform=solver_to_tiegcm_coupler_like`。
- 未检出 `forrtl`、`SIGTERM`、`process killed`、`ERROR`、`FATAL`、`Traceback`、`NaN`、`MPI_ABORT`。

数值结果：

- `cycle01` 的 `neutral_rhs_absmax` 约为北半球 `1.3539e-6`、南半球 `1.3293e-6`。
- `cycle02` 的 `neutral_rhs_absmax` 约为北半球 `1.3395e-6`、南半球 `1.3001e-6`。
- `cycle01` WACCM-X 日志为 `d_pie_set_external_epot: input/limited absmax 12.047 -> 12.047`。
- `cycle02` WACCM-X 日志为 `d_pie_set_external_epot: input/limited absmax 14.313 -> 14.313`。

结论：

- `solver_to_tiegcm_coupler_like` 缩放解决了上一轮 `11787.761 -> 150.000` 的 potential clamp 问题。
- 该测试说明缩放后的 `neutral_rhs` 路径可以完成 2-cycle clean-exit。
- 但 `neutral_rhs_absmax` 被压到约 `1e-6`，很可能过弱；它是数值稳定候选，不应直接作为物理正式基线。

## Neutral RHS Bracket 2-cycle Probe

为避免 `solver_to_tiegcm_coupler_like` 过度缩放，新增了一个可控倍率参数：

```text
WACCMX_NSRHS_SCALE
```

实现位置：

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cesm_feedback_to_kaiju_feedback.py
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_long_coupling_stability.sh
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_d_mpi_file_c2_cleanup_probe.sh
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh
```

默认值为 `1.0`，因此不会改变原有 `NSRHS=off`、`none`、`solver_to_tiegcm_coupler_like` 行为。

完成的第一档 bracket：

```text
job_id = 7480741
test_name = waccmx_file_d_mpi_c2_nsrhs_geo_scale1e2_20260519
num_cycles = 2
state = COMPLETED
elapsed = 00:15:26
output = /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_c2_nsrhs_geo_scale1e2_20260519_S7480741
```

运行模式：

```text
WACCMX_NSRHS_SOURCE_MODE=geo_sidecar
WACCMX_NSRHS_UNFOLDING=none
WACCMX_NSRHS_TRANSFORM=none
WACCMX_NSRHS_SCALE=1e-2
KAIJU_MPI_REQUIRE_CLEAN_EXIT=1
```

工程验收：

- Slurm 状态为 `COMPLETED 0:0`。
- `seed_forward`、`cycle01_kaiju`、`cycle02_kaiju` 三个 MPI 段全部 `clean_exit_ready=1`。
- 三个 MPI 段全部 `mpi_wait_status=0`、`mpi_status=0`。
- `cycle01_waccmx_cesm_feedback_package.h5` 和 `cycle02_waccmx_cesm_feedback_package.h5` 均为 `nsrhs_source=nsrhs_geo_sidecar`、`nsrhs_transform=none`、`nsrhs_scale=0.01`。
- 未检出 `forrtl`、`SIGTERM`、`process killed`、`ERROR`、`FATAL`、`Traceback`、`NaN`、`MPI_ABORT`。

数值结果：

- `cycle01` 的 `neutral_rhs_absmax` 约为北半球 `5.6645e5`、南半球 `5.5616e5`。
- `cycle02` 的 `neutral_rhs_absmax` 约为北半球 `5.6043e5`、南半球 `5.4394e5`。
- `cycle01` WACCM-X 日志为 `d_pie_set_external_epot: input/limited absmax 12.047 -> 12.047`。
- `cycle02` WACCM-X 日志为 `d_pie_set_external_epot: input/limited absmax 113.883 -> 113.883`。

结论：

- `scale=1e-2` 明显强于 `solver_to_tiegcm_coupler_like`，不是近零响应。
- `scale=1e-2` 仍未触发 WACCM-X `150` limiter。
- 这是当前 `neutral_rhs` 的最佳 2-cycle 数值候选，但还需要更长 cycle 验证后才能升为正式基线。

## 下一步

推荐后续顺序：

1. 保持 `7475694` 作为 `NSRHS=off` 的 D 档 clean-exit 1h 正式基线。
2. 保留 `7479764` 作为 `neutral_rhs` 过弱缩放参考。
3. 保留 `7480741` 作为当前 `neutral_rhs` 最佳 2-cycle 候选。
4. 先用 `scale=1e-2` 扩展到 4-cycle 或 12-cycle，检查是否累积触发 limiter。
5. 通过更长 cycle 后，再升级为 1h `neutral_rhs` 候选基线。
6. 在 file-bridge 稳定后，再讨论 native MPI communicator 或 CESM/CIME mediator。
