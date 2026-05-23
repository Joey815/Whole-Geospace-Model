# MAGE-WACCMX `NSRHS` GEO 投影验证

日期：2026-03-27

## 1. 目标

验证当前 `WACCM-X` 实验线里的两条 `NSRHS -> GEO` 路径是否存在实质性差异：

1. 直接路径：`mag -> geo 2D`
2. 当前 bridge 路径：`mag -> phys columns -> regular GEO remap`

这一步只比较**投影链路本身**，不讨论：

- `folded-source` 语义
- half-hemisphere unfolding
- `TIEGCM gnsrhs` 物理对齐

## 2. 本次实现

本次补了两部分最小实现：

1. `WACCM-X` 侧 direct `mag -> geo 2D` 诊断导出

- [edyn_esmf.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edyn_esmf.F90)
- [regridder.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/regridder.F90)
- [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90)

新增诊断 sidecar：

- `mage_waccmx_nsrhs_geo_rank*.txt`

2. bridge 侧自动对比脚本

- [compare_nsrhs_geo_projection.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/compare_nsrhs_geo_projection.py)

## 3. 运行与产物

聚焦运行目录：

- [nsrhs_geo_projection_20260327c](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c)

关键输入产物：

- [with_import_feedback](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/with_import_feedback)
- [mage_waccmx_nsrhs_rank000000.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/with_import_feedback/mage_waccmx_nsrhs_rank000000.txt)
- [mage_waccmx_nsrhs_geo_rank000000.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/with_import_feedback/mage_waccmx_nsrhs_geo_rank000000.txt)
- [mage_waccmx_feedback_rank000000_summary.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/with_import_feedback/mage_waccmx_feedback_rank000000_summary.txt)

自动对比报告：

- [nsrhs_geo_projection_compare_manual.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/nsrhs_geo_projection_compare_manual.md)

说明：

- 这次作业在拿到 direct-geo 和 bridge-geo 对比所需产物后主动停止，没有继续要求完整 `step2`。
- 所以这一步是**投影链路验证**，不是新的闭环验收。

## 4. 结果

对比报告给出的结论非常干净。

北半球：

- direct `geo`:
  - `absmax = 5.487442e+07`
  - `mean = 3.405984e+04`
- bridge `geo`:
  - `absmax = 5.487442e+07`
  - `mean = 3.405984e+04`
- 差值：
  - `diff_absmax = 1.877546e-06`
  - `rmse = 2.130132e-07`
  - `corr = 1.000000`

南半球：

- direct `geo`:
  - `absmax = 5.545070e+07`
  - `mean = 3.293534e+05`
- bridge `geo`:
  - `absmax = 5.545070e+07`
  - `mean = 3.293534e+05`
- 差值：
  - `diff_absmax = 1.341105e-06`
  - `rmse = 1.222937e-07`
  - `corr = 1.000000`

## 5. 结论

这一步可以明确排除一个先前假设：

**当前 `WACCM-X` 实验线里的主要误差，不在 `mag -> phys columns -> regular GEO remap` 这条 `GEO` 投影链本身。**

更准确地说：

- 在同一套 `WACCM-X GEO` 网格点上，
- direct `mag -> geo 2D`
- 和当前 bridge 的 `mag -> phys -> regular GEO remap`
- 数值上已经几乎逐点重合。

因此，这一步之后最合理的判断是：

- `GEO projection` 已经不是当前主矛盾
- 当前主矛盾重新收敛到：
  - `folded-source` 语义
  - `unfolding` 规则
  - `solver/coupler` 量纲与符号
  - 与 `TIEGCM nsrhs/gnsrhs` 的物理对齐

## 6. 对路线图的影响

这一步之后，`NSRHS` 第二阶段的优先级应改成：

1. 不再把 `GEO projection` 当第一风险项
2. 继续保留 direct `mag -> geo 2D` 诊断导出能力
3. 把后续工作重点放回：
   - `folded-source -> coupler-scale` 语义
   - `sign / scale`
   - `TIEGCM gnsrhs` 对齐

一句话总结：

**`NSRHS` 当前剩下的问题，主要不是“怎么投到 GEO”，而是“投过去的这个量到底应该是什么语义”。**
