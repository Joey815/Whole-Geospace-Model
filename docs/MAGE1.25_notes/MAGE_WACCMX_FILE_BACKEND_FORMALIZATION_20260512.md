# MAGE-WACCMX WACCMX_FILE 后端正式化记录

Date: 2026-05-12

## 目的

将当前文件桥运行入口从历史 `WACCMX_STUB` 默认语义切换为正式 `WACCMX_FILE` 默认语义。

这一步不改变物理变量或耦合算法，只改变默认运行路径，避免后续误用旧 stub 后端。

## 已改入口

已将默认后端改为 `WACCMX_FILE`：

- `experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh`
- `experiments/cesm_kaiju_bridge/slurm/run_live_repair_plus1h.sbatch`
- `experiments/cesm_kaiju_bridge/run_long_coupling_stability.sh`
- `experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`
- `experiments/cesm_kaiju_bridge/run_one_aggressive_test.sh`
- `experiments/kaiju_waccmx_coupling/scripts/waccmx_stub/run_voltron_smoke.sh`

保留显式回退能力：

```bash
KAIJU_GCM_BACKEND=WACCMX_STUB
```

当前正式默认：

```bash
KAIJU_GCM_BACKEND=WACCMX_FILE
WACCMX_NSRHS_SOURCE_MODE=off
WACCMX_REPAIR_OP_HOOK=0
```

## 静态检查

以下脚本通过 `bash -n`：

- `submit_fresh_rebuild_plus1h.sh`
- `run_live_repair_plus1h.sbatch`
- `run_long_coupling_stability.sh`
- `run_bidirectional_cycle.sh`
- `run_one_aggressive_test.sh`
- `run_voltron_smoke.sh`

严格 preflight 通过：

```bash
WACCMX_REPAIR_OP_HOOK=0 KAIJU_GCM_BACKEND=WACCMX_FILE \
  experiments/cesm_kaiju_bridge/preflight_mage_waccmx_runtime.sh \
  --mode live-1h --strict
```

## 1-cycle 验证

提交命令：

```bash
TEST_NAME=waccmx_file_formal_c1_20260512 \
NUM_CYCLES=1 \
KAIJU_GCM_BACKEND=WACCMX_FILE \
WACCMX_NSRHS_SOURCE_MODE=off \
  experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh
```

Slurm 作业：

- job id: `7276621`
- state: `COMPLETED`
- node: `qhcn090`
- elapsed: `00:08:59`
- allocated CPUs: `4`
- requested memory: `256G`
- batch MaxRSS: `18101264K`

结果目录：

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_formal_c1_20260512_S7276621
```

关键证据：

- Slurm 输出中记录 `kaiju_gcm_backend=WACCMX_FILE`
- `LONG_STABILITY_DONE waccmx_file_formal_c1_20260512`
- final summary 中记录 `kaiju_gcm_backend: WACCMX_FILE`
- contract 标题为 `# WACCMX_FILE contract summary`
- Voltron XML 记录 `gcmBackend="WACCMX_FILE"`
- WACCM-X feedback package 已生成：
  `cycle01_waccmx_cesm_feedback_package.h5`

## 变量闭环状态

本次验证仍是正式电动力学闭环，`NSRHS=off`：

MAGE/VOLTRON -> WACCM-X：

- `POT`
- `AVG_ENG`
- `NUM_FLUX`

WACCM-X -> MAGE/REMIX：

- `SIGMAP`
- `SIGMAH`

final contract 中的 conductance 范围：

- Hemisphere 1:
  - `SIGMAP`: `0.138 .. 17.676 S`
  - `SIGMAH`: `0.136 .. 11.635 S`
- Hemisphere 2:
  - `SIGMAP`: `0.109 .. 10.063 S`
  - `SIGMAH`: `0.157 .. 8.839 S`

`NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s`，符合当前 `NSRHS=off` 设置。

## 3-cycle 连续验证

提交命令：

```bash
TEST_NAME=waccmx_file_formal_c3_20260512 \
NUM_CYCLES=3 \
KAIJU_GCM_BACKEND=WACCMX_FILE \
WACCMX_NSRHS_SOURCE_MODE=off \
  experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh
```

