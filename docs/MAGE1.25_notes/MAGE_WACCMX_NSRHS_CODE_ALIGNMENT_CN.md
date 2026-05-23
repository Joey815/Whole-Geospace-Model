# MAGE-WACCMX `NSRHS` 代码级对照说明

日期：2026-03-27

## 1. 当前最重要的判断

基于当前代码排查，最稳妥的结论是：

- `WACCM-X rhspde()` 里的 `rhs`，在**物理类型**上更接近 `TIEGCM` 求解器内部使用的 `nsrhs`
- 但它**还不能直接等同于** `TIEGCM mage_ucurrent` 最后准备耦合输出的 `nsrhs/gnsrhs`

也就是说，当前更像是：

- `WACCM-X rhs` 对齐 `TIEGCM current.F` / 内部 solver-scale RHS

而不是：

- `WACCM-X rhs` 已经直接对齐 `TIEGCM -> MAGE` 的 coupler-scale GEO 输出

## 2. `TIEGCM` 里的两种 `nsrhs`

### 2.1 求解器内部 `nsrhs`

在 [current.F90](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/current.F90) 里：

- 先对 `rim_glb(:,:,1)` 做经向导数
- 再对 `rim_glb(:,:,2)` 做纬向导数
- 南北半球在 `theta0` 项上分别是 `-` 和 `+`
- 赤道使用双侧平均 stencil
- 最后做：
  - `nsrhs(:,:) = nsrhs(:,:)*dfac`
  - `dfac = r0*1.0e-2`

关键代码：

