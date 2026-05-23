# MAGE-WACCMX Ingest Object Schema

这份文档描述隔离原型最新增加的“ingest object package”。

它不是最终 `CESM/CMEPS` 在线耦合格式，但它比最初的 forward package 更接近未来 `WACCM-X` 侧真正会 ingest 的对象层。

## 为什么需要这一层

当前原型已经有三层：

- forward package
- pseudo consumer
- pseudo state updater

但如果后面要接真实 `WACCM-X/CESM`，还需要一层更稳定的“交付物”：

- 不再直接暴露 `REMIX` 内部组织方式
- 不再要求消费端自己重新拼 aurora / electrodynamics / state
- 把对象边界先固定下来

所以现在新增了一份 object-oriented 的 `HDF5` 包，目标是让 future adaptor 拿到以后，能更直接地映射到：

- aurora forcing object
- electrodynamics forcing object
- derived atmospheric state object

## 产物位置

- 报告：
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_ingest_report.md`
- 包文件：
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_ingest_package.h5`

实现文件：

- [waccmx_stub_ingest_package.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_ingest_package.F90)
- [waccmx_stub_ingestx.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/drivers/waccmx_stub_ingestx.F90)

## 当前 layout

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

这个 layout 的设计原则是：

- group 名按“对象职责”划分，不按 `REMIX` 内部模块划分
- 前向输入和派生状态显式分开
- 南北半球显式分开
- alias 保留下来，方便 future mediator/cap 做字段映射

## /meta

`/meta` 保存：

- `schema_version`
- `producer`
- `layout_version`
- `source_mix`
- `direction`
- `grid_source`
- `time_seconds`
- `mjd`

当前 `layout_version` 已经提升为：

- `aurora_edyn_state_sidecars_v2`

## /input_aurora_north and /input_aurora_south

每个 aurora group 包含：

- attributes
  - `hemisphere`
  - `coord`
  - `grid_source`
  - `avg_eng_alias`
  - `num_flux_alias`
  - `avg_eng_mean`
  - `num_flux_mean`
  - `energy_flux_proxy_mean`
- datasets
  - `theta`
  - `phi`
  - `avg_eng`
  - `num_flux`

这些对象对应 future `WACCM-X` 里的极光沉降输入。

## /input_electrodynamics_north and /input_electrodynamics_south

每个 electrodynamics group 包含：

- attributes
  - `hemisphere`
  - `coord`
  - `grid_source`
  - `pot_alias`
  - `num_flux_alias`
  - `pot_min`
  - `pot_max`
  - `cpcp`
  - `num_flux_mean`
- datasets
  - `theta`
  - `phi`
  - `pot`
  - `num_flux`

这些对象对应 future `WACCM-X` 里的高纬电势驱动输入。

## /state_north and /state_south

每个 state group 包含：

- attributes
  - `hemisphere`
  - `grid_source`
  - `cpcp`
  - `heating_mean`
  - `efield_mean`
  - `forcing_mean`
  - `peak_theta_deg`
  - `peak_phi_deg`
- datasets
  - `theta`
  - `phi`
  - `energy_flux_proxy`
  - `heating_proxy`
  - `potential`
  - `efield_proxy`
  - `forcing_index`

这些不是 `WACCM-X` 真正的内部预报变量，而是用于 future adaptor 设计的稳定状态代理量。

## /return_outflow_north and /return_outflow_south

每个 outflow return group 包含：

- attributes
  - `hemisphere`
  - `grid_source`
- datasets
  - `im_d_ring`
  - `im_p_ring`
  - `im_d_cold`
  - `im_p_cold`
  - `im_tscl`

这层的目标不是伪装成真实 `IMAG/MHD` 状态，而是把 `WACCM-X -> MAGE` 的轻量离子外流返回量，收敛成一个固定顺序、固定语义的 sidecar 对象。

## /return_neutral_column_north and /return_neutral_column_south

每个 neutral-column return group 包含：

- attributes
  - `hemisphere`
  - `grid_source`
- datasets
  - `tn_bar`
  - `un_bar`
  - `vn_bar`
  - `o_bar`

这层是当前原型里对“neutral moments”类别的最小占位实现。

## 这层的价值

它把问题进一步收敛成：

- future `CESM/WACCM-X` adaptor 应该接哪几个对象
- 每个对象最小需要哪些字段和元数据
- alias、units、hemisphere、coord 是否已经足够稳定

这样等真实 `CESM` 源码到位后，接线重点就可以更集中在：

- field registration
- regridding
- cadence
- cap/mediator glue code

而不是继续反复讨论“到底该把哪些字段打成一个对象”。
