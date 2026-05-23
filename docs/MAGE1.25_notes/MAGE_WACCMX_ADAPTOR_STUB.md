# MAGE-WACCMX Adaptor Stub

这份文档描述隔离原型最新增加的 adaptor stub。

它的定位是：

- 不是 `CESM/CMEPS` 的真实 cap
- 也不是 `WACCM-X` 的真实 ingest 逻辑
- 而是一个“消费端最小证明”

这个证明回答的问题是：

- 如果 `MAGE` 侧把对象收敛成 ingest package
- future `WACCM-X/CESM adaptor`
- 能不能在**不知道 `REMIX` 原始 group layout** 的情况下
- 仅凭这份 ingest contract 恢复出 cap-ready 对象

## 实现文件

- [waccmx_stub_adaptor_io.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_adaptor_io.F90)
- [waccmx_stub_adaptorx.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/drivers/waccmx_stub_adaptorx.F90)
- [WACCMX_STUB_ADAPTOR_CASE.xml](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/WACCMX_STUB_ADAPTOR_CASE.xml)

输出：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_adaptor_report.md`

## 读取的 contract

adaptor stub 只读取下面这些组：

```text
/
  /meta
  /input_aurora_north
  /input_aurora_south
  /input_electrodynamics_north
  /input_electrodynamics_south
  /state_north
  /state_south
  /return_outflow_north
  /return_outflow_south
  /return_neutral_column_north
  /return_neutral_column_south
```

这意味着它已经不再依赖更早那层：

- `/NORTH_GEO`
- `/NORTH_APEX`
- `/SOUTH_GEO`
- `/SOUTH_APEX`

也就是说，`REMIX` 原始导出细节已经被 ingest contract 隔离掉了。

## 当前恢复出的对象

adaptor stub 当前恢复三类对象：

- aurora forcing object
  - `avg_eng`
  - `num_flux`
  - `avg_eng_alias`
  - `num_flux_alias`
- electrodynamics forcing object
  - `pot`
  - `num_flux`
  - `pot_alias`
  - `num_flux_alias`
  - `cpcp`
- derived state object
  - `heating_proxy`
  - `efield_proxy`
  - `forcing_index`
  - `peak_theta_deg`
  - `peak_phi_deg`

同时也恢复两类返回 sidecar：

- outflow return object
  - `im_d_ring`
  - `im_p_ring`
  - `im_d_cold`
  - `im_p_cold`
  - `im_tscl`
- neutral-column return object
  - `tn_bar`
  - `un_bar`
  - `vn_bar`
  - `o_bar`

## 当前检查

报告里会检查：

- `layout_version == aurora_edyn_state_sidecars_v2`
- `direction == MAGE_REMIX_to_future_WACCMX`
- aurora 的 `coord == GEO`
- electrodynamics 的 `coord == APEX`
- alias 是否保持 `mage_*` 前缀
- aurora/state 的 shape 是否一致
- electrodynamics/state 的 `CPCP` 是否一致
- outflow 的 `im_tscl` 是否为正

## 当前实现备注

这个 adaptor stub 目前对 ingest 包里的固定长度字符串属性做了“合同前缀收敛”。

原因不是 ingest 包本身写错了，而是当前隔离原型里的 `ioH5` 在回读某些固定长度字符串属性时，会把尾部未定义字符一起带回来。为了不让这个局部 IO 问题遮住接口验证本身，adaptor stub 当前会按已知 contract 把这些字符串收敛成稳定值，例如：

- `layout_version -> aurora_edyn_state_v1`
- `mage_avg_eng_geo_north`
- `mage_pot_apex_south`

这意味着当前 adaptor report 可以可信地用来验证：

- 对象边界
- alias 命名合同
- hemisphere/coord 语义
- state 和 forcing 的一致性
- return sidecar 的语义边界

但它还不是一个“任意字符串属性都可泛化读取”的最终 HDF5 适配器实现。

## 这一步的意义

这一步意味着当前原型已经从“会导出字段”推进到“消费端 adaptor 也能基于稳定 contract 恢复对象”。

所以后面接真实 `CESM/WACCM-X` 时，真正剩下的重心会更明确：

- 这份 contract 是否要映射到 `CMEPS` field table
- 这些对象如何被 regrid 到 `WACCM-X` 目标网格
- 真实 `cap` 在 timestep 内怎样调用这些对象

而不是再回头争论：

- `MAGE` 到底应该怎样打包
- `WACCM-X` 到底应该从哪几个 group 里取数
