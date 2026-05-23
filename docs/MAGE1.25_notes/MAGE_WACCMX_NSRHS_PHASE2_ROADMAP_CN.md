# MAGE-WACCMX `NEUTRAL_DYNAMO_RHS / NSRHS` 第二阶段路线图

日期：2026-03-27

## 0. 当前进度更新

截至 `2026-03-27` 晚间，这条路线已经完成到：

- `Kaiju` 显式 `NSRHS` 槽位已打通
- `CESM/WACCM-X` `NSRHS` sidecar 已导出
- bridge 已支持 `NSRHS` sidecar -> feedback HDF5
- 最终 `step2` 验证中，南北半球 `NSRHS` 都已非零摄入

对应状态记录见：

- [MAGE_WACCMX_NSRHS_PHASE2_STATUS_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_PHASE2_STATUS_20260327.md)

当前路线图已经从“纯规划”进入“实验线已跑通，下一步转物理校准”阶段。

## 1. 阶段目标

在**不破坏当前正式 5 变量基线**的前提下，沿 `NEUTRAL_DYNAMO_RHS / NSRHS` 这条线推进 `neutral-dynamo` 耦合。

当前正式基线：

- `MAGE -> WACCM-X`: `POT / AVG_ENG / NUM_FLUX`
- `WACCM-X -> MAGE`: `SIGMAP / SIGMAH`

当前实验增强项：

- `neutral_rhs`

第二阶段的目标不是继续扩展当前 proxy，而是：

- 新增一个显式 `Kaiju` 变量：`NEUTRAL_DYNAMO_RHS` 或 `NSRHS`
- 让 `WACCM-X` 侧输出更接近 `TIEGCM nsrhs/gnsrhs` 的真实 dynamo RHS
- 将其与正式 5 变量基线解耦管理

## 2. 总体原则

1. 不改写当前正式基线结论。
2. `neutral-dynamo` 开发默认走**实验开关**，不默认启用。
3. 不再把最终目标量塞进当前 `NEUTRAL_WIND(cm/s)` 槽位。
4. 所有新工作先在独立实验线完成，再决定是否并回主仓库。

## 3. 推荐技术路线

### 路线 A：显式新变量，推荐

核心思路：

- `WACCM-X` 导出 `edynamo rhs`
- `Kaiju` 新增 `NEUTRAL_DYNAMO_RHS / NSRHS`
- `mixsolver` 将其作为独立 RHS/source term 注入，而不是通过 `NEUTRAL_WIND`

这是当前最推荐的正式方向。

### 路线 B：过渡兼容层

核心思路：

- `WACCM-X` 先导出真实 `rhs`
- 桥接仍暂时沿用现有文件通道
- `Kaiju` 先用兼容适配层接收，再过渡到新变量

只适合短期开发，不建议长期停留。

### 路线 C：继续沿用当前 proxy

不推荐作为最终方案。  
最多只保留为对照组或 fallback。

## 4. 实施分层

### Phase 0：基线冻结

当前已完成：

- 正式基线快照已保存在
  [20260327_waccmx_formal_baseline](/home/jiaoy_group/jiaoy/data/MAGE1.25/snapshots/20260327_waccmx_formal_baseline)

### Phase 1：Kaiju 接口扩展

当前状态：已完成实验线实现

目标：

- 新增显式变量 `NEUTRAL_DYNAMO_RHS` 或 `NSRHS`

建议文件：

- [mixdefs.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/base/defs/mixdefs.F90)
- [mixio.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/mixio.F90)
- [volttypes.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/base/types/volttypes.F90)
- [waccmx_stub_backend.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/waccmx_stub_backend.F90)
- [mixsolver.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/mixsolver.F90)

主要任务：

- 新变量枚举、名称、I/O 注册
- GEO 输入列表从 `NEUTRAL_WIND` 改为新变量
- `mixsolver` 单独接 RHS 项
- 默认关闭，不影响当前正式闭环

### Phase 2：WACCM-X 导出路径重构

当前状态：已完成第一版 `edynamo RHS` sidecar 导出

目标：

- 从 proxy 切换到更真实的 `edynamo rhs`

建议文件：

- [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90)
- [edynamo.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90)
- [atm_import_export.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/cpl/nuopc/atm_import_export.F90)
- [physpkg.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/physics/cam/physpkg.F90)

主要任务：

- 保留 proxy 和 `edyn_rhs` 双模式
- 明确实验输出模式
- 让新变量导出与正式 5 变量路径解耦

