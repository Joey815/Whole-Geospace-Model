# MAGE-WACCMX NSRHS 主 Bridge 可选接入说明

日期：2026-03-30

## 1. 本次完成了什么

本次没有改写当前正式 5 变量基线，而是把 `NSRHS sidecar` 的桥接能力并入了当前主 bridge 脚本，并保持**默认关闭**。

这意味着：

- 当前默认 formal 主流程仍然只走  
  `POT / AVG_ENG / NUM_FLUX -> WACCM-X`  
  `SIGMAP / SIGMAH -> MAGE/REMIX`
- 但如果后续要继续推进 `neutral_rhs / NSRHS`，现在已经可以直接在主 bridge 上通过开关接入：
  - `sidecar`
  - `geo_sidecar`

## 2. 本次改动的文件

- 主 bridge 脚本：
  [cesm_feedback_to_kaiju_feedback.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cesm_feedback_to_kaiju_feedback.py)
- 单轮正式桥入口：
  [run_bidirectional_cycle.sh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh)
- 多轮正式桥入口：
  [run_long_coupling_stability.sh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_long_coupling_stability.sh)

## 3. 新增的主流程开关

当前主桥支持：

- `WACCMX_NSRHS_SOURCE_MODE=off|sidecar|geo_sidecar`
- `WACCMX_NSRHS_UNFOLDING=none|mirror_south_folded_source_to_north`
- `WACCMX_NSRHS_TRANSFORM=none|solver_to_tiegcm_coupler_like|solver_to_tiegcm_coupler_crossmodel`

默认值：

- `WACCMX_NSRHS_SOURCE_MODE=off`
- `WACCMX_NSRHS_UNFOLDING=none`
- `WACCMX_NSRHS_TRANSFORM=none`

## 4. 行为说明

### 4.1 `off`

默认 formal 行为，不导出 `NSRHS sidecar`，不改变当前 live 正式主流程。

### 4.2 `sidecar`

`CESM` 侧导出：

- `mage_waccmx_nsrhs_rank*.txt`

主 bridge 会把这类 sidecar 合并进 `feedback_geo_{north,south}/neutral_rhs`。

当前语义是：

- `folded_solver_rhs_sidecar`
- `mag_to_phys_regrid_then_bridge_regular_remap`

### 4.3 `geo_sidecar`

`CESM` 侧导出：

- `mage_waccmx_nsrhs_geo_rank*.txt`

主 bridge 会把它作为当前更推荐的 canonical source 写入 `feedback_geo_{north,south}/neutral_rhs`。

当前语义是：

- `geo_projected_rhs_sidecar`
- `direct_mag_to_geo_2d_sidecar`

## 5. 本次验证范围

本次做的是**桥接级兼容验证**，没有直接在 live 主流程上启用这些开关重新跑 `cesm.exe`。

验证目录：

- [compat_checks_20260330](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/compat_checks_20260330)

生成了三份反馈包：

- formal 5 列兼容包：
  [formal_cycle01_feedback.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/compat_checks_20260330/formal_cycle01_feedback.h5)
- `NSRHS sidecar` 包：
  [nsrhs_sidecar_feedback.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/compat_checks_20260330/nsrhs_sidecar_feedback.h5)
- `NSRHS GEO sidecar` 包：
  [nsrhs_geo_feedback.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/compat_checks_20260330/nsrhs_geo_feedback.h5)

## 6. 当前验证结果

### 6.1 formal 5 列保持不变

- `schema_version = 0.1`
- `producer = CESM_WACCMX_BRIDGE`
- `nsrhs_source = inline_or_zero`
- `feedback_geo_north/south neutral_rhs absmax = 0`

这说明默认 formal 基线没有被这次改动打坏。

### 6.2 `sidecar` 路径已能被主 bridge 吃进去

- `schema_version = 0.2`
- `producer = CESM_WACCMX_BRIDGE_NSRHS`
- `nsrhs_source = nsrhs_sidecar`
- `feedback_geo_south neutral_rhs absmax = 5.545069933882411e+07`

同时 `north = 0`，这与当前 raw folded-source sidecar 的已知语义一致。

### 6.3 `geo_sidecar` canonical 路径已能被主 bridge 吃进去

- `schema_version = 0.2`
- `producer = CESM_WACCMX_BRIDGE_NSRHS`
- `nsrhs_source = nsrhs_geo_sidecar`
- `feedback_geo_north neutral_rhs absmax = 5.4874416196573004e+07`
- `feedback_geo_south neutral_rhs absmax = 5.545069933882278e+07`

