# MAGE-WACCMX NSRHS Phase 2 Status

日期：2026-03-27

## 1. 本次阶段结论

`NEUTRAL_DYNAMO_RHS / NSRHS` 这条**显式新变量实验线**已经完成技术贯通。

这里的“技术贯通”指的是：

- `Kaiju` 已新增显式 `NSRHS` 槽位
- `WACCM-X/CESM` 已能导出 `NSRHS` sidecar
- bridge 已能把 `NSRHS` 写入 kaiju-compatible feedback HDF5
- `step2 voltron.x` 已经真实读到 `NSRHS`
- 最终验证里，南北半球 `NSRHS` 都是非零

当前最关键的验收证据在：

- 反馈包：
  [waccmx_cesm_feedback_package_mirror.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/waccmx_cesm_feedback_package_mirror.h5)
- `step2` 合同：
  [waccmx_voltron_contract.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/step2_kaiju_feedback_mirror/waccmx_voltron_contract.txt)

## 2. 最终验证结果

`step2` 合同中：

- Hemisphere 1: `NSRHS absmax = 5.5451E+07 arb`
- Hemisphere 2: `NSRHS absmax = 5.5451E+07 arb`

这说明镜像后的 `NSRHS` 反馈包已经被 `Kaiju` 两个半球同时摄入。

## 3. 这次真正解决了什么

本次工作解决的不是正式 5 变量基线，而是第二阶段实验线里的三个关键问题：

1. `Kaiju` 不再复用旧的 `NEUTRAL_WIND` 槽位，而是走显式 `NSRHS` 槽位。
2. `CESM/WACCM-X` 不再只导出 proxy，而是开始沿 `edynamo RHS` 方向输出 sidecar。
3. bridge 现在明确知道 `NSRHS` 是 folded-solver source，必须在反馈包侧做半球展开。

## 4. 关键技术判断

这轮排查后，已经可以把 `WACCM-X` 侧 `RHS` 的语义边界说清楚：

- `rhspde()` 里的局地 `rhs` 只在北半球求值，南半球默认留零。
- `gather_edyn()` 里的 `rhs_glb` 不是直接全半球物理场，而是 solver 使用的 folded grid 表达。
- 因此，`NSRHS` 不能直接等同于：
  - 局地 `rhs`
  - 也不能直接等同于原样 `rhs_glb`
- 当前实验可运行方案是：
  - 先在 `CESM` 侧导出 folded-source sidecar
  - 再在 bridge 里按磁赤道对称假设把南半球 folded source 镜像到北半球

## 5. 当前代码状态

### Kaiju 实验线

路径：

- [/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_nsrhs_phase2](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_nsrhs_phase2)

关键改动：

- `mixdefs.F90`: 新增 `NSRHS`
- `mixio.F90`: 注册 `NSRHS`
- `mixsolver.F90`: 用 `NSRHS` 而不是 `NEUTRAL_WIND`
- `waccmx_stub_backend.F90`: GEO 输入改接 `NSRHS`

### CESM/WACCM-X

关键改动：

- [edynamo.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90)
- [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90)

当前导出策略：

- 主反馈文件仍保持正式 5 列 conductance 格式
- `NSRHS` 通过独立 sidecar `mage_waccmx_nsrhs_rank*.txt` 导出

### Bridge

关键改动：

- [cesm_feedback_to_kaiju_feedback.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/cesm_feedback_to_kaiju_feedback.py)

当前 bridge 行为：

- `SIGMAP/SIGMAH` 继续按正常 north/south source remap
- `NSRHS` 默认采用 `none`
- `mirror_south_folded_source_to_north` 保留为 legacy/debug unfolding 选项

## 6. 和正式基线的关系

这一阶段**没有改写正式基线口径**。

正式基线仍然是：

- `MAGE -> WACCM-X`: `POT / AVG_ENG / NUM_FLUX`
- `WACCM-X -> MAGE`: `SIGMAP / SIGMAH`

`NSRHS` 当前状态是：

- 已技术跑通
- 已进入 `step2 Kaiju`
- 但仍属于**第二阶段实验增强项**
- 还不应回写成“当前正式完成变量”

## 7. 还没有完成的事

这条线虽然已经技术贯通，但还没有到“物理最终定稿”的程度。

还缺：

- `NSRHS` 单位和缩放的严格物理校准
- 与 `TIEGCM nsrhs/gnsrhs` 的符号、投影、半球折叠对齐
- 决定最终是：
  - 保留 bridge 镜像展开
  - 还是把 GEO/solver 一致的展开直接做在 `WACCM-X` 侧

## 8. 推荐下一步

下一步不应该回头再改 formal baseline，而应该继续：

