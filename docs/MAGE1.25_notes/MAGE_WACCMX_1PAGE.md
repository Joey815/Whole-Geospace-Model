# MAGE + WACCM-X 一页速查表

适用范围：
- 这页只回答两个问题：
  1. `MAGE + WACCM-X` 公开上是不是在做
  2. 现有 `MAGE + TIEGCM` 的耦合逻辑能不能迁过去

## 1. 一句话结论

- **公开资料已经明确说明 `MAGE + WACCM-X` 在做。**
- **但当前公开发布给社区的 `MAGE` 主线仍然是 `TIEGCM`，不是 `WACCM-X`。**
- **可迁移的是物理闭环，不可直接照搬的是 `TIEGCM` 那套外部 MPI 耦合骨架。**

## 2. 公开证据里最关键的几条

### A. `WACCM-X` 正在开发成 `MAGE` 的交互组件

CEDAR `2025 WACCM-X Tutorial` 直接写到：
- `WACCM-X is currently under development to be an interacting component of the MAGE model`

这条最直接，说明不是猜测。

来源：
- [CEDAR 2025 WACCM-X Tutorial](https://cedarscience.org/workshop/2025-workshop-waccm-x-tutorial)

### B. 官方 slides 已说 `WACCM-X <-> GAMERA` 双向耦合“recently completed”

`2025` 年 CESM/NCAR slides 写到：
- `CGS and HAO have recently completed two-way coupling between WACCM-X and the GAMERA magnetosphere model`
- 同页还写 `Model Framework for CGS MAGE`

这说明：
- 公开口径里，这件事已经不是未来目标
- 但不代表社区已经拿到可跑源码版本

来源：
- [CESM/NCAR 2025 slides](https://www.cesm.ucar.edu/sites/default/files/2025-06/2025cesmpetadellabramberger.pdf)

### C. HAO 官方计划明确说要把 `WACCM-X` 建进 `MAGE`

`HAO Implementation Plan 2025-2030` 写到：
- `building WACCM-X into the MAGE modeling system`
- 同时还写了：
  `field-line based ionospheric dynamo module into WACCM-X`

这说明：
- 不只是“连起来”
- 而是在 `WACCM-X` 电动力学能力上也在往更深层耦合推进

来源：
- [HAO Implementation Plan 2025-2030](https://www2.hao.ucar.edu/sites/default/files/2025-12/HAO-Implementation%20Plan%202025-2030_FINAL1.pdf)

### D. 当前公开 MAGE 主线仍然是 `TIEGCM`

`JHUAPL/kaiju` README 明确写：
- `MAGE 1.25` 包含 `GAMERA + RAIJU + Dragon King + REMIX + TIEGCM`

说明：
- 公开主线不是 `WACCM-X`
- 现在社区真正拿得到、跑得到的是 `TIEGCM` 路线

来源：
- [JHUAPL/kaiju README](https://github.com/JHUAPL/kaiju)

## 3. 现有 `MAGE + TIEGCM` 哪些能迁

### 可以迁的：物理闭环

现有闭环本质是：

```text
MAGE/REMIX -> upper atmosphere model:
  POT / AVG_ENG / NUM_FLUX

upper atmosphere model -> MAGE/REMIX:
  SIGMAP / SIGMAH
```

这个思路对 `WACCM-X` 仍然成立：
- 磁层侧给高纬 forcing
- 上层大气/电离层侧给电导反馈

所以可迁移的是：
- 双向耦合物理结构
- 交换变量的大方向
- `REMIX` 作为电离层解算中枢的角色

### 不可直接迁的：程序级耦合方式

当前 `MAGE + TIEGCM` 是：
- 两个独立程序
- 同一个 `MPI_COMM_WORLD`
- 自定义 communicator
- `send/recv` 直接交换

而 `WACCM-X` 的公开定位是：
- `CESM` 的 atmospheric component
- 跑在 `CESM` 框架里
- 更接近 `CIME + CMEPS/NUOPC` 的 mediator 耦合

所以不能直接照搬的是：
- `mage_coupling.F` 这种外挂 MPI 接口
- `TIEGCM root rank <-> VOLTRON root rank` 这种点对点消息逻辑

## 4. 最稳妥的工程判断

如果你的问题是：

> 能不能按 `MAGE + TIEGCM` 的耦合方式去做 `MAGE + WACCM-X`？

最准确的回答是：

- **能按同样的物理逻辑做**
- **不能按同样的软件架构做**

更像应该这样理解：

- `TIEGCM` 路线：外部程序耦合
- `WACCM-X` 路线：`CESM` 组件耦合

## 5. 建议你下一步怎么做

最现实的路线是：

1. 先固定交换字段
- `MAGE -> WACCM-X`：`POT / AVG_ENG / NUM_FLUX`
- `WACCM-X -> MAGE`：`SIGMAP / SIGMAH`

2. 再决定架构
- 不要先复制 `mage_coupling.F`
- 先确定 `WACCM-X` 在 `CESM/CIME/CMEPS` 里怎么广告 import/export 字段

3. 最后再落实现
- `MAGE` 侧尽量复用已有 `gcm_mpi` / `REMIX` 逻辑
- `WACCM-X` 侧走 `CESM` 组件接口

## 6. 你最应该记住的三句话

- `MAGE + WACCM-X` 公开上已经不是概念，而是在开发中的路线。
- 当前公开可跑的 MAGE 主线还是 `TIEGCM`，不是 `WACCM-X`。
- 你应该复用的是 `MAGE + TIEGCM` 的**耦合物理**，不是它的**MPI 软件骨架**。