这说明当前主 bridge 已经能直接处理 canonical `geo_projected_rhs_sidecar`。

## 7. 当前最合理的理解

当前 `neutral_rhs / NSRHS` 这条线的状态已经从：

- 只存在于独立实验脚本

推进到了：

- 主 bridge 与主入口脚本已具备**按开关启用**的能力
- 默认 formal 基线保持不变
- canonical `geo_sidecar` 路径已完成桥接级验证

## 8. 还没做的事

本次最开始还没有做：

- 在 live `run_bidirectional_cycle.sh` 上直接开 `WACCMX_NSRHS_SOURCE_MODE=geo_sidecar` 重跑一轮
- 在 live `run_long_coupling_stability.sh` 上做多轮 `NSRHS` 开关验证
- 把 `Kaiju` 从当前 `NEUTRAL_WIND` proxy 路线升级到显式 `NSRHS` 主线变量

## 9. 新增 live 单轮验证

随后又补做了一次 live 主流程单轮验证：

- 目录：
  [live_nsrhs_geo_x1_c1_20260330_live_nsrhs_geo_x1c1](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_nsrhs_geo_x1_c1_20260330_live_nsrhs_geo_x1c1)
- 条件：
  - `WACCMX_REPAIR_OP_HOOK=1`
  - `WACCMX_NSRHS_SOURCE_MODE=geo_sidecar`
  - `x1/x1/x1`
  - `num_cycles=1`

结果是：

- 新开关已真实传入 `CESM`，并成功写出
  `mage_waccmx_nsrhs_geo_rank*.txt`
- 主 bridge 也成功生成了
  [cycle01_waccmx_cesm_feedback_package.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_nsrhs_geo_x1_c1_20260330_live_nsrhs_geo_x1c1/cycle01_waccmx_cesm_feedback_package.h5)
- `CESM` 本轮 continuation 正常结束，见
  [cycle01_summary.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_nsrhs_geo_x1_c1_20260330_live_nsrhs_geo_x1c1/cycle01_summary.txt)
- `cycle01_kaiju` 也成功完成，见
  [waccmx_voltron_contract.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_nsrhs_geo_x1_c1_20260330_live_nsrhs_geo_x1c1/cycle01_kaiju/waccmx_voltron_contract.txt)

但最关键的新事实是：

- 这轮 live `geo_sidecar` 写出来的是**零场**
- `mage_waccmx_feedback_rank*_summary.txt` 里：
  - `edyn_rhs_absmax = 0`
  - `edyn_rhs_geo_absmax = 0`
  - `wrote_nsrhs_geo_sidecar = T`
- 最终 `Kaiju` 合同里：
  - `NEUTRAL_DYNAMO_RHS absmax = 0.000 cm/s`

所以这轮 live 验证把 blocker 进一步前移到了：

- 不是主 bridge 不支持 `NSRHS`
- 也不是 live 主流程没把 sidecar 走通
- 而是当前这轮 `CESM/WACCM-X` 本身给出的 `edyn rhs` 源场为零

## 10. 当前最准确的结论

截至 `2026-03-30`，`neutral_rhs / NSRHS` 这条线已经推进到：

1. 主 bridge 已具备可选接入能力，默认不影响 formal baseline
2. canonical `geo_sidecar` 路径已完成桥接级验证
3. live 单轮主流程也已成功把 `geo_sidecar` 走完整条链
4. 当前真正的新 blocker 已收缩为：
   - `CESM/WACCM-X edyn_rhs / edyn_rhs_geo` 在这轮 live case 中为零

也就是说，后续主要该追的是 `edynamo rhs` 的生成条件和调用时机，而不是继续改 bridge 结构

## 11. 下一步建议

下一步最自然的是：

1. 直接回溯 `CESM/WACCM-X` 里为什么这轮 `edyn_rhs_absmax = 0`
2. 分清这是：
   - 物理上确实为零
   - 还是当前 `rhs_bothhem`/`gather_edyn`/导出时机没对上
3. 只有在 `edyn_rhs` 本身变成非零后，再继续做 live 多轮 `NSRHS` 开关验证
4. 最后再讨论是否把 `Kaiju` 侧从 `NEUTRAL_WIND` proxy 切换到显式 `NSRHS`

## 12. `postrefresh` 更新

随后又继续沿这条线往前推进了一步，核心不是再改 bridge，而是修正
`CESM/WACCM-X` 里 `edyn rhs` cache 的刷新时机。

本次源码调整是：

- 在
  [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90)
  新增 `mage_waccmx_refresh_edyn_rhs()`
