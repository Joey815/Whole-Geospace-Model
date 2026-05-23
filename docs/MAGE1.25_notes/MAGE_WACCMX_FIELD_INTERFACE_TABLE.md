# MAGE-WACCMX Field Interface Table

## Scope

这份表把 `MAGE/REMIX <-> future WACCM-X` 的接口拆成两部分：
- 物理上需要交换的字段
- 当前隔离原型里已经落到代码里的骨架

当前原型位置：
- code: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto`
- runtime outputs: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp`

## Interface Table

| Direction | Coord | Field | Units | Current kaiju source/target | Current prototype status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `MAGE/REMIX -> future WACCM-X` | `APEX` | `POT` | `kV` | `I(h)%St%Vars(:,:,POT)` | exported in stub skeleton | high-latitude electric potential |
| `MAGE/REMIX -> future WACCM-X` | `APEX` | `NUM_FLUX` | `1/cm^2 s` | `I(h)%St%Vars(:,:,NUM_FLUX)` | exported in stub skeleton | useful for auroral boundary or precipitation mask |
| `MAGE/REMIX -> future WACCM-X` | `GEO` | `AVG_ENG` | `keV` | `I(h)%St%Vars(:,:,AVG_ENG)` | exported in stub skeleton | auroral mean energy |
| `MAGE/REMIX -> future WACCM-X` | `GEO` | `NUM_FLUX` | `1/cm^2 s` | `I(h)%St%Vars(:,:,NUM_FLUX)` | exported in stub skeleton | paired with `AVG_ENG` for precipitation forcing |
| `future WACCM-X -> MAGE/REMIX` | `APEX` | `SIGMAP` | `S` | `gcm%APEX%mixInput(:,:,SIGMAP)` | already implemented in stub import | Pedersen conductance |
| `future WACCM-X -> MAGE/REMIX` | `APEX` | `SIGMAH` | `S` | `gcm%APEX%mixInput(:,:,SIGMAH)` | already implemented in stub import | Hall conductance |
| `future WACCM-X -> MAGE/REMIX` | `GEO/APEX` | `NEUTRAL_WIND` | model-dependent | not yet wired | design only | optional later dynamo closure |

## Code Mapping

当前隔离原型里对应的代码位置：
- `WACCMX_STUB -> REMIX` 导入骨架：`src/remix/waccmx_stub_backend.F90`
- `MAGE/REMIX -> future WACCM-X` 导出骨架：`src/remix/waccmx_stub_backend.F90`
- standalone driver: `src/drivers/waccmx_stub_remixx.F90`
- HDF5 package schema: `/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_HDF5_PACKAGE_SCHEMA.md`

导出骨架的具体实现方式：
- `gcm%GEO%outlist = [AVG_ENG, NUM_FLUX]`
- `gcm%APEX%outlist = [POT, NUM_FLUX]`
- `capture_waccmx_stub_exports(...)` 把 `REMIX` 解算后的字段拷贝到 `gcm%GEO%gcmOutput` 和 `gcm%APEX%gcmOutput`
- `write_waccmx_stub_exchange(...)` 把这套前向字段写成一个可检查的 Markdown 摘要
- `write_waccmx_stub_package(...)` 把这套前向字段和网格元数据写成一个 HDF5 交换包

## Prototype Outputs

当前原型运行后会留下两份最重要的检查文件：
- conductance return summary: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_contract.txt`
- forward exchange summary: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_exchange.md`
- forward HDF5 package: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_forward_package.h5`
- replay reader report: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_replay_report.md`

## Interpretation

这张表的工程含义是：
- `TIEGCM` 路线里真正值得复用的是字段闭环
- `WACCM-X` 路线里应尽量保持同一套字段语义
- 但软件承载层应改成 `CESM/CIME/CMEPS` 风格的 component/mediator exchange，而不是复制 `voltron_mpi.x <-> tiegcm.x` 的直接消息交换
