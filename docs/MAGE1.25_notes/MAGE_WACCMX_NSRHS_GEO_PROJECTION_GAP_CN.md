# MAGE-WACCMX `NSRHS` GEO 投影链路差异说明

日期：2026-03-27

## 1. 当前更新后的结论

这份文档最初记录的是一个待验证假设：  
**当前 `NSRHS` 实验线的主问题可能在 `GEO` 投影链路本身。**

截至 `2026-03-27` 晚间，这个假设已经被新实验基本排除，见：

- [MAGE_WACCMX_NSRHS_GEO_PROJECTION_VALIDATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_PROJECTION_VALIDATION_20260327.md)

最新结论应改写为：

- `TIEGCM` 仍然是：`mag grid nsrhs -> mag2geo_2d -> gnsrhs`
- `WACCM-X` 当前实验线仍然是：`rhs_bothhem -> regrid_mag2phys_2d -> physics columns -> bridge regular remap -> GEO feedback`
- 但在同一套 `WACCM-X GEO` 网格点上，**这两条 `WACCM-X` 内部投影路径已经几乎逐点一致**

所以现在更准确的判断是：

**`GEO` 投影链路已经不是当前主矛盾，主矛盾重新收敛为 `folded-source` 语义和 `solver/coupler` 物理对齐。**

## 2. `TIEGCM` 当前路径

`TIEGCM` 侧在 [pdynamo.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F#L1586) 中：

- 先 `call mage_ucurrent(..., nsrhs)`
- 再 `call mag2geo_2d(nsrhs, gnsrhs, ..., 'NSRHS   ')`

而 [mag2geo_2d](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F#L2778) 本身是：

- `esmf_set2d_mag(...)`
- `esmf_regrid(...,'mag2geo',2)`
- `esmf_get_2dfield(...)`

也就是：**直接把磁网格 2D 场重网格到 GEO 2D 场。**

## 3. `WACCM-X` 当前实验路径

`WACCM-X` 侧当前实验导出在 [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90#L122)：

- 使用 `rhs_bothhem`
- 调 [regrid_mag2phys_2d](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/regridder.F90#L30)
- 得到 `edyn_rhs_flat`
- 再写成 `mage_waccmx_nsrhs_rank*.txt`

然后 bridge 在 [cesm_feedback_to_kaiju_feedback.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/cesm_feedback_to_kaiju_feedback.py#L75) 到 [cesm_feedback_to_kaiju_feedback.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/cesm_feedback_to_kaiju_feedback.py#L210) 做：

- `build_source_grid(...)`
- `hemi_latlon(...)`
- `remap_regular(...)`

也就是：**先落到 physics columns，再由 Python 做规则经纬 nearest-neighbor remap。**

## 4. 当前真正剩下的差异是什么

结构差异仍然存在，但“存在不同路径”不再等于“数值上就是主误差源”。

现在仍然存在的结构差异有：

1. 中间表示不一样

- `TIEGCM`: 直接 `mag -> geo`
- `WACCM-X`: `mag -> phys columns -> geo`

2. 重网格器不一样

- `TIEGCM`: `ESMF mag2geo`
- `WACCM-X` 当前 bridge: Python 规则经纬最近邻 `remap_regular`

3. 源场语义不一样

- `TIEGCM`: `nsrhs` 在进入 `mag2geo_2d` 之前已经是 coupler-side 磁网格 RHS
- `WACCM-X`: 当前 sidecar 还是 folded-source / experimental unfolded 语义

## 5. 为什么现在不再把它当第一风险项

`dfac` 这层现在已经有定量结论，见
[MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md)：

- `solver_to_tiegcm_coupler_like`
- `solver_to_tiegcm_coupler_crossmodel`

两者只差约 `0.108%`，而且在 `step2` 工作点验证里几乎重合。

而 `GEO` 投影链这一步，在新验证中已经给出：

- 北半球 `corr = 1.000000`
- 南半球 `corr = 1.000000`
- `rmse ~ 1e-7`
- `diff_absmax ~ 1e-6`

也就是说，**就当前 `WACCM-X` 自己这条实验线而言，`mag -> phys -> GEO` 已经能重现 direct `mag -> geo` 的 `GEO` 数值场。**

## 6. 现在的下一步应该改成什么

这条 direct `mag -> geo` 的 `WACCM-X` 2D 导出通道现在已经补上，并完成了 first-pass 对比。

所以下一步不应再继续围绕“投影链路差多少”做工作，而应转向：

1. `folded-source` 语义
2. `unfolding` 是否应该留在 bridge，还是前移到 `WACCM-X` 侧
3. `solver-scale rhs` 到 `coupler-scale gnsrhs` 的符号和缩放
4. 与 `TIEGCM nsrhs/gnsrhs` 的最终物理对齐

## 7. 推荐实验顺序

推荐顺序现在应改成：

1. 固定 `KAIJU_NSRHS_SCALE ~ 4e5`
2. 保持 `coupler-crossmodel` 作为更严格的常数级分支
3. 保留当前 direct `mag -> geo 2D` 诊断导出作为回归对照
4. 继续讨论：
   - `folded-source`
   - `solver_to_tiegcm_coupler_*`
   - `TIEGCM gnsrhs`
5. 再做最终物理定稿

## 8. 一句话判断

现在 `NSRHS` 这条线的主问题已经从“尺度调多少”进一步收敛成：

**怎样让 `WACCM-X` 产生一个在物理语义上真正可与 `TIEGCM gnsrhs` 对照的 coupler-scale `NSRHS`。**
