# MAGE-WACCMX to TIEGCM GNSRHS Alignment Hypothesis

日期：2026-03-27

## 结论

截至当前实验阶段，最值得继续推进的 `WACCM-X -> TIEGCM-style gnsrhs`
候选路径是：

- `nsrhs_source = nsrhs_geo_sidecar`
- `nsrhs_transform = solver_to_tiegcm_coupler_crossmodel`

也就是：

**`geo_projected_rhs_sidecar + crossmodel transform`**

## 为什么是这条线

### 1. TIEGCM 对外耦合语义是 `gnsrhs`

`TIEGCM` 里真正接近 coupler 导出语义的量，不是 solver 内部 `nsrhs`
本身，而是：

- `nsrhs = mage_ucurrent(rim1, rim2, ...)`
- `gnsrhs = mag2geo_2d(nsrhs, ...)`

对应代码：

- [mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F)
- [pdynamo.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F)

其中：

- `mage_ucurrent()` 最后做
  - `nsrhs(:,:) = -1.*nsrhs(:,:)/dfac`
- `pdynamo` 再做
  - `call mag2geo_2d(nsrhs, gnsrhs, ...)`

所以 `TIEGCM` 的 coupler-scale 目标量，本质上是：

- 已做符号/`dfac` 缩放
- 已投到 `GEO`

的 `gnsrhs`

### 2. WACCM-X 当前 direct GEO sidecar 已解决投影链问题

现在 `WACCM-X` 侧已经能直接导出：

- `direct mag -> geo 2D` 的 `NSRHS` sidecar

并且它和当前 raw/no-mirror bridge 包在 `feedback_geo` 层上几乎逐点一致，
说明 `GEO` 投影链本身已经不是主要不确定性。

对应说明：

- [MAGE_WACCMX_NSRHS_GEO_PROJECTION_VALIDATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_PROJECTION_VALIDATION_20260327.md)
- [MAGE_WACCMX_NSRHS_GEO_SIDECAR_CANONICALIZATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_SIDECAR_CANONICALIZATION_20260327.md)

所以现在没必要再从 folded-source sidecar 出发绕一遍 bridge 投影。

### 3. crossmodel transform 是当前最接近 TIEGCM `dfac` 语义的显式写法

bridge 当前已支持：

- `solver_to_tiegcm_coupler_crossmodel`

它的写法是：

- `-1 / (WACCM_DFAC_M * TIEGCM_DFAC_M)`

这条写法的意义是：

- 先承认 `WACCM-X` 当前 sidecar 仍带 solver-scale `rhs` 语义
- 再显式朝 `TIEGCM coupler-scale nsrhs/gnsrhs` 的量纲和符号靠拢

对应说明：

- [MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md)

## 当前最强判断

因此，现在最合理的对齐路径不是：

- folded-source sidecar + mirror + transform

而是：

- direct `GEO` sidecar
- 不再做 `mirror`
- 直接应用 `crossmodel transform`
- 然后和 `TIEGCM gnsrhs` 做符号、缩放和 coupler 语义对照

## 当前产物

当前已经生成的最关键候选包：

- [waccmx_cesm_feedback_package_geo_direct_crossmodel.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/waccmx_cesm_feedback_package_geo_direct_crossmodel.h5)

它当前的 metadata 是：

- `nsrhs_source = nsrhs_geo_sidecar`
- `nsrhs_semantics = geo_projected_rhs_sidecar`
- `nsrhs_projection = direct_mag_to_geo_2d_sidecar`
- `nsrhs_transform = solver_to_tiegcm_coupler_crossmodel`

并且这条候选路线的 `step2 Kaiju` 工作点也已完成，说明它不只是
“理论最像”，而是在当前工作点上已经可运行：

- [MAGE_WACCMX_NSRHS_GEO_XMODEL_WORKPOINT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_XMODEL_WORKPOINT_20260327.md)

## 下一步

下一步不再是 bridge 机制开发，而是物理对齐：

1. 以 `geo_direct_crossmodel` 包为工作基线
2. 跑 `step2 Kaiju` 工作点响应
3. 与 `TIEGCM gnsrhs` 的符号、缩放和 hemisphere 语义做最终对照
