# MAGE + WACCM-X 公开情报汇总与迁移判断

更新时间：
- 2026-03-25

适用范围：
- 这份笔记只总结**公开可见**的信息
- 重点回答两个问题：
  1. 公开资料是否表明 `MAGE + WACCM-X` 正在做，做到什么阶段
  2. 现有 `MAGE + TIEGCM` 的耦合逻辑，哪些可以迁移到 `MAGE + WACCM-X`，哪些不能

## 1. 先给结论

短结论：
- **是的，公开资料明确表明 `MAGE + WACCM-X` 正在推进。**
- 到 `2025` 年公开口径已经不只是“远期目标”，而是：
  - `WACCM-X` 正在开发成 `MAGE` 的交互组件
  - `WACCM-X <-> GAMERA` 的双向耦合已经“recently completed”
- 但**当前公开发布的 MAGE 主线版本仍然是 `TIEGCM` 路线，不是 `WACCM-X` 路线**。

工程结论：
- **物理耦合逻辑可以迁移**
  - `MAGE -> upper atmosphere model`：高纬电势、极光沉降
  - `upper atmosphere model -> MAGE`：电导、可能还有中性风相关电流源
- **软件实现不能照搬**
  - `TIEGCM` 路线是外部程序间的直接 MPI 耦合
  - `WACCM-X` 路线大概率要走 `CESM/CIME/CMEPS/NUOPC` 风格的组件/mediator 耦合

## 2. 公开证据时间线

### 2022-04-13：APL 对 MAGE 的公开表述已经把“lower atmosphere”放进目标

JHU/APL 官方新闻稿写到：
- `MAGE` 要把地磁层、电离层、上层大气，以及“for the first time ... lower atmosphere” 拼到一起

这说明：
- `MAGE` 的公开愿景从一开始就不是只停留在 `TIEGCM`
- 低层大气到上层大气的贯通是公开目标的一部分

