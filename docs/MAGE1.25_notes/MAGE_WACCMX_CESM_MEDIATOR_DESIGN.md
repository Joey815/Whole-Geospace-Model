# MAGE-WACCMX CESM Mediator Design

## Premise

目标不是把 `WACCM-X` 当成一个像 `TIEGCM` 那样的独立 sidecar 程序挂到 `MAGE` 上，而是把 `MAGE` 这边整理成一个适合接入 `CESM/CIME/CMEPS` 的外部组件接口。

这份设计基于两类约束：
- `MAGE/REMIX` 当前已经明确的字段闭环
- `CESM/WACCM-X` 官方软件架构

官方参考：
- CAM/WACCM-X 作为 CESM 组件运行的说明：<https://docs.cesm.ucar.edu/models/cam/user-guide/6/ug.pdf>
- CIME 架构说明：<https://esmci.github.io/cime/versions/cesm2.2/html/what_cime/index.html>
- CMEPS/mediator 说明：<https://escomp.github.io/CMEPS/versions/master/html/introduction.html>
- CMEPS 字段与中介层说明：<https://escomp.github.io/CMEPS/versions/master/html/esmflds.html>

## Key Conclusion

可以复用的：
- `MAGE <-> TIEGCM` 里的字段闭环
- `REMIX` 上已经存在的 `gcm_T`, `mix2gcm`, `gcm2mix` 抽象
- `POT / AVG_ENG / NUM_FLUX <-> SIGMAP / SIGMAH` 这一套基本耦合变量

不能直接复用的：
- `voltron_mpi.x` 与 `tiegcm.x` 这种同一 `MPI_COMM_WORLD` 下的点对点交换模式
- 依赖 root-rank send/recv 的启动方式
- 假设对方是一个独立轻量可执行文件的实现前提

## Recommended Architecture

推荐把未来实现拆成三层：

1. `MAGE external component`
- 责任：把 `MAGE/REMIX` 侧字段整理成 mediator 可消费的 state
- 输出：`POT`, `AVG_ENG`, `NUM_FLUX`
- 输入：`SIGMAP`, `SIGMAH`

2. `CMEPS mediator`
- 责任：字段注册、时间协调、重网格、单位检查
- 不建议把物理转换逻辑塞回 `MAGE` 或 `WACCM-X` 主体

3. `WACCM-X/CAM cap`
- 责任：把 mediator 下发的高纬驱动落到 `WACCM-X` 内部需要的场
- 再把电导或扩展电动力反馈整理回 mediator

## Proposed Field Advertisement

建议在 mediator 层显式区分两条前向腿：

| Producer | Consumer | Coord | Field | Units | Why split this way |
| --- | --- | --- | --- | --- | --- |
| `MAGE/REMIX` | `WACCM-X` | `APEX` | `POT` | `kV` | 高纬电势天然更适合磁坐标腿 |
| `MAGE/REMIX` | `WACCM-X` | `APEX` | `NUM_FLUX` | `1/cm^2 s` | 可服务于极光边界或磁坐标侧过滤 |
| `MAGE/REMIX` | `WACCM-X` | `GEO` | `AVG_ENG` | `keV` | 最终热层/电离层沉降更贴近地理网格应用 |
| `MAGE/REMIX` | `WACCM-X` | `GEO` | `NUM_FLUX` | `1/cm^2 s` | 与 `AVG_ENG` 成对进入沉降加热 |
| `WACCM-X` | `MAGE/REMIX` | `APEX` | `SIGMAP` | `S` | 回写 Pedersen conductance |
| `WACCM-X` | `MAGE/REMIX` | `APEX` | `SIGMAH` | `S` | 回写 Hall conductance |

建议的 mediator 内部命名可以先保持保守：
- `mage_pot_apex`
- `mage_num_flux_apex`
- `mage_avg_eng_geo`
- `mage_num_flux_geo`
- `waccmx_sigmap_apex`
- `waccmx_sigmah_apex`

## Time Coordination

建议耦合 cadence 采用分层策略：
- 第一阶段：`300 s`
- 第二阶段：`60-120 s`
- 只有在数值稳定并且 mediator/regridding 成本可接受时，再压到 `MAGE-TIEGCM` 类似的更快步长

理由很简单：
- `WACCM-X/CESM` 的组件调度比当前 `MAGE-TIEGCM` sidecar 结构更重
- 第一版应先把字段语义和重网格闭环跑通，再追求高频耦合

## Grid Strategy

推荐不要让 `WACCM-X` 直接理解 `MAGE` 的内部 `REMIX` 网格。

更稳妥的路线：
- `MAGE` 输出两套显式字段包：
  - `APEX` package
  - `GEO` package
- mediator 负责重网格到 `WACCM-X` 目标网格
- 回写电导时同样由 mediator 把 `WACCM-X` 电导重映射回 `MAGE/REMIX` 需要的 `APEX` 网格

这样做的优点：
- `MAGE` 不需要知道 `CESM` case 的内部网格细节
- `WACCM-X` 不需要知道 `REMIX` 的实现细节
- 网格变化主要留在 mediator 权重与 field table 层解决

## Suggested Build Path

### Phase 0

已经完成的本地隔离验证：
- `WACCMX_STUB -> REMIX`
- `MAGE/REMIX -> future WACCM-X` 导出骨架

位置：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto`

### Phase 1

离线 one-way replay
- `MAGE` 先生成 `POT / AVG_ENG / NUM_FLUX` 时间序列
- 由一个 CESM data-like component 或 stub component 重放给 mediator
- 目标是先验证 `WACCM-X` 吃场是否合理

### Phase 2

在线 one-way coupling
- 给 `MAGE` 包一层 CESM external component/cap
- 每个耦合步向 mediator 发布四个前向字段
- `WACCM-X` 先只消费，不回写

### Phase 3

在线 two-way coupling
- `WACCM-X` 向 mediator 回写 `SIGMAP/SIGMAH`
- mediator 将其送回 `MAGE`
- `REMIX` 用更新电导重解电势并反馈磁层

## Concrete Implementation Tasks

在拿到真实 `CESM/WACCM-X` 源码后，优先做下面这些事情：

1. 定义 mediator 字段表
- 先只放 `POT / AVG_ENG / NUM_FLUX / SIGMAP / SIGMAH`

2. 做一个最小 `MAGE` cap
- 不要求一开始就在线耦合
- 先实现 state 打包、单位标记、时间戳、网格元数据

3. 做最小重网格链
- `APEX -> WACCM-X`
- `GEO -> WACCM-X`
- `WACCM-X -> APEX`

4. 做单向 case
- 只测 `MAGE -> WACCM-X`

5. 再做闭环 case
- `MAGE -> WACCM-X -> MAGE`

## Current Limitation

本地还没有真实 `/home/jiaoy_group/jiaoy/data/CESM` 源码树，因此这份文档现在是：
- 架构级设计
- 字段级设计
- 分阶段落地路线

还不是：
- 对具体 CESM 文件路径的补丁说明
- 对具体 cap 源文件的逐行修改说明

## Bottom Line

最稳妥的路线不是“把 `WACCM-X` 改成另一个 `tiegcm.x`”，而是：
- 复用 `MAGE-TIEGCM` 的字段闭环
- 保留 `MAGE` 侧的 `gcm_T / mix2gcm / gcm2mix` 抽象
- 在 `CESM` 侧按 `CIME/CMEPS/mediator` 规范接入 `WACCM-X`
