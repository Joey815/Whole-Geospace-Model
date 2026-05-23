# MAGE 1.25 与 WACCM-X 真实双向文件耦合闭环：一页汇报版

日期：2026-03-25

## 1. 核心结论

截至 2026-03-25，`MAGE 1.25` 与 `WACCM-X(CESM)` 的**真实双向文件耦合闭环已经跑通**。

这里的“完成”指的是：

- 第一轮真实 `voltron.x` 从 `MAGE/REMIX` 产生前向耦合量
- 真实 `CESM/WACCM-X` 读取桥接后的输入文件并完成一次真实 `cesm.exe` 运行
- `CESM/WACCM-X` 输出反馈电导
- 第二轮真实 `voltron.x` 成功读回 `CESM` 反馈并改写自身电导状态

这里的“未完成”指的是：

- 这还不是 `MAGE + TIEGCM` 那种在线 `MPI`/内存直连耦合
- 当前实现仍然是**真实模型 + 文件桥接**

## 2. 本次跑通的真实闭环链路

本次完成的链路是：

`MAGE/voltron -> forward package -> CESM/WACCM-X import files -> cesm.exe -> feedback rank files -> feedback HDF5 -> second voltron`

对应的完整端到端运行目录：

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a`

桥接入口脚本：

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`

## 3. 关键工件

Step 1：`MAGE -> WACCM-X`

- 前向包：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/step1_kaiju_forward/waccmx_voltron_forward_package.h5`

CESM/WACCM-X 阶段：

- 真实运行日志：
  `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run/manual_cesm_kaiju_cycle.log`
- 结束标志：
  `med_finalize max rss=5432193024.0 MB`

WACCM-X -> MAGE 反馈阶段：

- 反馈包：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/waccmx_cesm_feedback_package.h5`

Step 2：`MAGE <- WACCM-X`

- 第二轮 contract：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/step2_kaiju_feedback/waccmx_voltron_contract.txt`
- 第二轮 exchange：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/step2_kaiju_feedback/waccmx_voltron_exchange.md`
- 第二轮前向包：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/fixepot_e2e_20260325a/step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

## 4. 为什么可以认定“闭环完成”

判断标准不是“文件写出来了”，而是**第二轮 `voltron` 的物理量确实变了**。

第一轮 `voltron` 的默认电导范围为：

- Hemisphere 1: `SIGMAP 5.000 .. 14.966 S`, `SIGMAH 2.000 .. 7.980 S`
- Hemisphere 2: `SIGMAP 5.000 .. 14.966 S`, `SIGMAH 2.000 .. 7.980 S`

第二轮 `voltron` 读入 `CESM` 反馈后变为：

- Hemisphere 1: `SIGMAP 0.138 .. 17.678 S`, `SIGMAH 0.136 .. 11.635 S`
- Hemisphere 2: `SIGMAP 0.109 .. 10.062 S`, `SIGMAH 0.157 .. 8.839 S`

这说明第二轮 `voltron` 没有保留默认椭圆电导，而是**确实吃进了 `WACCM-X/CESM` 反馈**。

## 5. 这次真正解锁闭环的两个技术点

### 5.1 `external epot` 路径真正打通

关键入口：

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90`

处理方式是：

- 在 external `MAGE epot` 分支里，先调用标准 `d_pie_epotent(...)` 初始化 `edynamo/ESMF`
- 然后再调用 `d_pie_set_external_epot(...)` 用 `MAGE` 输入覆盖 `phihm`

这个顺序避免了之前直接走 external `epot` 时触发的 `ESMF_FieldGet rc = 51` 问题。

### 5.2 `MAGE -> WACCM-X` 的 `epot` 网格尺寸改对

关键入口：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py`

处理方式是：

- 从 `NORTH_APEX/SOUTH_APEX` 的 `POT` 采样
- 写出 `WACCM-X` 需要的全局磁网格 `mage_waccmx_epot_global.txt`
- 尺寸改成正确的 `7760` 点格式，从而消除了此前的 `MAGE epot size mismatch`

## 6. 当前边界

已经完成：

- 真实 `MAGE/voltron` 参与
- 真实 `CESM/WACCM-X` 参与
- 真实双向交换
- 端到端脚本一次跑完整个文件闭环

尚未完成：

- 在线 `MPI` 直连耦合
- `CIME/CMEPS/mediator` 原生组件级集成
- `neutral_rhs` 的真实物理回传仍然是占位处理

## 7. 一句话结论

**现在已经可以正式表述为：我们完成了 `MAGE 1.25` 与 `WACCM-X(CESM)` 的真实双向文件耦合闭环验证；该闭环由真实 `voltron.x` 与真实 `cesm.exe` 通过文件桥接实现，并已证明 `WACCM-X` 反馈能够回写并改变第二轮 `MAGE/REMIX` 电导状态。**