- 在
  [ionosphere_interface.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90)
  的 `call d_pie_coupling(...)` 之后立即调用这一步 refresh

这样做的目的很直接：

- `phys_run2` 里原先 capture 到的是较早阶段 cache
- `d_pie_coupling` 之后 `rhs_bothhem` 才真正更新
- 所以 `NSRHS GEO sidecar` 的正确抓取时机应在 `d_pie_coupling` 之后

修完后，先没有直接回到长流程，而是在隔离 continuation 上验证：

- 运行目录：
  [restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh)
- summary：
  [summary.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/summary.txt)

这次最关键的新事实是：

- `edyn_rhs_absmax` 已不再是零
- `edyn_rhs_geo_absmax` 也已不再是零
- `mage_waccmx_nsrhs_geo_rank*.txt` 已写出非零场

直接证据在各 rank summary：

- [rank000000 summary](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/run/mage_waccmx_feedback_rank000000_summary.txt)
  `edyn_rhs_absmax = 4.4036454298272066E+07`
  `edyn_rhs_geo_absmax = 4.9739641809171423E+07`
- [rank000003 summary](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/run/mage_waccmx_feedback_rank000003_summary.txt)
  `edyn_rhs_absmax = 5.3296008092669755E+07`
  `edyn_rhs_geo_absmax = 5.3296008092668504E+07`

主 bridge 也已经把这份非零 `geo_sidecar` 成功转成反馈包：

- [waccmx_cesm_feedback_package_postrefresh.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/waccmx_cesm_feedback_package_postrefresh.h5)

该包现在的真实状态是：

- `nsrhs_source = nsrhs_geo_sidecar`
- `nsrhs_transform = none`
- `feedback_geo_north/neutral_rhs absmax = 5.32960080926685e+07`
- `feedback_geo_south/neutral_rhs absmax = 4.973964180917142e+07`

最后一跳 `Kaiju` 也已经补跑验证：

- step2 目录：
  [kaiju_step2_postrefresh_rerun](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/kaiju_step2_postrefresh_rerun)
- 合同文件：
  [waccmx_voltron_contract.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260330_nsrhs_iso_01500_postrefresh/kaiju_step2_postrefresh_rerun/waccmx_voltron_contract.txt)

这次合同里：

- `SIGMAP/SIGMAH` 已正常更新
- `NEUTRAL_DYNAMO_RHS absmax` 已不是 `0.000`
- 但由于当前输出格式还是 `f10.3`，数值太大，直接显示成了 `**********`

这意味着当前最准确的口径已经变成：

1. `geo_sidecar` 的零场 blocker 已被定位并修掉
2. `CESM -> bridge -> Kaiju` 的 `NSRHS` 数据路径现在已经能走通到 `Kaiju contract`
3. 当前剩下的主问题不再是“有没有场”，而是“当前 raw `edyn_rhs_geo` 的量级/单位是否要做额外变换和重标定”

所以 `NSRHS` 这条线现在的 blocker 已经前移为：

- 不再是导出时机
- 不再是 bridge 兼容性
- 而是 `raw edyn_rhs_geo (~5e7)` 与 `Kaiju NEUTRAL_DYNAMO_RHS` 注入尺度之间的量级收敛

## 13. `postrefresh` 工作点补验

在确认 `raw geo_sidecar` 已经非零并能走到 `Kaiju contract` 之后，又补做了一轮
最小工作点验证，目的不是再证明链路能通，而是回答：

- 这份最新 `postrefresh` 源场
- 放到现有 `phase2 NSRHS` 变换/尺度工作线上
- 还能不能保持稳定、可见、且不过强

本次新生成的三个反馈包在：

- [postrefresh_transform_tests_20260330a](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_transform_tests_20260330a)

分别是：

- [postrefresh_raw_geo.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_transform_tests_20260330a/postrefresh_raw_geo.h5)
- [postrefresh_coupler_like.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_transform_tests_20260330a/postrefresh_coupler_like.h5)
- [postrefresh_coupler_crossmodel.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_transform_tests_20260330a/postrefresh_coupler_crossmodel.h5)

包级 `NSRHS absmax` 为：

- raw `geo_sidecar`
  - North `5.32960080926685e+07`
  - South `4.973964180917142e+07`
- `solver_to_tiegcm_coupler_like`
  - North `1.273870016158155e-06`
  - South `1.1888664945595844e-06`
- `solver_to_tiegcm_coupler_crossmodel`
  - North `1.2752501100279053e-06`
  - South `1.1901544967421317e-06`

随后用 `phase2` 二进制和现有 scale-probe 脚本，补做了三组短 probe：