1. 固化这次 `NSRHS` phase2 快照
2. 保持正式 5 变量闭环不动
3. 单独做 `NSRHS` 的物理量纲/符号校准
4. 再决定是否把这条线推进到主仓库默认能力

## 9. Phase 4 首轮校准进展

截至 `2026-03-27` 夜间，`Phase 4` 已完成 first-pass 语义校准。

新增产物：

- 首轮校准说明：
  [MAGE_WACCMX_NSRHS_PHASE4_FIRSTPASS_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_PHASE4_FIRSTPASS_CN.md)
- 代码级对照说明：
  [MAGE_WACCMX_NSRHS_CODE_ALIGNMENT_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_CODE_ALIGNMENT_CN.md)
- transform 实验记录：
  [MAGE_WACCMX_NSRHS_TRANSFORM_EXPERIMENT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_TRANSFORM_EXPERIMENT_20260327.md)
- 自动分析报告：
  [nsrhs_phase4_analysis.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/nsrhs_phase4_analysis.md)
- 分析脚本：
  [analyze_nsrhs_phase4.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/analyze_nsrhs_phase4.py)

这轮新增结论是：

- `NSRHS` 当前可以确认是 `folded-source` 语义，不是已经可直接使用的完整 GEO 双半球物理场。
- `mirror_south_folded_source_to_north` 在 first-pass 阶段曾作为实验展开规则保留；该判断现已由第 13 节更新。
- `WACCM-X rhs` 当前更接近 `TIEGCM` 的 solver-scale `nsrhs`，而不是已经准备耦合导出的 `gnsrhs`。
- `solver_to_tiegcm_coupler_like` 变换分支已经可执行，但当前会把 `NSRHS absmax` 从 `~5.5e7` 压到 `~1.3e-6`，说明后续若采用这一路径，`Kaiju` 侧注入尺度必须重整定。
- 因此，`NSRHS` 现在仍然是：
  - 已技术跑通
  - 已做首轮语义校准
  - 但还未完成最终物理定稿

## 10. Coupler-Like 注入尺度扫描

截至 `2026-03-27` 深夜，`Phase 4` 已继续推进到 `Kaiju NSRHS` 注入尺度重整定。

新增产物：

- 扫描说明：
  [MAGE_WACCMX_NSRHS_SCALE_SCAN_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_SCALE_SCAN_20260327.md)
- 自动汇总：
  [nsrhs_scale_scan_summary_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs/nsrhs_scale_scan_summary_20260327.md)
- 扫描脚本：
  [run_one_nsrhs_scale_probe.sh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/run_one_nsrhs_scale_probe.sh)
- `Slurm` 数组：
  [run_nsrhs_scale_probe_array.sbatch](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/slurm/run_nsrhs_scale_probe_array.sbatch)

这轮新增结论是：

- `solver_to_tiegcm_coupler_like` 分支并非“完全没有响应”，而是需要把 `Kaiju` 侧 `NSRHS` 注入尺度从旧的 `1e-8` 提升到 `~1e5-1e6` 区间，才会进入可见反馈区。
- `scale ~ 4.18e5` 已经落入一个合理的工作区间：
  - 相比 `scale=0` 有明确 `POT` 响应
  - 又没有像 `1e7` 那样进入明显过强的极端振幅
- 因此，后续这条实验线的默认工作点，不应再用旧的固定 `1e-8`，而应先以 `~4e5` 作为 `coupler-like` 分支的第一工作点继续做物理校准。

## 11. Dfac 常数级对齐补充

截至 `2026-03-27` 深夜，`NSRHS` transform 又补了一个更严格的跨模型常数分支：

- `solver_to_tiegcm_coupler_crossmodel`

对应说明见：

- [MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md)

这轮补充结论是：

- 若严格把 `WACCM-X solver-scale rhs` 映射到 `TIEGCM coupler-scale nsrhs`，更合理的常数写法是 `-1 / (WACCM_DFAC * TIEGCM_DFAC)`。
- 但它与当前 `-1 / WACCM_DFAC^2` 的差异只有约 `0.108%`。
- 因此，现在不需要为这点常数差异重新做整轮尺度扫描。
- 当前主不确定性仍然是：
  - folded-source 语义
  - `mag -> phys columns -> GEO` 投影链路

并且，这一点已经在工作点层面再次确认：

- `coupler-like @ KAIJU_NSRHS_SCALE ~ 4.18e5`
- `coupler-crossmodel @ KAIJU_NSRHS_SCALE ~ 4.18e5`

二者的 `step2 POT` 响应几乎重合，详细对照见：

- [nsrhs_workpoint_compare_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_crossmodel/nsrhs_workpoint_compare_20260327.md)

所以现在可以把结论再收紧一步：

