# MAGE-WACCMX Pseudo State Updater

这个文档描述隔离原型里的“伪 `WACCM-X` 状态更新器”做了什么，以及它为什么比单纯改字段名更有价值。

## 目的

在真实 `CESM/WACCM-X` 源码尚未接入之前，这个状态更新器用来回答一个更关键的问题：

- `MAGE/REMIX` 导出的 `POT / AVG_ENG / NUM_FLUX`
- 在“大气模式侧”被消费以后
- 能不能先稳定地组织成一组内部状态代理量

如果这一步都不清楚，那么后面即使把字段名改成更像 `CMEPS` 的样子，也只是表面收敛，不是真正的接口收敛。

## 输入

状态更新器不直接读 `REMIX`，而是读前面已经稳定下来的消费端对象：

- `Aurora Inputs`
  - `AVG_ENG`
  - `NUM_FLUX`
- `Electrodynamics Inputs`
  - `POT`
  - `NUM_FLUX`

这些对象来自：
- [waccmx_stub_consumer.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_consumer.F90)
- [waccmx_stub_state_update.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_state_update.F90)

## 当前导出的状态代理量

每个半球当前都会生成：

- `energy_flux_proxy = AVG_ENG * NUM_FLUX`
- `heating_proxy = normalized(energy_flux_proxy)`
- `potential = POT`
- `efield_proxy = |grad(POT)|`
- `forcing_index = heating_proxy + normalized(efield_proxy)`

另外还输出每个半球的摘要量：

- `CPCP`
- `mean heating_proxy`
- `mean efield_proxy`
- `mean forcing_index`
- `peak forcing theta/phi`

## 为什么这一步有用

它解决的是“消费端语义”问题，而不是“字段命名”问题。

具体来说，它能提前暴露这些后面一定会碰到的接口风险：

- 南北半球数据是不是应该分开持有
- `GEO` 和 `APEX` 两条输入链在内部怎样合流
- 网格维度顺序和角坐标解释是否稳定
- 光沉降和电动力输入合成以后，是否需要新的派生量
- 现有元数据是否足够支撑一次明确的 ingest

## 输出产物

隔离实验会生成两类输出：

- 报告：
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_state_report.md`
- `HDF5` 状态包：
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_state_package.h5`

状态包当前包含：

- `/Meta`
- `/NORTH_STATE`
- `/SOUTH_STATE`

每个半球组里包括：

- `theta`
- `phi`
- `energy_flux_proxy`
- `heating_proxy`
- `potential`
- `efield_proxy`
- `forcing_index`
- `cpcp`
- `peak_theta_deg`
- `peak_phi_deg`

## 结论

这不是 `WACCM-X` 的真实物理更新器，也不能替代 `CESM/CMEPS` 的正式接线。

它的作用是把接口工作从“只会读包”推进到“已经可以在消费端内部形成一组自洽状态对象”。这一层一旦稳定，后面再接真实 `WACCM-X`，剩下的问题就会更集中在：

- `cap/mediator` 接线
- 重网格
- 字段注册
- 时间同步