来源：
- [JHU/APL 新闻稿，2022-04-13](https://www.jhuapl.edu/news/news-releases/220413-nasa-extends-apl-solar-and-space-physics-drive-center)

### 2023：CESM 官方战略计划把 `WACCM-X <-> GAMERA` 双向耦合写进开发目标

`CESM Science and Strategic Plan 2023-2028` 明确写到：
- 要在 `WACCM-X` 中发展与磁层模型 `GAMERA` 的双向耦合
- 目标是提升 space weather modeling capability

这说明：
- 这不是社区传闻，而是 `CESM` 官方中期计划
- `WACCM-X + GAMERA` 已经进入正式路线图

来源：
- [CESM Science and Strategic Plan 2023-2028](https://www.cesm.ucar.edu/sites/default/files/2023-03/cesm-science-strategic-plan-2023-2028.pdf)

### 2023：NCAR 面向数值预报社区的公开摘要已提到 “coupling with GAMERA”

`UIFCW 2023` 的摘要里，Hanli Liu 直接把下面三项并列为正在进行中的开发：
- 全球高分辨率能力
- MPAS-A 非静力动力核适配
- 与 `GAMERA` 的耦合

这说明：
- 到 `2023` 年，这件事已经不是模糊愿景，而是公开宣讲中的具体开发项

来源：
- [UIFCW 2023 Abstracts](https://epic.noaa.gov/uifcw-2023-abstracts/)

### 2025-02：SIMA/NCAR 已公开介绍新的 field-line dynamo，为磁层耦合做准备

`SIMA Geospace Updates` 公开说明：
- 已为 `WACCM-X` 开发新的 field-line based ionospheric electric dynamo
- 该 dynamo 可通过 electric currents 指定高纬磁层输入
- 文中明确说这使 magnetosphere-ionosphere coupling 更物理一致

这点非常关键，因为它意味着：
- `WACCM-X` 不是简单接收经验高纬电势
- 它在电动力学求解器层面也在为更深的磁层耦合做准备

来源：
- [SIMA Geospace Updates](https://sima.ucar.edu/news/2025/geospace-updates-58)

### 2025：CEDAR 官方 workshop 页面明确说 `WACCM-X` 正在开发成 `MAGE` 的交互组件

CEDAR `2025 Workshop: WACCM-X Tutorial` 页面直接写到：
- `WACCM-X is currently under development to be an interacting component of the MAGE model`

这条信息的价值非常高，因为：
- 它直接把 `WACCM-X` 和 `MAGE` 连在一起
- 不是泛泛讲“whole geospace”，而是明确说交互组件

来源：
- [CEDAR 2025 WACCM-X Tutorial](https://cedarscience.org/workshop/2025-workshop-waccm-x-tutorial)

### 2025-06：CESM/NCAR slides 公开说 `WACCM-X <-> GAMERA` 双向耦合已经完成

`Whole Atmosphere Working Group Overview and Developments` slides 写到：
- `CGS and HAO have recently completed two-way coupling between WACCM-X and the GAMERA magnetosphere model`
- 同页还写了 `WACCM-X/GAMERA: Towards a whole geospace model`
- 并直接标注 `Model Framework for CGS MAGE`

这说明：
- 公开口径里，`WACCM-X/GAMERA` 双向耦合已经不是未来时
- 但“completed”说的是耦合完成，不等于已经公开发布成社区可跑的 `MAGE` 版本

来源：
- [CESM/NCAR 2025 overview slides](https://www.cesm.ucar.edu/sites/default/files/2025-06/2025cesmpetadellabramberger.pdf)
- [CEDAR 2025 WACCM-X Tutorial PDF](https://www2.hao.ucar.edu/sites/default/files/2025-08/WACCMX_Tutorial_CEDAR_2025.pdf)

### 2025-12：HAO 实施计划进一步确认要把 `WACCM-X` 建进 `MAGE`

`HAO Implementation Plan 2025-2030` 里明确写了两件事：
- 正在把 `field-line based ionospheric dynamo module` 并入 `WACCM-X`
- `This includes building WACCM-X into the MAGE modeling system`

这意味着：
- `WACCM-X` 并入 `MAGE` 在 HAO 官方规划里是明确任务
- 而且与数据同化、whole geospace、open-source system 是放在同一个建设语境里

来源：
- [HAO Implementation Plan 2025-2030](https://www2.hao.ucar.edu/sites/default/files/2025-12/HAO-Implementation%20Plan%202025-2030_FINAL1.pdf)

### 2025-12：JHU/APL 公开发布的 MAGE 仍然是 `TIEGCM` 路线

JHU/APL 官方新闻稿写的是：
- `MAGE` pulls together `GAMERA ... and TIEGCM for the upper atmosphere`

同时，JHU/APL 公开仓库 `JHUAPL/kaiju` 的 README 也写明：
- `MAGE 1.25` 当前包括 `GAMERA + RAIJU + Dragon King + REMIX + TIEGCM`
- 没有把 `WACCM-X` 列进当前公开版本

这说明：
- 到 `2025-12`，公开可获得的主线 `MAGE` 仍然不是 `WACCM-X` 版
- 所以“公开在做”和“公开可跑”是两回事

来源：
- [JHU/APL 新闻稿，2025-12-12](https://www.jhuapl.edu/news/news-releases/251212-center-geospace-storms-mage-model)
- [JHUAPL/kaiju README](https://github.com/JHUAPL/kaiju)

## 3. 哪些是“确认事实”，哪些只是“合理推断”

### A. 可以直接确认的事实

- `WACCM-X` 正在开发成 `MAGE` 的交互组件
- `WACCM-X <-> GAMERA` 双向耦合在公开口径里已被称为“recently completed”
- `HAO/NCAR` 正在把新的 field-line dynamo 并入 `WACCM-X`
- 当前公开发布给社区的 `MAGE 1.25` 主线仍是 `TIEGCM`，不是 `WACCM-X`

### B. 我基于公开资料做出的工程推断

- `MAGE + WACCM-X` 的实现路径大概率不会是简单复制 `MAGE + TIEGCM` 的 root-rank MPI send/recv
- 更可能是把 `WACCM-X` 作为 `CESM` 大气/高层大气组件，通过 `CIME/CMEPS/NUOPC` 风格的 mediator/field exchange 去实现
- 原因是 `WACCM-X` 公开定义本身就是 `CESM` 的 atmospheric component，而 `CESM` 当前耦合基础设施是 `CIME + CMEPS`

支持这一推断的公开文档：
- [WACCM-X 是 CESM atmospheric component](https://www.cesm.ucar.edu/models/waccm-x)
- [CIME glossary: driver/coupler](https://esmci.github.io/cime/versions/maint-5.6/html/glossary/index.html)
- [CMEPS 文档首页](https://escomp.github.io/CMEPS/versions/master/html/index.html)
- [CMEPS field exchange 机制](https://escomp.github.io/CMEPS/versions/master/html/esmflds.html)

注意：
- 上面这部分是**工程推断**，不是我已经看到公开源码后下的结论
- 公开网页没有直接给出 `MAGE+WACCM-X` 的 source-level 耦合实现细节

## 4. 对现有 `MAGE + TIEGCM` 的迁移判断

### A. 可以迁移的部分：物理耦合思路

现有 `MAGE + TIEGCM` 的核心闭环是：

```text
MAGE/REMIX -> upper atmosphere model:
  POT / AVG_ENG / NUM_FLUX

upper atmosphere model -> MAGE/REMIX:
  SIGMAP / SIGMAH
```

这套**物理交换思路**对 `WACCM-X` 仍然成立：
- 磁层侧给高纬强迫
- 高层大气/电离层侧给电导与电动力反馈

也就是说，下面这些东西大概率是可以迁移的：
- 交换变量的大方向
- 双向闭环的物理结构
- `REMIX/ionosphere electrodynamics` 在整个闭环里的中枢角色
- 用更自洽的 thermosphere-ionosphere 响应替代经验高纬 forcing 的目标

### B. 半可迁移的部分：网格/坐标处理思想

`MAGE + TIEGCM` 现在已经有：
- GEO / APEX / SM 之间的变换
- 高纬二维场重映射
- 不同模块网格之间的变量转写

这些**思想**可以迁移，但具体实现很可能要重写，因为：
- `WACCM-X` 公开路线里已经强调新 regridding 基础设施
- `SIMA Geospace` 明确提到 geometric / geomagnetic 之间的高效映射基础设施
- `CESM/CMEPS` 本身也有 mediator 侧 field mapping / merging 机制

所以：
- “要做坐标/网格映射”这个问题是一样的
- “怎么做映射”这层实现，不太可能直接复用现在 `kaiju + tiegcm` 的 Fortran MPI 交换代码

来源：
- [SIMA Geospace Applications](https://sima.ucar.edu/applications/geospace)
- [CMEPS exchange 文档](https://escomp.github.io/CMEPS/versions/master/html/esmflds.html)

### C. 很难直接迁移的部分：程序级耦合架构

这个是最关键的不可直接迁移点。

当前 `MAGE + TIEGCM`：
- 是两个外部程序同一个 `MPI_COMM_WORLD`
- 靠自定义 communicator 和直接 `send/recv`
- `VOLTRON/REMIX` 是耦合调度中枢

而 `WACCM-X` 的公开定位是：
- `CESM` atmospheric component
- 配套的是 `CIME` driver/coupler
- `CMEPS` mediator 负责字段广告、映射、合并和交换

因此下面这些不能直接照搬：
- `mage_coupling.F` 式的独立外部 MPI 耦合结构
- `TIEGCM root rank <-> VOLTRON root rank` 这种点对点消息模式
- 现有 `MAGE` 里把高层大气模型当作“外挂子程序”的方式

换句话说：
- **可迁移的是耦合物理**
- **不可直接迁移的是耦合软件骨架**

## 5. 对照表：`MAGE+TIEGCM` 到 `MAGE+WACCM-X`

| 项目 | `MAGE + TIEGCM` | `MAGE + WACCM-X` |
|---|---|---|
| 公开可用程度 | 已公开、代码可得 | 公开表明在做，但未见公开主线版本 |
| 当前公开主线 | 是 | 不是 |
| 上层大气模型角色 | 外部可执行程序 | CESM/WACCM-X 组件 |
| 直接耦合方式 | 自定义 MPI 通信 | 很可能是 CIME/CMEPS/NUOPC 风格 |
| 物理闭环 | 已实现 | 公开口径表明正在实现/部分完成 |
| 高纬 forcing 输入思路 | `POT/AVG_ENG/NUM_FLUX` | 大方向可沿用 |
| 反馈量思路 | `SIGMAP/SIGMAH` | 大方向可沿用 |
| 网格映射 | `kaiju` 侧自定义 | 更可能依赖 CESM/SIMA/CMEPS 基础设施 |
| 对你现有代码可复用性 | 高 | 中等偏低，主要复用物理设计而非代码 |

## 6. 对你下一步工作最有价值的判断

如果你的目标是“照着 `MAGE + TIEGCM` 的套路，把 `MAGE + WACCM-X` 做出来”，那应该这样理解：

- **可以照着做的，是耦合闭环设计**
  - 磁层给 forcing
  - 高层大气返回电导/电动力响应
  - 双向耦合

- **不能照着做的，是程序组织方式**
  - `TIEGCM` 是外部程序式耦合
  - `WACCM-X` 更像 `CESM` 生态中的组件式耦合

对你而言，最现实的技术路线不是：
- “把 `mage_coupling.F` 复制一份给 `WACCM-X`”

而更像是：
- 先定义 `MAGE <-> WACCM-X` 的交换字段和时间步
- 再确定这些字段在 `CESM/CMEPS` 的哪个层面广告、映射、合并和传递
- 最后再考虑 `GAMERA/REMIX/VOLTRON` 这一侧是如何接进去

## 7. 我认为目前还缺的公开信息

以下内容我没有在公开资料中找到：
- 公开的 `MAGE + WACCM-X` 源码分支
- 可运行的 case / job script
- 字段交换表
- 明确写明使用 `CMEPS`、`NUOPC` 还是额外外部耦合接口的技术说明

所以目前最稳妥的判断是：
- **公开证据足以证明这条路线在做，而且进展不低**
- **但公开信息还不足以让人直接复现软件实现**

## 8. 参考链接

- [JHU/APL：NASA extends APL-led CGS, mentions lower atmosphere in MAGE (2022-04-13)](https://www.jhuapl.edu/news/news-releases/220413-nasa-extends-apl-solar-and-space-physics-drive-center)
- [CEDAR 2025 WACCM-X Tutorial：WACCM-X is under development to be an interacting component of MAGE](https://cedarscience.org/workshop/2025-workshop-waccm-x-tutorial)
- [CESM Science and Strategic Plan 2023-2028：two-way coupling with GAMERA in WACCM-X](https://www.cesm.ucar.edu/sites/default/files/2023-03/cesm-science-strategic-plan-2023-2028.pdf)
- [CESM/NCAR 2025 slides：recently completed two-way coupling between WACCM-X and GAMERA](https://www.cesm.ucar.edu/sites/default/files/2025-06/2025cesmpetadellabramberger.pdf)
- [HAO Implementation Plan 2025-2030：building WACCM-X into the MAGE modeling system](https://www2.hao.ucar.edu/sites/default/files/2025-12/HAO-Implementation%20Plan%202025-2030_FINAL1.pdf)
- [SIMA Geospace Applications：coupling with GAMERA + regridding infrastructure](https://sima.ucar.edu/applications/geospace)
- [SIMA Geospace Updates：field-line based dynamo and high-latitude current input](https://sima.ucar.edu/news/2025/geospace-updates-58)
- [CESM WACCM-X page：WACCM-X as CESM atmospheric component](https://www.cesm.ucar.edu/models/waccm-x)
- [CIME glossary：driver/coupler definitions](https://esmci.github.io/cime/versions/maint-5.6/html/glossary/index.html)
- [CMEPS docs：首页](https://escomp.github.io/CMEPS/versions/master/html/index.html)
- [CMEPS docs：field exchange](https://escomp.github.io/CMEPS/versions/master/html/esmflds.html)
- [JHU/APL MAGE public release news (2025-12-12)](https://www.jhuapl.edu/news/news-releases/251212-center-geospace-storms-mage-model)
- [JHUAPL/kaiju README：public MAGE 1.25 still lists TIEGCM, not WACCM-X](https://github.com/JHUAPL/kaiju)