Slurm 作业：

- job id: `7276731`
- state: `COMPLETED`
- node: `qhcn090`
- elapsed: `00:18:53`
- allocated CPUs: `4`
- requested memory: `256G`
- batch MaxRSS: `22008976K`

结果目录：

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_formal_c3_20260512_S7276731
```

关键证据：

- Slurm 输出中记录 `kaiju_gcm_backend=WACCMX_FILE`
- `LONG_STABILITY_DONE waccmx_file_formal_c3_20260512`
- `cycle01 / cycle02 / cycle03` 均写出 CESM rank import 文件
- `cycle01 / cycle02 / cycle03` 均写出 WACCM-X feedback package
- `cycle01 / cycle02 / cycle03` 的 contract 均为 `# WACCMX_FILE contract summary`
- 未发现 `ERROR / SIGSEGV / forrtl / NaN / Inf / Traceback / FAILED / STOP` 关键错误

最终 contract 中的 conductance 范围：

- Hemisphere 1:
  - `SIGMAP`: `0.138 .. 17.691 S`
  - `SIGMAH`: `0.136 .. 11.636 S`
- Hemisphere 2:
  - `SIGMAP`: `0.110 .. 10.050 S`
  - `SIGMAH`: `0.157 .. 8.838 S`

输出规模：

- 文件数: `116`
- 目录大小: `1.2G`

## 12-cycle clean 1h 验证

说明：

- 本地已有旧的 `waccmx_file_1h_20260512_S7270337` 12-cycle 结果，但旧结果的 Kaiju launcher 日志中仍含旧式 `forrtl: error (78): process killed (SIGTERM)`。
- 因此重新提交 clean-exit 12-cycle，用于验证当前正式入口不再依赖 kill 掉 Voltron 的旧流程。

提交命令：

```bash
TEST_NAME=waccmx_file_formal_1h_clean_20260512 \
NUM_CYCLES=12 \
KAIJU_GCM_BACKEND=WACCMX_FILE \
WACCMX_NSRHS_SOURCE_MODE=off \
  experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh
```

Slurm 作业：

- job id: `7276927`
- state: `COMPLETED`
- node: `qhcn585`
- elapsed: `01:06:45`
- allocated CPUs: `4`
- requested memory: `256G`
- batch MaxRSS: `19182924K`

结果目录：

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_formal_1h_clean_20260512_S7276927
```

关键证据：

- Slurm 输出中记录 `kaiju_gcm_backend=WACCMX_FILE`
- `LONG_STABILITY_DONE waccmx_file_formal_1h_clean_20260512`
- `cycle01` 到 `cycle12` 均写出 CESM rank import 文件
- `cycle01` 到 `cycle12` 均写出 WACCM-X feedback package
- final summary 中记录 `kaiju_gcm_backend: WACCMX_FILE`
- final contract 标题为 `# WACCMX_FILE contract summary`
- 未发现 `forrtl / SIGSEGV / ERROR / FAILED / Traceback / NaN / Inf / STOP` 关键错误

最终 contract 中的 conductance 范围：

- Hemisphere 1:
  - `SIGMAP`: `0.138 .. 17.691 S`
  - `SIGMAH`: `0.136 .. 11.636 S`
- Hemisphere 2:
  - `SIGMAP`: `0.110 .. 10.050 S`
  - `SIGMAH`: `0.157 .. 8.838 S`

输出规模：

- 文件数: `404`
- 目录大小: `3.8G`

## 当前结论

`WACCMX_FILE` 已经是当前文件桥正式默认入口，并且完成 `1 cycle`、`3 cycles`、`12 cycles = 1 h` clean-exit 连续验证。

这一步不等同于 native MPI 或 CESM mediator 在线耦合；它确认的是正式文件耦合后端的默认入口可运行。

## 下一步

按当前路线继续：

1. 切到 `O` 档做 `1 cycle`
2. 通过后做 `O` 档 `3 cycles`
3. 再评估是否把 `neutral_rhs / NEUTRAL_DYNAMO_RHS` 加入正式路线