### Phase 3：桥接协议整理

当前状态：已完成 first-pass sidecar bridge；当前实验实现使用 folded-source mirror 展开

目标：

- 让 `NSRHS` 的实验协议不污染正式 5 变量口径

推荐做法：

- 正式 5 变量文件继续保持原有含义
- `NSRHS` 通过独立 sidecar 路径进入反馈包

优先方案：

- 在反馈 HDF5 包中新增显式 group / dataset

次优方案：

- 单独文本 sidecar 文件，例如 `mage_waccmx_nsrhs_rank*.txt`

不推荐方案：

- 长期继续复用当前 `neutral_rhs` 第 6 列语义不清地混跑

### Phase 4：物理校准

当前状态：已完成 first-pass 语义校准，符号/缩放/GEO 投影校准仍待继续

目标：

- 校准 `WACCM-X rhs` 与 `TIEGCM nsrhs/gnsrhs`

校准维度：

- 符号
- 缩放系数
- 单位
- GEO 投影
- 半球折叠 / 赤道处理

当前依据：

- [MAGE_WACCMX_NEUTRAL_RHS_CALIBRATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NEUTRAL_RHS_CALIBRATION_20260327.md)
- [MAGE_WACCMX_NSRHS_PHASE4_FIRSTPASS_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_PHASE4_FIRSTPASS_CN.md)
- [MAGE_WACCMX_NSRHS_CODE_ALIGNMENT_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_CODE_ALIGNMENT_CN.md)
- [MAGE_WACCMX_NSRHS_TRANSFORM_EXPERIMENT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_TRANSFORM_EXPERIMENT_20260327.md)
- [nsrhs_phase4_analysis.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/nsrhs_phase4_analysis.md)

当前 first-pass 结论：

- `WACCM-X` sidecar 目前表现为 folded-source，而不是完整双半球 GEO 物理场
- `mirror_south_folded_source_to_north` 在 first-pass 阶段可视为临时实验展开，但该结论已由后续 `raw/no-mirror` 工作点验证更新
- `WACCM-X rhs` 当前更接近 `TIEGCM` 的 solver-scale `nsrhs`，而不是直接对齐到 coupler-scale `gnsrhs`
- `solver_to_tiegcm_coupler_like` 变换分支已落地，但当前会把 `NSRHS` 压到 `~1e-6` 量级；这说明后续若采用该变换，必须同步重整定 `Kaiju` 侧 `NSRHS` 注入尺度
- 在完成符号/缩放/GEO 投影校准前，不应把这条线升级为正式 neutral-dynamo 完成态

最新补充：

- `Kaiju NSRHS` 注入尺度扫描已完成，见
  [MAGE_WACCMX_NSRHS_SCALE_SCAN_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_SCALE_SCAN_20260327.md)
- `dfac` 常数级对齐说明已补充，见
  [MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md)
- `GEO` 投影链路差异说明已补充，见
  [MAGE_WACCMX_NSRHS_GEO_PROJECTION_GAP_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_PROJECTION_GAP_CN.md)
- direct `mag -> geo` 验证说明已补充，见
  [MAGE_WACCMX_NSRHS_GEO_PROJECTION_VALIDATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_PROJECTION_VALIDATION_20260327.md)
- `unfolding` 工作点验证说明已补充，见
  [MAGE_WACCMX_NSRHS_UNFOLDING_VALIDATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_UNFOLDING_VALIDATION_20260327.md)
- `GEO sidecar` canonicalization 说明已补充，见
  [MAGE_WACCMX_NSRHS_GEO_SIDECAR_CANONICALIZATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_SIDECAR_CANONICALIZATION_20260327.md)
- 这轮扫描表明：
  - `1e4` 仍接近无响应
  - `1e5` 开始出现可见 `POT` 变化
  - `~4.18e5` 是当前最自然的工作点
  - `1e6` 已进入强响应区
  - `1e7` 虽可跑通 smoke，但不适合当标定基线
- 因此，下一步不再做盲扫，应固定 `KAIJU_NSRHS_SCALE ~ 4e5`，转入符号/缩放/GEO 投影对齐
- `dfac` 跨模型常数差异只有 `~0.108%`，不再单独视为主要风险
- 并且这一点已经在 `step2` 工作点验证中得到确认，见
  [nsrhs_workpoint_compare_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_crossmodel/nsrhs_workpoint_compare_20260327.md)
