# MAGE + WACCM-X 技术方案草案

状态：
- Draft v0.1
- 日期：2026-03-25

适用范围：
- 这是一个**设计草案**
- 它基于：
  - 当前公开的 `MAGE 1.25 + TIEGCM` 实现
  - 当前公开的 `WACCM-X / CESM / CIME / CMEPS` 文档
  - 已公开的 `WACCM-X <-> GAMERA` / `WACCM-X into MAGE` 进展信息
- 它**不是**基于本地 `CESM` 源码审阅后的实施方案

限制条件：
- 当前工作区 [CESM](/home/jiaoy_group/jiaoy/data/CESM) 为空目录
- 所以下面的 `WACCM-X/CESM` 侧实现点属于**工程建议**，不是源码定位后的确定结论

## 1. 设计目标

目标不是简单替换 `TIEGCM` 名字，而是实现下面这个双向闭环：

```text
GAMERA / RAIJU / REMIX -> WACCM-X
WACCM-X -> REMIX / VOLTRON -> GAMERA / RAIJU
```

更具体地说：
- `MAGE` 向 `WACCM-X` 提供高纬磁层 forcing
- `WACCM-X` 返回更自洽的电离层/热层响应
- `REMIX` 继续作为电离层 electrodynamics 解算中枢

## 2. 当前 `MAGE + TIEGCM` 可作为什么基线

现有实现中，核心双向变量是：

`REMIX -> TIEGCM`
- `POT`
- `AVG_ENG`
- `NUM_FLUX`

`TIEGCM -> REMIX`
- `SIGMAP`
- `SIGMAH`

相关本地实现：
- [mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F)
- [advance.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/advance.F)
- [gcm_mpi.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/voltron/mpi/gcm_mpi.F90)
- [tgcm.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/tgcm.F90)
- [mixconductance.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/mixconductance.F90)

因此，对 `WACCM-X` 而言，最合理的第一版目标不是重新定义一整套新物理接口，而是先复用这组高层接口。

## 3. 推荐总体架构

### A. 不推荐的路线

不推荐直接复制 `TIEGCM` 的做法：
- 新造一个 `waccmx_coupling.F`
- 用 `MPI_Comm_split` 把 `WACCM-X` 当作外挂程序
- 让 `VOLTRON` 和 `WACCM-X` root rank 直接 `send/recv`

原因：
- `WACCM-X` 公开定位是 `CESM` atmospheric component
- `CESM` 公开基础设施是 `CIME` driver 和 `CMEPS` mediator
- 强行外挂会和 `CESM` 原生运行方式冲突，维护成本很高

