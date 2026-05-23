# MAGE-WACCMX Ingest Adaptor Contract

这份文档总结隔离原型里已经跑通的 `ingest -> adaptor -> outflow payload` 合同层。

它对应的目标不是复刻真实 `CMEPS/NUOPC` 接口，而是先把未来 `WACCM-X` 和 sidecar consumer 真正要消费的对象固定下来。

## 已验证的链路

当前隔离原型已经实际跑通：

- `REMIX -> forward package`
- `forward package -> pseudo consumer`
- `pseudo consumer -> pseudo state`
- `pseudo state -> ingest package`
- `ingest package -> adaptor objects`
- `ingest package -> IMAG/MHD-style outflow payload`

对应产物在：

- [waccmx_stub_ingest_package.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_ingest_package.h5)
- [waccmx_stub_ingest_report.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_ingest_report.md)
- [waccmx_stub_adaptor_report.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_adaptor_report.md)
- [waccmx_stub_outflow_payload.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_outflow_payload.txt)
- [waccmx_stub_outflow_payload_report.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_outflow_payload_report.md)

## Ingest Package Layout

`ingest` 包当前把对象稳定到 11 个 group：

- `/meta`
- `/input_aurora_north`
- `/input_aurora_south`
- `/input_electrodynamics_north`
- `/input_electrodynamics_south`
- `/state_north`
- `/state_south`
- `/return_outflow_north`
- `/return_outflow_south`
- `/return_neutral_column_north`
- `/return_neutral_column_south`

它的作用是把原始 `REMIX` 导出细节折叠成三类未来消费端真正关心的对象：

- aurora forcing
- electrodynamics forcing
- derived atmospheric-side state

同时保留两类返向 sidecar：

- outflow return
- neutral column return

实现位置：

- [waccmx_stub_ingest_package.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_ingest_package.F90)
- [waccmx_stub_ingestx.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/drivers/waccmx_stub_ingestx.F90)

## Adaptor Contract

`adaptor` 现在已经不依赖原始 `forward package` 的 group 命名，而是只依赖 `ingest` 合同。

它恢复出来的对象包括：

- `Aurora NORTH/SOUTH`
- `Electrodynamics NORTH/SOUTH`
- `State NORTH/SOUTH`
- `Outflow NORTH/SOUTH`
- `Neutral Column NORTH/SOUTH`

当前已验证的约束包括：

- `layout_version == aurora_edyn_state_sidecars_v2`
- `direction == MAGE_REMIX_to_future_WACCMX`
- aurora 输入坐标是 `GEO`
- electrodynamics 输入坐标是 `APEX`
- alias 保持 `mage_*` 前缀
- aurora/state 的 `theta` shape 一致
- edyn/state 的 `CPCP` 一致
- outflow timescale 为正

实现位置：

- [waccmx_stub_adaptor_io.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_adaptor_io.F90)
- [waccmx_stub_adaptorx.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/drivers/waccmx_stub_adaptorx.F90)

## Outflow Payload

`outflow payload` 这层的目的，是模拟未来一个非常轻量的 sidecar consumer。

当前文本 payload 固定顺序为：

- `im_d_ring`
- `im_p_ring`
- `im_d_cold`
- `im_p_cold`
- `im_tscl`

这意味着未来如果 `IMAG/MHD` 只想拿最小一组 outflow 驱动量，它不需要理解整个 ingest 包，只要消费这 5 个标量即可。

实现位置：

- [waccmx_stub_outflow_payloadx.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/drivers/waccmx_stub_outflow_payloadx.F90)

## 对真实 CESM/WACCM-X 的意义

这层原型已经足够说明两件事：

- 你后面真正需要稳定的，不是 `REMIX` 原始字段文件格式，而是 `ingest contract`
- 回传路径未必都要走完整 mediator；一部分 sidecar 可以被压成更小、更稳定的 payload

所以后续如果接真实 `CESM/WACCM-X`，更合理的工作顺序是：

1. 先把这份 `ingest contract` 当作临时稳定接口
2. 再把 contract 中的对象映射到真实 `cap/mediator/state` 数据结构
3. 最后再决定哪些返向量走正式 mediator，哪些保留 sidecar 方式