- 进一步地，direct `mag -> geo 2D` 与当前 bridge `GEO` 链在同一套 `WACCM-X GEO` 网格上的 first-pass 对比也已经几乎逐点一致
- 再进一步，`raw/no-mirror` 与 `mirror` 在当前工作点的 `CPCP` 也已无可见差异；`mirror` 主要只是把北半球 `NSRHS` 人工补齐到与南半球完全相同
- 因此，当前 bridge 默认 `NSRHS_UNFOLDING` 已切换为 `none`，`mirror` 降级为 legacy/debug 选项
- 再进一步，raw/no-mirror 反馈包与 direct `GEO sidecar` 反馈包在
  `feedback_geo_{north,south}/neutral_rhs` 数组上也已几乎逐点一致
- 因此，`NSRHS` 的 canonical bridge source 已可以从
  folded-source sidecar 转向 `geo_projected_rhs_sidecar`
- 并且 `geo sidecar` 路线的 `step2 Kaiju` smoke 也已完成，说明这不是
  仅仅数组层的等价，而是已在 `Kaiju` 响应层通过当前工作点验收
- 并且 `geo_projected_rhs_sidecar + solver_to_tiegcm_coupler_crossmodel`
  的候选包已经可生成，后续 `TIEGCM gnsrhs` 对齐可直接基于这一路线推进
- 这条路线的 `step2 Kaiju` 工作点也已完成，见
  [MAGE_WACCMX_NSRHS_GEO_XMODEL_WORKPOINT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_GEO_XMODEL_WORKPOINT_20260327.md)
- 因此下一步不再围绕 `scale`、`dfac` 或 `GEO` 投影链本身反复试探，而是直接转入：
  - `geo_projected_rhs_sidecar -> TIEGCM gnsrhs`
  - `solver/coupler` 语义
  - `TIEGCM gnsrhs` 对齐

### Phase 5：回归与验收

必须同时满足：

- 正式 5 变量闭环不回归
- `NSRHS` 实验路径可单独启停
- 计算节点闭环测试通过
- 文档口径继续保持“正式基线”和“实验增强项”分开

## 5. 当前不建议做的事

- 直接把 `edyn_rhs` 塞进现在的 `NEUTRAL_WIND(cm/s)` 槽位
- 把 `neutral_rhs` 重新改回“当前正式完成变量”
- 在没有校准完之前宣称已完成 `neutral-dynamo` 正式耦合

## 6. 下一次真正开工时的推荐顺序

1. 在隔离实验线里新增 `Kaiju` 变量 `NEUTRAL_DYNAMO_RHS / NSRHS`
2. 保持正式 5 变量闭环不动
3. 给 `WACCM-X` 导出 `edyn_rhs` 的 sidecar 实验协议
4. 固定 `KAIJU_NSRHS_SCALE ~ 4e5`，做 `rhs -> NSRHS` 工作点验证
5. 再开始符号/缩放/GEO 投影物理校准
6. 进入真实 `MAGE` 驱动 `TIEGCM gnsrhs` 的逐发送时刻对齐

最新补充：

- 真实 `MAGE-TIEGCM` coupled smoke 的 `gnsrhs` GEO 诊断已经拿到，见
  [MAGE_WACCMX_TIEGCM_GNSRHS_MATCHED_COMPARISON_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_TIEGCM_GNSRHS_MATCHED_COMPARISON_20260327.md)
- 这轮对比说明 `WACCM-X` 当前 canonical 候选与 `TIEGCM gnsrhs`
  已进入“弱正相关、可继续校准”的阶段
- 因此下一步不再是“能不能拿到 `gnsrhs`”，而是：
  - 保留多个发送时刻快照
  - 做逐发送时刻 cross-model 对齐
  - 再收敛最终的符号、缩放和 hemisphere 语义
- 再进一步，`TIEGCM` 这一侧的多发送时刻快照也已经完成，见
  [MAGE_WACCMX_TIEGCM_GNSRHS_TIMESERIES_CAPTURE_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_TIEGCM_GNSRHS_TIMESERIES_CAPTURE_20260327.md)
- 因此路线图上的下一实际阻塞项，已经变成：
  - 给 `WACCM-X` 侧建立同类时序快照
  - 再做逐发送时刻对齐

## 7. 当前一句话判断

下一阶段应当把 `neutral-dynamo` 从“proxy 加到 `NEUTRAL_WIND`”升级为“显式 `NSRHS` 变量通道”，并且全过程都要与当前正式 5 变量基线隔离管理。