参考：
- [WACCM-X as CESM model component](https://www.cesm.ucar.edu/models/waccm-x)
- [CIME: single-executable coupled architecture / hub-and-spoke](https://esmci.github.io/cime/versions/cesm2.2/html/what_cime/index.html)
- [CMEPS: NUOPC mediator used in CESM](https://escomp.github.io/CMEPS/versions/master/html/index.html)

### B. 推荐路线

推荐架构是：

```text
MAGE side:
  GAMERA / RAIJU / REMIX / VOLTRON

CESM side:
  WACCM-X component + CIME/CMEPS mediator/cap layer

Coupling concept:
  exchange high-latitude geospace fields through CESM-compatible import/export states
```

翻成工程动作，就是：
- `MAGE` 侧保留现有 `REMIX` 为离子层中枢的思路
- `WACCM-X` 侧不要当外挂程序，而应当作为 `CESM` 组件参加字段交换
- 耦合字段由 mediator/cap 广告、映射和合并

## 4. 第一版建议交换字段

### A. `MAGE -> WACCM-X`

第一版建议直接复用现有 `TIEGCM` 接口：

1. `POT`
- 高纬电势
- 优先 APEX / geomagnetic 表达

2. `AVG_ENG`
- 极光平均能量
- GEO 或 WACCM-X 接受的地理高纬网格表达

3. `NUM_FLUX`
- 粒子数通量

这些字段在现有 `MAGE` 里已成熟：
- [gcm_mpi.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/voltron/mpi/gcm_mpi.F90)
- [tgcm.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/tgcm.F90)

### B. `WACCM-X -> MAGE`

第一版建议同样复用现有反馈量：

1. `SIGMAP`
- Pedersen conductance

2. `SIGMAH`
- Hall conductance

第二阶段再考虑可选增强字段：

3. `NEUTRAL_WIND_DYNAMO_CURRENT` 或等价量
- 如果 `WACCM-X` 侧 field-line dynamo 提供了更直接的电流闭合量，可考虑加入

4. 动态 auroral boundary / FAC closure diagnostics
- 仅在第一版闭环跑通后再扩展

## 5. `REMIX` 在新架构里的角色

建议保留 `REMIX` 作为中枢，而不是把它绕开。

原因：
- 现有 `MAGE` 里，`REMIX` 已经是磁层、电离层、电导的汇合点
- `GAMERA -> REMIX`
- `RAIJU -> REMIX`
- `TIEGCM -> REMIX`

如果切到 `WACCM-X`，最稳妥的思路仍是：
- `GAMERA`、`RAIJU` 继续先喂给 `REMIX`
- `WACCM-X` 提供电导和高层响应给 `REMIX`
- `REMIX` 继续解电势并反馈到 `VOLTRON/GAMERA/RAIJU`

也就是说：
- **建议替换的是 T/I 模型**
- **不建议第一阶段就替换 REMIX 的中枢角色**

## 6. 时间步与同步策略

### A. 当前基线

现有 `MAGE + TIEGCM` 常见耦合步是 `5 s` 量级。

### B. 对 `WACCM-X` 的建议

不建议一上来就要求 `WACCM-X` 和现有 `TIEGCM` 一样 `5 s` 双向耦合。

更现实的分阶段策略：

第一阶段：
- `30 s` 或 `60 s` 双向耦合
- `MAGE` 在中间小步内保持最近一次 `WACCM-X` 反馈场

第二阶段：
- 评估是否能下探到 `10 s`

第三阶段：
- 再讨论是否需要 `5 s`

原因：
- `WACCM-X` 是 whole atmosphere component，数值代价明显高于 `TIEGCM` 这种专门的 IT 模型
- 公开资料虽表明已完成双向耦合，但未公开说明最终 operational coupling cadence

## 7. 网格与坐标建议

这是最容易低估的难点。

### A. `MAGE` 当前习惯

现有 `MAGE + TIEGCM` 已经处理：
- GEO
- APEX / geomagnetic
- SM

### B. `WACCM-X` 的新问题

`WACCM-X/CESM` 路线下，很可能涉及：
- 原生大气格点
- 高纬磁坐标表示
- `CMEPS/ESMF` 侧重映射
- `SIMA` 提到的 geometric / geomagnetic regridding infrastructure

来源：
- [SIMA Geospace Applications](https://sima.ucar.edu/applications/geospace)
- [CMEPS mapping and exchange docs](https://escomp.github.io/CMEPS/versions/master/html/esmflds.html)

### C. 第一版建议

建议不要一开始就追求“任意坐标都原生交换”，而是先规定：

`MAGE -> WACCM-X`
- 电势：磁坐标高纬网格
- 沉降：地理高纬网格或 `WACCM-X` 当前最容易吸收的高纬二维场

`WACCM-X -> MAGE`
- 电导：高纬磁坐标网格

也就是说：
- 第一版优先选择**最接近现有 `TIEGCM` 接口**的字段表达
- 先让闭环跑通，再优化高阶坐标一致性

## 8. 推荐的软件分层

### A. MAGE 侧

建议新增一个抽象层，而不是把 `TIEGCM` 逻辑硬编码成唯一 `gcm`。

建议目标：

```text
GCM backend abstraction
  - tiegcm_backend
  - waccmx_backend
```

MAGE 侧可复用的地方：
- `gcm_mpi.F90` 的字段组织思想
- `gcminterp` 的导入/导出数组逻辑
- `REMIX` 中 `apply_gcm2mix` 的使用方式

要改的地方：
- 当前实现默认对端是 `TIEGCM`，字段尺寸和初始化握手也偏 `TIEGCM`
- 需要把 “GCM backend capability” 抽象出来

### B. CESM/WACCM-X 侧

建议把 `WACCM-X` 侧耦合拆成三层：

1. `WACCM-X physics interface`
- 把高纬 forcing 接到电势 / aurora / electrodynamics 入口
- 把电导诊断导出来

2. `WACCM-X cap / import-export state layer`
- 负责把模型变量挂到 `ESMF/NUOPC` 状态上

3. `CMEPS mediator field table`
- 负责字段广告、字段名映射、mapping、merge、时间平均

这也是为什么：
- 你不能直接把 `mage_coupling.F` 复制过去
- 因为 `WACCM-X` 这边应该接的是 mediator 生态，不是裸 MPI

## 9. 分阶段实施路线

### Phase 0：接口冻结

目标：
- 先冻结第一版交换量

建议字段：
- `POT`
- `AVG_ENG`
- `NUM_FLUX`
- `SIGMAP`
- `SIGMAH`

交付物：
- 字段表
- 单位表
- 坐标表
- 时间步表

### Phase 1：离线回放验证

目标：
- 不做在线双向耦合
- 先把 `MAGE` 输出回放进 `WACCM-X`

做法：
- 用某个 storm case 的 `MAGE/REMIX` forcing
- 在 `WACCM-X` 侧离线读取并驱动
- 验证高纬电势、沉降、电导响应是否合理

意义：
- 先把“物理接口”从“框架接口”里分离出来

### Phase 2：单向在线耦合

目标：
- `MAGE -> WACCM-X`
- 暂不把 `WACCM-X` 电导回馈给 `MAGE`

意义：
- 先打通 mediator/import-export/重网格链路

### Phase 3：双向 conductance feedback

目标：
- `WACCM-X -> REMIX` 回 `SIGMAP / SIGMAH`
- `REMIX` 使用该电导重解电势

意义：
- 这是第一阶段真正意义上的 “MAGE + WACCM-X” 双向闭环

### Phase 4：扩展字段

可选扩展：
- 中性风 dynamo 电流
- 更高频耦合
- 更细坐标一致性
- 与 `RAIJU` 更紧密的沉降反馈

## 10. 风险清单

### 风险 1：把“公开已完成双向耦合”误解为“社区已有可跑主线”

风险说明：
- 公开 slides 说 completed
- 但公开 `kaiju` 主线仍是 `TIEGCM`

工程含义：
- 不能假定社区仓库里已经有现成可复制实现

### 风险 2：低估 `CESM` 框架改造成本

风险说明：
- `WACCM-X` 不是独立小程序
- 是 `CESM` 组件

工程含义：
- mediator/cap/state advertisement 这层工作量可能不小于物理耦合本身

### 风险 3：时间步要求过激

风险说明：
- 如果一开始就要求 `5 s` 双向闭环，工程上可能过重

建议：
- 从 `30-60 s` 起步

### 风险 4：坐标与网格映射复杂度高

风险说明：
- `MAGE` 侧已有 GEO/APEX/SM
- `WACCM-X`/`CESM` 侧还有自身网格与 mediator mapping

建议：
- 第一版先简化字段表达

## 11. 我对“能不能做”的技术判断

我的判断是：

- **可以做**
- 但应理解为“按相同物理逻辑重构到 `WACCM-X/CESM` 生态里”
- 不应理解为“把 `TIEGCM` 的 MPI 耦合代码改改名字就能跑”

更具体地说：

- 如果目标是科研原型：可行
- 如果目标是短时间内复刻 `MAGE + TIEGCM` 的成熟度：难度明显更高
- 如果目标是长期社区化方案：`WACCM-X` 路线在框架层面其实更正规

## 12. 建议的下一步产物

如果继续往下做，我建议接着产出三样东西：

1. `字段接口表`
- 每个字段的名字、单位、坐标、方向、cadence

2. `MAGE 侧改造点列表`
- 哪些文件要抽象成 backend-neutral

3. `CESM/WACCM-X 侧接入点清单`
- import/export state
- cap 层
- mediator field dictionary

## 13. 参考资料

- [CEDAR 2025 WACCM-X Tutorial](https://cedarscience.org/workshop/2025-workshop-waccm-x-tutorial)
- [CESM/NCAR 2025 slides](https://www.cesm.ucar.edu/sites/default/files/2025-06/2025cesmpetadellabramberger.pdf)
- [HAO Implementation Plan 2025-2030](https://www2.hao.ucar.edu/sites/default/files/2025-12/HAO-Implementation%20Plan%202025-2030_FINAL1.pdf)
- [CESM Science and Strategic Plan 2023-2028](https://www.cesm.ucar.edu/sites/default/files/2023-03/cesm-science-strategic-plan-2023-2028.pdf)
- [WACCM-X model page](https://www.cesm.ucar.edu/models/waccm-x)
- [CIME overview](https://esmci.github.io/cime/versions/cesm2.2/html/what_cime/index.html)
- [CIME driver/coupler docs](https://esmci.github.io/cime/versions/maint-5.6/html/driver_cpl/index.html)
- [CMEPS introduction](https://escomp.github.io/CMEPS/versions/master/html/introduction.html)
- [CMEPS exchange of fields](https://escomp.github.io/CMEPS/versions/master/html/esmflds.html)
- [JHUAPL/kaiju README](https://github.com/JHUAPL/kaiju)

## 14. 本地相关实现参考

现有 `MAGE + TIEGCM` 代码基线：
- [gcm_mpi.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/voltron/mpi/gcm_mpi.F90)
- [tgcm.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/tgcm.F90)
- [mixconductance.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/mixconductance.F90)
- [mhd2mix_interface.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/voltron/modelInterfaces/mhd2mix_interface.F90)
- [mix2mhd_interface.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/voltron/modelInterfaces/mix2mhd_interface.F90)
- [imag2mix_interface.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/voltron/modelInterfaces/imag2mix_interface.F90)
- [mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F)
- [advance.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/advance.F)
