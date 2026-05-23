# MAGE-WACCMX NSRHS GEO Sidecar Canonicalization

日期：2026-03-27

## 结论

当前 `NSRHS` 实验线的 canonical bridge source，已经可以从
`folded-source sidecar` 转向 `direct GEO sidecar`。

原因不是概念判断，而是已经有数组级证据：

- raw/no-mirror 反馈包中的 `feedback_geo_{north,south}/neutral_rhs`
- direct `mag -> geo 2D` sidecar 生成的 `geo_direct` 反馈包中的同名数组

二者在同一套 `Kaiju GEO` 反馈网格上几乎逐点一致。

## 关键证据

### 1. direct GEO feedback package

- 反馈包：
  [waccmx_cesm_feedback_package_geo_direct.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/waccmx_cesm_feedback_package_geo_direct.h5)

该包元数据为：

- `nsrhs_source = nsrhs_geo_sidecar`
- `nsrhs_semantics = geo_projected_rhs_sidecar`
- `nsrhs_projection = direct_mag_to_geo_2d_sidecar`

### 2. raw vs geo-direct 数组对比

对比对象：

- raw 包：
  [waccmx_cesm_feedback_package.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/waccmx_cesm_feedback_package.h5)
- geo-direct 包：
  [waccmx_cesm_feedback_package_geo_direct.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/waccmx_cesm_feedback_package_geo_direct.h5)

结果：

- North:
  - `absmax_raw = 5.4874416196572095e+07`
  - `absmax_geo = 5.4874416196573004e+07`
  - `diff_absmax = 1.8775463e-06`
  - `rmse = 2.7548591e-07`
  - `corr = 1.0`
- South:
  - `absmax_raw = 5.545069933882411e+07`
  - `absmax_geo = 5.545069933882278e+07`
  - `diff_absmax = 1.3411045e-06`
  - `rmse = 1.2438570e-07`
  - `corr = 1.0`

这已经足够说明：

- 当前 bridge 的 raw/no-mirror GEO 结果
- 和 direct `mag -> geo 2D` GEO sidecar 结果

在反馈 HDF5 层面等价到数值舍入误差。

## 含义

这一步的意义不是“再证明一次 GEO 投影正确”，而是：

1. `NSRHS` 的 canonical 交换形态现在可以提升为 `geo_projected_rhs_sidecar`
2. 后续若继续做 `TIEGCM gnsrhs` 对齐，应优先基于这个 `GEO sidecar`
3. `folded-source sidecar` 仍可保留，但更适合当 solver-diagnostic / legacy source

## Step2 验收

`GEO sidecar` 路线已经补做了 `step2 Kaiju` smoke 验收。

- 作业：`4728272`
- 结果目录：
  [geo_direct_4p18e5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_geo/geo_direct_4p18e5)
- 汇总：
  [nsrhs_scale_probe_summary.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_geo/geo_direct_4p18e5/nsrhs_scale_probe_summary.txt)

结果：

- H1 `NSRHS absmax = 5.4874E+07 arb`
- H2 `NSRHS absmax = 5.5451E+07 arb`

这与 raw/no-mirror probe 的 `step2` 合同一致，说明：

- `geo sidecar` 不只是数组级等价
- 它在 `Kaiju step2` 响应层面也已与当前 raw/no-mirror 路线对齐

因此，现在可以把 `geo_projected_rhs_sidecar` 写成当前 `NSRHS`
实验线的 canonical bridge source。

## 代码状态

bridge 现在已经同时支持两类 `NSRHS` 源：

- `--neutral-rhs-glob`
- `--neutral-rhs-geo-glob`

对应脚本：

- [cesm_feedback_to_kaiju_feedback.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/cesm_feedback_to_kaiju_feedback.py)

总循环脚本也已经支持源模式切换：

- [run_bidirectional_cycle.sh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/run_bidirectional_cycle.sh)
- `NSRHS_SOURCE_MODE=sidecar`
- `NSRHS_SOURCE_MODE=geo_sidecar`

## 下一步

下一步不再围绕 raw vs geo-direct 做额外机制验证，而是直接转入：

- `geo_projected_rhs_sidecar`
- 与 `TIEGCM gnsrhs`

的符号、缩放和 coupler 语义对齐。
