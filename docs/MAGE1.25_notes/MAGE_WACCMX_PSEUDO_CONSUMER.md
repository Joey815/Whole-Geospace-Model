# MAGE-WACCMX Pseudo Consumer

## What it is

这是一个隔离原型里的“伪 `WACCM-X` 消费端”。

它不是真正的 `CAM/WACCM-X` 组件，也不接 `CIME/CMEPS`，但它做了一件现在很有价值的事：
- 把 `MAGE/REMIX` 输出的前向 `HDF5` 包
- 重组为更像上层大气模式侧会消费的对象

对应实现位置：
- code root: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto`
- module: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/remix/waccmx_stub_consumer.F90`
- driver: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/drivers/waccmx_stub_consumerx.F90`

## Why this step matters

在真正接 `CESM/WACCM-X` 之前，最容易返工的不是字段名字，而是消费端语义：
- 哪些字段属于极光沉降输入
- 哪些字段属于电动力输入
- 半球怎么拆
- `GEO/APEX` 两条腿怎么分
- 未来 mediator 名称应该长什么样

这个 pseudo consumer 的作用，就是把这些问题先提前暴露出来。

## Current Consumer Object

当前 consumer 在概念上拆成两类对象：

### Aurora Inputs

每个半球一份：
- `AVG_ENG`
- `NUM_FLUX`
- `coord = GEO`

它对应未来 `WACCM-X` 侧的极光沉降/加热输入。

### Electrodynamics Inputs

每个半球一份：
- `POT`
- `NUM_FLUX`
- `coord = APEX`

它对应未来 `WACCM-X` 侧的高纬电势和相关边界输入。

## Current Output

当前 consumer 运行后会生成：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_consumer_report.md`

这份报告里包含：
- `Aurora Inputs`
- `Electrodynamics Inputs`
- 每个对象的 `coord/grid_source/grid`
- 均值或 `CPCP`
- 一层 mediator 风格 alias

## Alias Mapping

当前 consumer 会给出一组保守的 alias，用来模拟未来 mediator 字段命名：

| Native field | Consumer alias example |
| --- | --- |
| `AVG_ENG` on `NORTH_GEO` | `mage_avg_eng_geo_north` |
| `NUM_FLUX` on `NORTH_GEO` | `mage_num_flux_geo_north` |
| `POT` on `NORTH_APEX` | `mage_pot_apex_north` |
| `NUM_FLUX` on `NORTH_APEX` | `mage_num_flux_apex_north` |

南半球同理。

## Current Limitation

这个 consumer 现在仍然是原型级：
- 它读取的是 `REMIX_SM_STUB` 网格承载的前向包
- 不是 `CESM` 真正的目标网格
- 也还没有真正的 regridding

所以它现在解决的是：
- 消费端对象建模
- 接口语义建模
- 命名与分组建模

还没有解决的是：
- `CMEPS mediator` 的真实字段注册
- `WACCM-X` 真网格映射
- 真正的 `CAM`/`WACCM-X` 时间步接入

## Why this is still useful

因为到你真正拿到 `CESM/WACCM-X` 源码时，这些事情就已经收敛了：
- forward package 结构
- consumer 侧对象拆分
- 基本字段 alias
- 最低限度的消费端检查逻辑

这样后面的真实接线工作，就能更专注在：
- cap/mediator 插点
- regridding
- runtime orchestration
