# MAGE-TIEGCM `gnsrhs` 多发送时刻快照捕获

日期：2026-03-27

## 1. 这次解决了什么

前一轮只能拿到单帧 `gnsrhs` 快照，后续若要做 `WACCM-X NSRHS` 与
`TIEGCM gnsrhs` 的逐发送时刻对齐，会受限于：

- 同名文件覆盖
- 无法区分不同发送时刻

这次已经把 `TIEGCM` 诊断导出改成：

- `MAGE_TIEGCM_GNSRHS_DIAG_MODE=step`

即按 `istep` 留档，输出形如：

- `mage_tiegcm_gnsrhs_geo_step00000001_rank000000.txt`

## 2. 关键代码与运行

### 代码

- [pdynamo.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F)

新增逻辑：

- 默认模式继续保留旧的 `mage_tiegcm_gnsrhs_geo_rank*.txt`
- 若 `MAGE_TIEGCM_GNSRHS_DIAG_MODE=step`
  - 输出改为 `mage_tiegcm_gnsrhs_geo_stepXXXXXXXX_rankYYYYYY.txt`

### 运行

多帧捕获 run：

- [gtrd_smoke20_gnsrhs_steps_20260327b](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_steps_20260327b)

提交脚本：

- [run_gtrd_smoke20_gnsrhs_diag.sbatch](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/slurm/run_gtrd_smoke20_gnsrhs_diag.sbatch)

作业号：

- `4728444`

## 3. 结果

这次 run 已经在同一个短程 `MAGE-TIEGCM` coupled smoke 中，捕获到多个 step：

- `00000001`
- `00000002`
- `00000003`
- `00000004`

也就是说，现在已经不再是“只能比第一帧”，而是至少具备了：

- 多发送时刻 `TIEGCM gnsrhs`
- 可做逐发送时刻 cross-model 对齐

## 4. 当前意义

这一步非常关键，因为它把下一步工作从：

- “继续猜符号和缩放”

推进到了：

- “真正做逐发送时刻对齐”

换句话说，现在 `TIEGCM` 这一侧的时序抓取能力已经具备，后续剩下的主要工作是：

1. 给 `WACCM-X` 侧建立同类时序快照保留
2. 逐发送时刻比较：
   - correlation
   - sign agreement
   - 最佳缩放常数
3. 再决定最终 `NSRHS -> gnsrhs` 的物理对齐方式

## 5. 当前最准确的阶段判断

截至这一步：

- `TIEGCM gnsrhs` 单帧对齐已经完成
- `TIEGCM gnsrhs` 多帧时序抓取已经完成

所以后续 `NSRHS` 线真正的下一步，不再是继续改 `TIEGCM` 导出，而是：

- 补 `WACCM-X` 侧同类时序快照
- 然后做逐时刻对齐
