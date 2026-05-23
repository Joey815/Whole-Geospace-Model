# MAGE-WACCMX NSRHS GEO Crossmodel Workpoint

日期：2026-03-27

## 结论

`geo_projected_rhs_sidecar + solver_to_tiegcm_coupler_crossmodel`
这条候选路线已经完成 `step2 Kaiju` 工作点验证。

结果表明：

- 它与此前 folded/crossmodel 参考在 `CPCP` 上一致到当前输出精度
- 但它保留了 north/south 的约 `1%` 非对称
- 因而它比 folded/crossmodel 更适合继续作为
  `TIEGCM gnsrhs` 对齐的工作基线

## 关键证据

### 1. 新工作点

- 作业：`4728329`
- 结果目录：
  [geo_direct_xmodel_4p18e5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_geo_crossmodel/geo_direct_xmodel_4p18e5)
- 汇总：
  [nsrhs_scale_probe_summary.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_geo_crossmodel/geo_direct_xmodel_4p18e5/nsrhs_scale_probe_summary.txt)

合同结果：

- H1 `NSRHS absmax = 1.3130E-06`
- H2 `NSRHS absmax = 1.3268E-06`

### 2. 旧参考

- 参考目录：
  [scale_4p18e5_xmodel_A4728147_T0](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_crossmodel/scale_4p18e5_xmodel_A4728147_T0)
- 汇总：
  [nsrhs_scale_probe_summary.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_crossmodel/scale_4p18e5_xmodel_A4728147_T0/nsrhs_scale_probe_summary.txt)

旧参考结果：

- H1 `NSRHS absmax = 1.3268E-06`
- H2 `NSRHS absmax = 1.3268E-06`

### 3. CPCP 对照

新工作点：

- [launcher.log](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_geo_crossmodel/geo_direct_xmodel_4p18e5/step2_kaiju_feedback/launcher.log)
- `CPCP = 14.882 18.189 [kV, N/S]`

旧参考：

- [launcher.log](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_crossmodel/scale_4p18e5_xmodel_A4728147_T0/step2_kaiju_feedback/launcher.log)
- `CPCP = 14.882 18.189 [kV, N/S]`

## 对比解释

这说明：

- folded/crossmodel 参考把两半球压成了完全相同的 `NSRHS`
- `geo_direct_xmodel` 则保留了原本 north/south 的约 `1.04%` 差异
- 但这点差异在当前工作点下尚未把 `CPCP` 推出可见差别

因此现在可以把判断再收紧一步：

- 如果目标是更接近真实 `gnsrhs` 语义
- 同时又不牺牲当前工作点响应

那么 `geo_direct_xmodel` 比 folded/crossmodel 更适合作为下一步对齐基线
