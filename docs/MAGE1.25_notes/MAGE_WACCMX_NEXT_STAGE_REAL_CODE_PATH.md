# MAGE-WACCMX Next-Stage Real Code Path

Date:
- 2026-03-25

Scope:
- 这份说明只讨论当前已经跑通的**真实文件桥闭环**之后，下一阶段如果要往更稳、更少 sidecar 的方向推进，最应该动哪些真实代码入口。
- 它不讨论 `kaiju_waccmx_proto` 的 stub 原型链。

## 1. 当前真实基线

当前已验证成功的真实链路是：

`real voltron.x -> bridge files -> real cesm.exe -> feedback files/HDF5 -> second real voltron.x`

基线证据：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_REAL_FILE_COUPLING_STATUS.md`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a`

这意味着当前最稳妥的推进方向，不是重写一套新逻辑，而是沿着已经跑通的真实入口，把“文件桥的哪些部分可以继续保留，哪些部分该逐步内收”拆清楚。

## 2. 真实代码入口应该分三层看

### A. MAGE/bridge 前向导出层

这里负责把 `voltron/REMIX` 的前向结果转成 `CESM/WACCM-X` 当前能消费的格式。

关键文件：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`

当前职责：
- 从 `waccmx_voltron_forward_package.h5` 取出 `AVG_ENG / NUM_FLUX / POT`
- 写 rank-local aurora import 文件
- 写全局 `epot` 平面文件

下一阶段最稳妥的增强点：
- 先继续保留这个桥，但把更多元数据写进 import sidecar
- 把当前脚本里的 grid/units 假设显式化
- 先不要直接砍掉这层

### B. CESM/WACCM-X 摄入与反馈层

这里是当前真实运行真正吃输入、吐反馈的核心。

关键文件：
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/cpl/nuopc/atm_import_export.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_ingest_stub.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/dpie_coupling.F90`

当前职责：
- import side 接住 `MAGE` aurora forcing 和 `epot`
- export side 把 `Pedersen/Hall conductance` 写出成 rank feedback 文件

下一阶段最稳妥的增强点：
- 先把 conductance export 的单位、网格和列积分语义固定
- 再把 `epot` flat-file contract 向 grid-aware contract 推进
- 仍然不建议一下子改成在线 MPI

### C. CESM 反馈回写到 MAGE 层

这里负责把 `CESM` rank feedback 文件转成 `Kaiju` 当前能吃的反馈包。

关键文件：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cesm_feedback_to_kaiju_feedback.py`

当前职责：
- 把 `mage_waccmx_feedback_rank*.txt` 转成 `waccmx_cesm_feedback_package.h5`
- 供第二次 `voltron.x` 摄入

下一阶段最稳妥的增强点：
- 继续保留 `SIGMAP / SIGMAH` 主回路
- 再逐步把 `neutral wind / outflow / neutral moments` 的 sidecar 返向量并进这个层

## 3. 真实代码推进顺序

最稳妥的顺序是：

1. 固化当前文件桥合同
- 不改字段语义
- 先把成功的 `POT / AVG_ENG / NUM_FLUX -> SIGMAP / SIGMAH` 合同完全写死

2. 稳定 CESM 侧真实 ingest/export 语义
- 优先稳 `mage_waccmx_ingest_stub.F90`
- 优先稳 `mage_waccmx_feedback_stub.F90`
- 少动 `voltron` 主体

3. 把 flat `epot` contract 往 grid-aware 方向内收
- 这是当前文件桥里最脆弱的一段
- 但已经有成功基线，所以现在应该在“成功基线附近”推进，而不是重起炉灶

4. 再考虑把部分文件桥替换成更紧的接口
- 比如先从文本 sidecar 变成更结构化的单文件包
- 再往 mediator/cap 原生字段交换靠

## 4. 我建议下一阶段优先动的真实文件

优先级 1：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cesm_feedback_to_kaiju_feedback.py`

原因：
- 这是最低风险层
- 可以继续做更激进测试
- 不直接碰 `CESM` 主体

优先级 2：
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_ingest_stub.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/cpl/nuopc/atm_import_export.F90`

原因：
- 这是当前真实耦合最核心的摄入/导出点
- 但改这里已经会直接影响真实 `cesm.exe`

优先级 3：
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/dpie_coupling.F90`

原因：
- 这是电动力学和 `epot` 真正落地的位置
- 也是风险最高的位置

## 5. 不建议现在就做的事

- 不建议立刻把文件桥整体替换成在线 MPI
- 不建议先改 `voltron_mpi.x` 风格架构
- 不建议在没有更多回归测试前，把当前成功的 `fixepot_v3/replay_verify` 基线推翻

## 6. 下一阶段的测试方向

在不改源码的前提下，最值得先做的是：

1. `epot` 幅值压力测试
- 保持当前格式不变
- 只放大 `mage_waccmx_epot_global.txt`

2. aurora forcing 幅值压力测试
- 放大 rank-local `AVG_ENG / NUM_FLUX`

3. 双重放大测试
- 同时放大 `epot + aurora`

4. 负向/退化测试
- 只给 aurora 不给 `epot`
- 只给 `epot` 不给 aurora

这样能先回答：
- 当前真实文件桥的稳定边界在哪
- 哪条腿更脆弱
- 后面应该优先收敛哪段真实接口
