# MAGE-WACCMX Mock Cap Fields

这份文档描述隔离原型里最新补上的一层：

- `ingest contract`
- `adaptor objects`
- `mock CESM/WACCM-X cap fields`

它的目的，是把前面已经稳定下来的对象合同，进一步落成“更像未来 `WACCM-X/CMEPS cap` 会注册什么字段”的形式。

## 已验证产物

当前已经实际生成并验证：

- [waccmx_stub_cap_fields_report.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_cap_fields_report.md)
- [waccmx_stub_cap_fields_package.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_cap_fields_package.h5)

实现文件：

- [waccmx_stub_cap_fields.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_cap_fields.F90)
- [waccmx_stub_capfieldsx.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/drivers/waccmx_stub_capfieldsx.F90)
- [WACCMX_STUB_CAP_FIELDS_CASE.xml](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/WACCMX_STUB_CAP_FIELDS_CASE.xml)

## Package Layout

当前 mock cap 包分成 9 组：

- `/meta`
- `/cap_import_geo_north`
- `/cap_import_geo_south`
- `/cap_import_apex_north`
- `/cap_import_apex_south`
- `/cap_internal_state_north`
- `/cap_internal_state_south`
- `/cap_export_outflow`
- `/cap_export_neutral_column`

这里真正关键的是三层语义：

- import state
- internal state
- export sidecars

## Import Fields

mock cap 现在把前向输入注册成 8 个 import 字段：

- `mage_avg_eng_geo_north`
- `mage_num_flux_geo_north`
- `mage_avg_eng_geo_south`
- `mage_num_flux_geo_south`
- `mage_pot_apex_north`
- `mage_num_flux_apex_north`
- `mage_pot_apex_south`
- `mage_num_flux_apex_south`

其中：

- `GEO` 组用于 aurora forcing
- `APEX` 组用于 electrodynamics forcing

## Internal State

mock cap 还保留了一层内部状态代理量：

- `energy_flux_proxy`
- `heating_proxy`
- `potential`
- `efield_proxy`
- `forcing_index`

这层不是 mediator 字段表本身，但很接近未来 `WACCM-X` 侧 ingest 后会保留的工作状态。

## Export Sidecars

返向量在 mock cap 里被改写成 `waccmx_*` 前缀的 export 字段。

当前 outflow export 包含：

- `waccmx_im_d_ring_north/south`
- `waccmx_im_p_ring_north/south`
- `waccmx_im_d_cold_north/south`
- `waccmx_im_p_cold_north/south`
- `waccmx_im_tscl_north/south`

当前 neutral-column export 包含：

- `waccmx_tn_bar_north/south`
- `waccmx_un_bar_north/south`
- `waccmx_vn_bar_north/south`
- `waccmx_o_bar_north/south`

## 验证结论

这层原型已经验证了三件事：

- `ingest contract` 足够支撑一次更接近 cap 的字段注册
- 前向 import alias 和返向 export alias 可以在这一层明确分家
- sidecar return path 可以被收敛成独立 export contract，而不必强行混回原始 `REMIX` 输出语义

## 对下一步的意义

如果后面开始接真实 `CESM/WACCM-X`，这层最有用的地方不是文件格式，而是字段职责已经被拆清：

- 哪些是 cap import
- 哪些是 cap internal state
- 哪些是 cap export/sidecar

这样后面真正落到 `CMEPS/NUOPC` 时，工作重点就可以更集中在：

- import/export state registration
- mediator field dictionary
- 重网格
- 时间同步