- [current.F90:169](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/current.F90#L169)
- [current.F90:187](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/current.F90#L187)
- [current.F90:214](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/current.F90#L214)
- [current.F90:246](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/current.F90#L246)

### 2.2 准备耦合导出的 `nsrhs`

在 [mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F) 的 `mage_ucurrent` 里：

- 也是由 `rim1/rim2` 形成 RHS
- 同样南北半球 `theta0` 项分别是 `-` 和 `+`
- 同样会单独处理赤道
- 但最后做的是：
  - `nsrhs(:,:) = -1.*nsrhs(:,:)/dfac`
  - `dfac = r0*1.0e-2`

关键代码：

- [mage_coupling.F:1039](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F#L1039)
- [mage_coupling.F:1086](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F#L1086)
- [mage_coupling.F:1091](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F#L1091)
- [mage_coupling.F:1106](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F#L1106)

然后在 [pdynamo.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F) 里：

- `call mage_ucurrent(..., nsrhs)`
- 再 `call mag2geo_2d(nsrhs, gnsrhs, ..., 'NSRHS   ')`

关键代码：

- [pdynamo.F:1586](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F#L1586)
- [pdynamo.F:1602](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F#L1602)

## 3. `WACCM-X` 里的 `rhs`

在 [edynamo.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90) 里：

- `rhspde()` 明确只在北半球和赤道形成 `rhs`
- 注释写着 `allow south hemisphere to remain 0`
- 最后做：
  - `rhs(i,j) = rhs(i,j)*r0*1.e-2_r8`

关键代码：

- [edynamo.F90:1052](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90#L1052)
- [edynamo.F90:1069](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90#L1069)
- [edynamo.F90:1105](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90#L1105)
- [edynamo.F90:1127](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90#L1127)

然后在 `gather_edyn()` 里：

- 局地 `rhs` 被 gather 到 `rhs_nhem`
- 再被塞进 folded `rhs_glb`

关键代码：

- [edynamo.F90:1178](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90#L1178)
- [edynamo.F90:1183](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90#L1183)

## 4. 当前最关键的缩放差异

把代码最关键的缩放拿出来看：

- `TIEGCM current.F` 内部 RHS：`* dfac`
- `TIEGCM mage_ucurrent` 导出 RHS：`- / dfac`
- `WACCM-X rhspde` 当前 RHS：`* dfac`

因此，仅从代码形式上看：

- `WACCM-X rhs` 更像 `TIEGCM current.F` 里的内部 solver-scale `nsrhs`
- 不像 `mage_ucurrent` 最后要耦出去的 coupler-scale `nsrhs`

这意味着后续如果要拿 `WACCM-X rhs` 去对齐 `TIEGCM -> MAGE` 的 `gnsrhs`，**很可能需要单独的 coupler transform**，而不是直接拿当前 sidecar 数值去比。

更严格地说，如果把 `WACCM-X solver-scale rhs` 对齐到 `TIEGCM coupler-scale nsrhs`，跨模型写法应当区分两套 `dfac`：

- `WACCM-X solver-scale -> TIEGCM coupler-scale`
  - `-1 / (WACCM_DFAC * TIEGCM_DFAC)`

而不是简单近似为：

- `-1 / WACCM_DFAC^2`

但这两者在当前常数下只差约 `0.108%`，见
[MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md)。

所以当前主不确定性并不是 `dfac` 常数本身，而是：

- folded-source 语义
- `mag -> phys columns -> GEO` 的投影链路

## 5. 当前投影路径也不一样

`TIEGCM` 当前是：

- `mag grid nsrhs`
- `mag2geo_2d`
- `gnsrhs`

`WACCM-X` 当前实验线是：

- `rhs_bothhem` on magnetic grid
- [regrid_mag2phys_2d](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/regridder.F90#L30)
- physics columns sidecar
- bridge 里再根据 column `lat/lon` 常规 remap 成 GEO feedback HDF5

关键代码：

- [regridder.F90:30](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/regridder.F90#L30)
- [mage_waccmx_feedback_stub.F90:130](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90#L130)
- [cesm_feedback_to_kaiju_feedback.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/cesm_feedback_to_kaiju_feedback.py)

所以当前 `WACCM-X` 实验线的投影路径不是：

- `mag -> geo`

而是：

- `mag -> phys columns -> bridge regular GEO remap`

这也是为什么当前 `NSRHS` 仍然不能直接宣称已经对齐 `TIEGCM gnsrhs`。

## 6. 当前可操作的实验判断

现在最合理的判断是：

1. `WACCM-X rhs` 是一个合理的 `NSRHS` 候选源项。
2. 当前 sidecar 语义仍应写成：
   - `folded_solver_rhs_sidecar`
3. 当前 mirror 展开仍只是 bridge 的实验展开规则。
4. 后续真正的校准重点应是：
   - 符号
   - 缩放
   - `mag -> geo` 投影
   - folded / equator 处理

## 7. 当前新增的可复现实验开关

为了把 raw 和 mirror 校准过程标准化，当前 bridge 脚本已经支持：

- `--nsrhs-unfolding none`
- `--nsrhs-unfolding mirror_south_folded_source_to_north`

对应脚本：

- [cesm_feedback_to_kaiju_feedback.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/cesm_feedback_to_kaiju_feedback.py)
- [run_bidirectional_cycle.sh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/run_bidirectional_cycle.sh)

并且已用现成 `nsrhs_cycle_20260327d` 数据重新生成：

- raw reproducible 包：
  [waccmx_cesm_feedback_package_raw_repro.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/waccmx_cesm_feedback_package_raw_repro.h5)
- mirror reproducible 包：
  [waccmx_cesm_feedback_package_mirror_repro.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/waccmx_cesm_feedback_package_mirror_repro.h5)

这两份包的 `meta` 现在会明确写：

- `nsrhs_semantics`
- `nsrhs_projection`
- `nsrhs_unfolding`

## 8. 下一步建议

下一步不该再改 bridge 结构，而应直接做：

1. 给 `WACCM-X sidecar` 增加一个 coupler-scale 试验分支
2. 比较它和 `TIEGCM mage_ucurrent -> gnsrhs` 的量级与符号
3. 判断最终的 unfold / projection 应该落在：
   - `WACCM-X` 导出侧
   - 还是 bridge 侧

## 9. 一句话判断

当前代码排查支持这样的工作假设：

**`WACCM-X rhs` 当前更接近 `TIEGCM` 的 solver-scale `nsrhs`，而不是已经准备正式耦合输出的 `gnsrhs`；因此后续需要做显式的 coupler transform，而不是直接把当前 sidecar 当最终物理量。**
