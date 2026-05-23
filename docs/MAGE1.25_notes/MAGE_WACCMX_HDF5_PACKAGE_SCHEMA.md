# MAGE-WACCMX HDF5 Package Schema

## Purpose

这份 schema 描述当前隔离原型输出的前向交换包：
- file: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_forward_package.h5`
- producer: isolated `MAGE/REMIX` stub prototype
- companion replay report: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_replay_report.md`

它的定位不是最终 `CESM` 在线耦合格式，而是：
- 一个稳定的字段合同
- 一个可离线回放的前向字段包
- 一个后续 `mediator/cap` 接线时可直接参照的接口雏形

## File Layout

```text
/
  /Meta
  /NORTH_GRID
  /NORTH_GEO
  /NORTH_APEX
  /SOUTH_GRID
  /SOUTH_GEO
  /SOUTH_APEX
```

## /Meta

`/Meta` 以属性形式保存全局元数据：

| Attribute | Type | Meaning |
| --- | --- | --- |
| `schema_version` | string | 当前 schema 版本，现为 `0.1` |
| `producer` | string | 生成方，现为 `MAGE_WACCMX_STUB` |
| `direction` | string | 交换方向，现为 `MAGE_REMIX_to_future_WACCMX` |
| `grid_source` | string | 网格来源说明，现为 `REMIX_SM_STUB` |
| `source_mix` | string | 输入 `mix.h5` 短文件名 |
| `time_seconds` | float64 | 来自输入 `mix.h5` 的时间 |
| `mjd` | float64 | 来自输入 `mix.h5` 的修改儒略日 |

## Hemisphere Grid Groups

`/NORTH_GRID` 和 `/SOUTH_GRID` 保存原型当前使用的占位网格元数据。

属性：
- `hemisphere`
- `coord = SM`

数据集：
- `theta` `[Nt, Np]` radians
- `phi` `[Nt, Np]` radians
- `theta_deg` `[Nt, Np]` degrees
- `phi_deg` `[Nt, Np]` degrees

注意：
- 这不是最终 `APEX/GEO` mediator 网格
- 当前只是 `REMIX` 原型网格占位

## Forward Field Groups

### /NORTH_GEO and /SOUTH_GEO

属性：
- `coord = GEO`
- `grid_source = REMIX_SM_STUB`

数据集：
- `theta` `[Nt, Np]`, radians
- `phi` `[Nt, Np]`, radians
- `AVG_ENG` `[Nt, Np]`, `keV`
- `NUM_FLUX` `[Nt, Np]`, `1/cm^2 s`

### /NORTH_APEX and /SOUTH_APEX

属性：
- `coord = APEX`
- `grid_source = REMIX_SM_STUB`

数据集：
- `theta` `[Nt, Np]`, radians
- `phi` `[Nt, Np]`, radians
- `POT` `[Nt, Np]`, `kV`
- `NUM_FLUX` `[Nt, Np]`, `1/cm^2 s`

## Current Prototype Interpretation

当前 package 里的字段语义是“对的”，但空间承载仍然是原型级的：
- `AVG_ENG / NUM_FLUX / POT` 已经按未来耦合方向分好腿
- 但网格还没有做真正的 `GEO/APEX -> CESM target grid` regridding

因此它适合做这些事情：
- 离线 replay
- mediator 字段命名讨论
- 单位/维度/方向校验
- 后续 `CESM` 侧 cap stub 开发

它还不适合做这些事情：
- 当成最终科学生产耦合文件
- 直接宣称已经完成 `MAGE -> WACCM-X` 空间坐标一致性

## Recommended Next Use

等真实 `CESM/WACCM-X` 源码接进来后，建议把这个 package 映射成 mediator 字段：
- `/NORTH_GEO/AVG_ENG`, `/SOUTH_GEO/AVG_ENG`
- `/NORTH_GEO/NUM_FLUX`, `/SOUTH_GEO/NUM_FLUX`
- `/NORTH_APEX/POT`, `/SOUTH_APEX/POT`
- `/NORTH_APEX/NUM_FLUX`, `/SOUTH_APEX/NUM_FLUX`

再由 mediator 完成：
- 真正的目标网格重映射
- 时间协调
- 字段注册与单位检查
