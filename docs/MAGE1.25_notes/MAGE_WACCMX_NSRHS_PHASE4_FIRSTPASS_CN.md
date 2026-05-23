# MAGE-WACCMX `NSRHS` Phase 4 首轮物理校准说明

日期：2026-03-27

## 1. 这一步解决了什么

这一步不是继续扩桥接功能，而是把当前 `NSRHS` 实验线的**代码语义**和**运行产物语义**对齐。

目标问题只有两个：

1. `TIEGCM nsrhs/gnsrhs` 和 `WACCM-X rhs/rhs_glb/rhs_bothhem` 分别代表什么。
2. 当前 bridge 里的 `mirror_south_folded_source_to_north` 到底是在修一个临时技术问题，还是已经得到了物理定稿的全半球量。

## 2. `MAGE-TIEGCM` 里是怎么处理的

`TIEGCM` 内部确实明确计算了 neutral-dynamo RHS：

- [mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F) 里的 `mage_ucurrent`
- [pdynamo.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F) 里的 `call mage_ucurrent(..., nsrhs)`
- 随后又 `call mag2geo_2d(nsrhs, gnsrhs, ..., 'NSRHS   ')`

语义上：

- `nsrhs` 是磁网格上的 neutral-dynamo PDE RHS / current-continuity source term
- `gnsrhs` 是把 `nsrhs` 投影到 GEO 后的版本

但当前正式 `MAGE-TIEGCM` 主线并没有把它真正耦出去：

- [mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F) 里 `nmixoutgeo = 0`

所以 `TIEGCM` 当前状态是：

- **内部已算 `nsrhs -> gnsrhs`**
- **正式耦合未导出 GEO 量**

## 3. `WACCM-X` 里当前 `rhs` 链路的语义

当前 `WACCM-X` 侧有三层量要分开：

1. `rhs`
2. `rhs_glb`
3. `rhs_bothhem`

### 3.1 `rhs`

[edynamo.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90) 的 `rhspde()` 里：

- 赤道和北半球会计算 RHS
- 注释明确写着 `allow south hemisphere to remain 0`

所以局地 `rhs` 不是“南北半球完整物理场”。

### 3.2 `rhs_glb`

同文件 `gather_edyn()` 会把 `rhs_nhem` 转成 `rhs_glb`。

代码注释和赋值方式说明：

- `rhs_glb` 不是直接意义上的 full-hemisphere GEO 场
- 它是 solver 使用的 folded-grid 表达
- 其纬向组织方式是“south pole -> equator”的折叠表示

### 3.3 `rhs_bothhem`

当前实验代码又新增了 `rhs_bothhem`，做法是：

- 先把 `rhs_glb` 人工展开成 `rhs_unfold_glb`
- 再 `mp_scatter_phim(rhs_unfold_glb, rhs_bothhem)`

这一步目前只是**工程实验展开**，不是已经物理定稿的正统全半球定义。

## 4. 当前运行产物告诉了我们什么

基于本次完整实验 run：

- 运行目录：
  [nsrhs_cycle_20260327d](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d)
- 自动分析报告：
  [nsrhs_phase4_analysis.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/nsrhs_phase4_analysis.md)
- 代码级对照说明：
  [MAGE_WACCMX_NSRHS_CODE_ALIGNMENT_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_CODE_ALIGNMENT_CN.md)

关键数值是：

- sidecar 原始源：
  - north `nnz = 452`
  - south `nnz = 6782`
  - south/north `nnz` 比约 `15.0`
- raw feedback HDF5：
  - north `nnz = 0`
  - south `nnz = 16200`
- mirror 后 feedback HDF5：
  - north `nnz = 16200`
  - south `nnz = 16200`
  - 两半球 `absmax` 和 `mean` 一致
- `step2` 合同：
  - raw: H1 `NSRHS = 0`, H2 `NSRHS = 5.5451E+07`
  - mirror: H1/H2 都是 `5.5451E+07`

这说明：

- 当前 sidecar 不是一个可直接当作 full-hemisphere GEO 场使用的量
- bridge 里的 `mirror_south_folded_source_to_north` 确实在“修复输入形态”
- 但这仍然只是**临时展开规则**

## 5. 当前最稳妥的技术结论

现在可以明确下结论：

1. `WACCM-X rhs` 在物理类型上更接近 `TIEGCM nsrhs`，而不是当前 proxy 风场。
2. 但当前 `WACCM-X` 导出的 `NSRHS sidecar` 还不能直接等同于“完整 GEO neutral-dynamo forcing”。
3. bridge 里的 mirror 展开应当继续保留为**实验临时手段**。
4. 现在还不应该把这条 `NSRHS` 实验线升级成“正式完成的 neutral-dynamo 耦合”。

## 6. 现在不该做什么

当前不建议：

- 把 `NSRHS` 改回正式基线变量
- 把 mirror 展开直接宣称为最终物理闭合
- 在没有完成符号/缩放/GEO 投影校准前，把 `rhs_bothhem` 并回正式生产路径

## 7. 下一步应该做什么

下一步应继续做真正的物理校准，而不是继续扩桥接：

1. 对齐 `TIEGCM nsrhs` 的符号和缩放
2. 对齐 `TIEGCM gnsrhs` 的 GEO 投影含义
3. 判断 mirror 展开最终应该：
   - 留在 bridge
   - 还是前移到 `WACCM-X` 导出侧
4. 在完成前 3 项之前，`NSRHS` 继续保留为第二阶段实验增强项

## 8. 一句话判断

`NSRHS` 这条线现在已经完成了**技术贯通 + 首轮语义校准**，但当前得到的是：

- **folded-source + 临时 mirror 展开**

而不是：

- **已经物理定稿的 full-hemisphere neutral-dynamo GEO 回传**

补充一点：

- 当前 bridge 已支持显式 `--nsrhs-unfolding`
- 已可重复生成 `raw` 和 `mirror` 两种反馈包
- 因此后续 `Phase 4` 校准现在已经具备可复现实验基线