- `dfac` 跨模型常数差异不再视为当前主要工作项
- 下一步校准重点正式收敛到：
  - folded-source 语义
  - `TIEGCM gnsrhs` 的符号/缩放
  - `GEO` 投影等价性

对应的投影链路说明已整理为：

- [MAGE_WACCMX_NSRHS_GEO_PROJECTION_GAP_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_PROJECTION_GAP_CN.md)

## 12. GEO 投影验证更新

截至 `2026-03-27` 夜间，`WACCM-X` 侧已经补上了 direct `mag -> geo 2D` 诊断导出，并完成了和当前 bridge `GEO` 链的 first-pass 对比。

新增产物：

- direct/bridge 对比说明：
  [MAGE_WACCMX_NSRHS_GEO_PROJECTION_VALIDATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_PROJECTION_VALIDATION_20260327.md)
- 自动对比报告：
  [nsrhs_geo_projection_compare_manual.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/nsrhs_geo_projection_compare_manual.md)
- 诊断 run：
  [nsrhs_geo_projection_20260327c](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c)

这轮新增结论是：

- `mage_waccmx_nsrhs_geo_rank*.txt` 已真实生成，说明：
  - `MAGE_WACCMX_WRITE_NSRHS_GEO_SIDECAR` 已成功传入 `cesm.exe`
  - `WACCM-X` 侧 direct `mag -> geo 2D` route 已可运行
- 在同一套 `WACCM-X GEO` 网格点上：
  - 北半球 `corr = 1.000000`
  - 南半球 `corr = 1.000000`

## 13. Unfolding 验证更新

截至 `2026-03-27` 晚间，`raw/no-mirror` 工作点验证也已完成。

新增产物：

- 专门说明：
  [MAGE_WACCMX_NSRHS_UNFOLDING_VALIDATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_UNFOLDING_VALIDATION_20260327.md)
- raw/no-mirror probe：
  [raw_geo_nomirror_4p18e5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_raw/raw_geo_nomirror_4p18e5)

这轮新增结论是：

- `raw/no-mirror` 包已经可被 `step2 Kaiju` 两个半球同时非零摄入
- 与此前 `mirror` 参考相比，`CPCP` 在当前输出精度下没有可见差异
- `mirror` 的主要效果，只是把北半球 `NSRHS` 人工抬高到和南半球完全相同
- 因此，当前 bridge 默认 `NSRHS_UNFOLDING` 已切换为 `none`
- `mirror_south_folded_source_to_north` 现在降级为 legacy/debug unfolding 选项

## 14. GEO Sidecar Canonicalization 更新

截至 `2026-03-27` 晚间，bridge 已经支持把 direct `mag -> geo 2D`
导出的 `NSRHS` sidecar 直接写成 kaiju-compatible feedback HDF5。

新增产物：

- 说明：
  [MAGE_WACCMX_NSRHS_GEO_SIDECAR_CANONICALIZATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_SIDECAR_CANONICALIZATION_20260327.md)
- direct-geo 反馈包：
  [waccmx_cesm_feedback_package_geo_direct.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/waccmx_cesm_feedback_package_geo_direct.h5)

这轮新增结论是：

- bridge 现在同时支持：
  - folded-source sidecar
  - direct `GEO` sidecar
- raw/no-mirror 反馈包中的 `feedback_geo_{north,south}/neutral_rhs`
  与 `geo_direct` 反馈包中的同名数组几乎逐点一致
- 因此，当前 `NSRHS` 的 canonical bridge source 已可以转向
  `geo_projected_rhs_sidecar`
- 后续若继续和 `TIEGCM gnsrhs` 对齐，应优先基于 `GEO sidecar`
  路线，而不是再把 folded-source 作为唯一正式候选
- `geo sidecar` 路线的 `step2 Kaiju` smoke 也已完成，并与 raw/no-mirror
  的 `NSRHS absmax` 完全一致，因此现在可以把它从“候选”提升为当前
  `NSRHS` 实验线的 canonical bridge source

## 15. GEO-Sidecar Crossmodel 候选包

截至 `2026-03-27` 晚间，`direct GEO sidecar` 路线已经可以直接生成
更接近 `TIEGCM gnsrhs` 语义的 `crossmodel` 候选反馈包。

新增产物：

- [waccmx_cesm_feedback_package_geo_direct_crossmodel.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_geo_projection_20260327c/waccmx_cesm_feedback_package_geo_direct_crossmodel.h5)

该包元数据为：

- `nsrhs_source = nsrhs_geo_sidecar`
- `nsrhs_semantics = geo_projected_rhs_sidecar`
- `nsrhs_projection = direct_mag_to_geo_2d_sidecar`
- `nsrhs_transform = solver_to_tiegcm_coupler_crossmodel`

并且其 `NSRHS absmax` 已处于此前 `crossmodel/coupler-like` 路线一致的量级：

