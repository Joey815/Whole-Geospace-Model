# MAGE-WACCMX 与 MAGE-TIEGCM `gnsrhs / NSRHS` 首次 MAGE 驱动对比

日期：2026-03-27

## 1. 这次做了什么

这次不再使用前面的 `standalone quiet Heelis` `TIEGCM` 诊断，而是重新跑了一次真实的
`MAGE-TIEGCM` 短程 coupled smoke，并在 `TIEGCM` 侧打开：

- `MAGE_TIEGCM_WRITE_GNSRHS_DIAG=1`

运行目录：

- [/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_20260327a](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_20260327a)

关键快照：

- `TIEGCM gnsrhs` 首次发送快照：
  [gnsrhs_snapshot_firstsend](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_20260327a/gnsrhs_snapshot_firstsend)
- `WACCM-X` 当前 canonical 候选包：
  [waccmx_cesm_feedback_package_geo_direct_crossmodel.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/waccmx_cesm_feedback_package_geo_direct_crossmodel.h5)
- 自动对比报告：
  [tiegcm_waccmx_nsrhs_compare_firstsend.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_20260327a/tiegcm_waccmx_nsrhs_compare_firstsend.md)

## 2. 结果

### 北半球

- correlation: `0.102874`
- sign agreement: `0.462593`
- `alpha_tiegcm_per_waccm`: `1.8917e-02`
- raw RMSE: `1.6662e-07`
- RMSE after alpha scaling: `3.0583e-08`

### 南半球

- correlation: `0.154007`
- sign agreement: `0.601173`
- `alpha_tiegcm_per_waccm`: `5.4551e-02`
- raw RMSE: `1.6458e-07`
- RMSE after alpha scaling: `5.7199e-08`

## 3. 这组结果说明什么

这组结果比前面的 `standalone quiet Heelis` 对比更有信息量。

前面的结论是：

- 相关性接近 `0`，北半球甚至略负

这次改成真实 `MAGE` 驱动的 `TIEGCM` 之后：

- 南北半球相关系数都转成了**正值**
- 而且经过一个常数缩放后，RMSE 明显下降

这说明：

1. 用真实 `MAGE` 驱动去取 `TIEGCM gnsrhs` 是必要的。
2. 当前 `WACCM-X geo_direct_crossmodel NSRHS` 与 `TIEGCM gnsrhs` 至少已经进入“同类量、可继续校准”的区间。
3. 但它们还远没有到“已经对齐”的程度。

## 4. 当前还不能下的结论

这组结果还**不能**说明：

- `WACCM-X NSRHS` 已经等价于 `TIEGCM gnsrhs`
- 也不能说明当前符号、缩放、半球语义都已经正确

原因是：

- 这次只锁定了 `TIEGCM` 首次发送时刻的 `gnsrhs` 快照
- `WACCM-X` 候选包来自另一条 `MAGE-WACCMX` 运行链
- 当前对比仍然是“同类 MAGE 驱动条件下的 first-pass 对比”，还不是严格逐时刻同步对齐

## 5. 当前最合理的技术判断

截至这一步，可以把判断收敛成：

- `WACCM-X geo_projected_rhs_sidecar + solver_to_tiegcm_coupler_crossmodel`
  这条路线是目前最合理的 `NSRHS` 候选表达
- 它与 `TIEGCM gnsrhs` 已经出现**弱正相关**
- 但仍需要进一步做：
  - 逐发送时刻对齐
  - 半球语义确认
  - 常数缩放定标

## 6. 下一步建议

下一步不再做新的 bridge 结构试验，而是做：

1. 在同一类短程 `MAGE-TIEGCM` run 中保留多个发送时刻的 `gnsrhs` 快照
2. 按发送时刻对齐 `WACCM-X` 候选 `NSRHS`
3. 再看：
   - 相关系数是否继续上升
   - `alpha_tiegcm_per_waccm` 是否收敛到稳定量级
   - 南北半球是否表现出一致的符号/尺度关系