- 控制组：
  [postrefresh_raw_geo_scale0](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_raw_geo_scale0)
- `coupler-like @ 4.18378699684e5`：
  [postrefresh_coupler_like_4p18e5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_coupler_like_4p18e5)
- `crossmodel @ 4.18378699684e5`：
  [postrefresh_coupler_crossmodel_4p18e5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_coupler_crossmodel_4p18e5)

三组 summary 分别在：

- [raw summary](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_raw_geo_scale0/nsrhs_scale_probe_summary.txt)
- [coupler-like summary](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_coupler_like_4p18e5/nsrhs_scale_probe_summary.txt)
- [crossmodel summary](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_coupler_crossmodel_4p18e5/nsrhs_scale_probe_summary.txt)

这轮最关键的结果是：

1. 三组都稳定完成，没有新的数值失稳
2. raw 控制组在 `scale=0` 下保留原始超大 `NSRHS` 包幅值，但不向求解器注入
3. `coupler-like` 与 `crossmodel` 在 `4.18e5` 工作点下都稳定回到 `~1.2e-6` 的合同量级
4. 两条 transform 的响应几乎重合

合同值：

- raw `scale=0`
  - H1 `NSRHS absmax = 5.3296E+07`
  - H2 `NSRHS absmax = 4.9740E+07`
- `coupler-like @ 4.18e5`
  - H1 `NSRHS absmax = 1.2739E-06`
  - H2 `NSRHS absmax = 1.1889E-06`
- `crossmodel @ 4.18e5`
  - H1 `NSRHS absmax = 1.2753E-06`
  - H2 `NSRHS absmax = 1.1902E-06`

对应 forward `POT` 范围：

- raw `scale=0`
  - North `-13.1430 / 10.9712 kV`
  - South `-15.8848 / 13.6946 kV`
- `coupler-like @ 4.18e5`
  - North `-9.40238 / 18.1043 kV`
  - South `-15.4911 / 15.3800 kV`
- `crossmodel @ 4.18e5`
  - North `-9.39842 / 18.1181 kV`
  - South `-15.4908 / 15.3819 kV`

对应 exchange 文件：

- [raw exchange](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_raw_geo_scale0/step2_kaiju_feedback/waccmx_voltron_exchange.md)
- [coupler-like exchange](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_coupler_like_4p18e5/step2_kaiju_feedback/waccmx_voltron_exchange.md)
- [crossmodel exchange](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_scale_probe_runs_20260330a/postrefresh_coupler_crossmodel_4p18e5/step2_kaiju_feedback/waccmx_voltron_exchange.md)

因此，这一轮可以把结论再往前收紧一步：

- 最新 `postrefresh` 非零 `geo_sidecar` 并没有把旧工作点打坏
- `solver_to_tiegcm_coupler_like` 和 `solver_to_tiegcm_coupler_crossmodel`
  在当前最新源场上仍然都是稳定可用的
- 而且 `crossmodel` 相对 `coupler-like` 的差异依然小到几乎可以忽略

所以现在 `NSRHS` 这条线的优先级已经进一步聚焦为：

- 不再需要怀疑 `postrefresh` 源场能否接到现有工作点
- 下一步应把注意力放到：
  - 选择 `coupler_like` 还是 `crossmodel` 作为继续对齐基线
  - 以及最终面向 `TIEGCM gnsrhs` 的物理语义定稿

## 14. `crossmodel` 三点矩阵

随后又按“只保留一个实验基线”的思路，直接把：

- `solver_to_tiegcm_coupler_crossmodel`

固定为当前唯一实验基线，并在最新 `postrefresh` 源场上补做了：

- `1e5`
- `4.18378699684e5`
- `1e6`

三点尺度矩阵。

完整结果已单独整理为：

- [MAGE_WACCMX_NSRHS_POSTREFRESH_XMODEL_SCALE_SCAN_20260330.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_POSTREFRESH_XMODEL_SCALE_SCAN_20260330.md)

这一步的新结论是：

1. `postrefresh` 之后，`crossmodel` 基线仍然稳定成立
2. 合同里的 `NSRHS absmax` 不随 `KAIJU_NSRHS_SCALE` 变化，这是当前 `phase2` 设计预期
3. 真正区分工作点的是 `POT` 响应
4. 在三点里，`4.18e5` 仍然是最平衡的工作点

因此当前推荐口径可以进一步收紧为：

- 若只保留一条实验基线，优先保留
  `geo_sidecar + solver_to_tiegcm_coupler_crossmodel + KAIJU_NSRHS_SCALE≈4.18e5`