- North `~ 1.3130e-06`
- South `~ 1.3268e-06`

这说明：

- 后续若继续做 `TIEGCM gnsrhs` 对齐，已经不必再依赖 folded-source sidecar
- 可以直接在 `geo_projected_rhs_sidecar + crossmodel transform` 路线上推进

并且这条路线的 `step2 Kaiju` 工作点也已完成：

- [MAGE_WACCMX_NSRHS_GEO_XMODEL_WORKPOINT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_XMODEL_WORKPOINT_20260327.md)

对应新增结论：

- `geo_direct_xmodel` 与 folded/crossmodel 参考在 `CPCP` 上一致到当前输出精度
- 但 `geo_direct_xmodel` 保留了约 `1.04%` 的 north/south `NSRHS` 非对称
- 因此它比 folded/crossmodel 更适合作为下一步 `TIEGCM gnsrhs` 对齐的工作基线
  - `rmse ~ 1e-7`
  - `diff_absmax ~ 1e-6`
- 所以当前 `NSRHS` 实验线的主要不确定性，已经不再是 `GEO` 投影链路本身，而是：
  - `folded-source` 语义
  - `unfolding`
  - `solver/coupler` 物理对齐

因此，现在可以把阶段判断再收紧一步：

- `GEO projection` 已从“主要风险项”降级为“已完成 first-pass 验证项”
- 后续工作重心应正式转回：
  - `TIEGCM nsrhs/gnsrhs` 对齐
  - `coupler-scale` 定义
  - `sign / scale / semantics`

## 16. 真实 `MAGE` 驱动 `TIEGCM gnsrhs` 首轮对齐

截至 `2026-03-27` 深夜，已经拿到一轮真实 `MAGE-TIEGCM` coupled smoke 的
`gnsrhs` GEO 诊断快照，并完成了与当前 `WACCM-X` canonical 候选的 first-pass 对比。

新增产物：

- 对齐 run：
  [gtrd_smoke20_gnsrhs_20260327a](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_20260327a)
- 首次发送快照：
  [gnsrhs_snapshot_firstsend](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_20260327a/gnsrhs_snapshot_firstsend)
- 自动对比报告：
  [tiegcm_waccmx_nsrhs_compare_firstsend.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_20260327a/tiegcm_waccmx_nsrhs_compare_firstsend.md)
- 结论记录：
  [MAGE_WACCMX_TIEGCM_GNSRHS_MATCHED_COMPARISON_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_TIEGCM_GNSRHS_MATCHED_COMPARISON_20260327.md)

这轮新增结论是：

- 与前面的 `standalone quiet Heelis` 对比不同，真实 `MAGE` 驱动下，
  `WACCM-X` 候选 `NSRHS` 与 `TIEGCM gnsrhs` 已转成**弱正相关**
- 北半球 `corr ~ 0.103`
- 南半球 `corr ~ 0.154`
- 经过一个常数缩放后，RMSE 明显下降

因此现在可以更明确地说：

- `geo_projected_rhs_sidecar + solver_to_tiegcm_coupler_crossmodel`
  已经进入“可与 `TIEGCM gnsrhs` 做继续校准”的区间
- 但它仍然没有到“已完成物理对齐”的程度

当前下一步已进一步收敛为：

1. 在真实 `MAGE-TIEGCM` 短程 run 中保留多个发送时刻的 `gnsrhs` 快照
2. 做逐发送时刻的 cross-model 对齐
3. 再决定最终符号、缩放和 hemisphere 语义

## 17. `TIEGCM gnsrhs` 多帧时序抓取已完成

截至 `2026-03-27` 深夜，`TIEGCM` 诊断导出已经从单帧升级为按 `istep` 留档。

新增产物：

- 说明：
  [MAGE_WACCMX_TIEGCM_GNSRHS_TIMESERIES_CAPTURE_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_TIEGCM_GNSRHS_TIMESERIES_CAPTURE_20260327.md)
- 多帧 run：
  [gtrd_smoke20_gnsrhs_steps_20260327b](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/tiegcm_gnsrhs_alignment/runs/gtrd_smoke20_gnsrhs_steps_20260327b)

这轮新增结论是：

- `MAGE_TIEGCM_GNSRHS_DIAG_MODE=step` 已经工作
- 当前短程 coupled smoke 中已经抓到至少 4 个发送时刻：
  - `step00000001`
  - `step00000002`
  - `step00000003`
  - `step00000004`

因此，下一步已不再是“如何让 `TIEGCM` 留住多个 `gnsrhs` 快照”，而是：

1. 给 `WACCM-X` 侧也建立同类时序快照保留
2. 做逐发送时刻 cross-model 对齐
3. 再收敛最终符号、缩放和 hemisphere 语义
