# MAGE 与 WACCM-X 真实交换变量速查表

日期：2026-03-28
更新：2026-03-29
复核：2026-03-30

## 一句话结论

当前真实 `MAGE 1.25 <-> WACCM-X(CESM)` 文件桥已经跑通的交换变量是：

- `MAGE -> WACCM-X`: `POT`, `AVG_ENG`, `NUM_FLUX`
- `WACCM-X -> MAGE`: `SIGMAP`, `SIGMAH`

另外，当前还存在一条**实验增强项**：

- `WACCM-X -> MAGE`: `neutral_rhs / NSRHS`

其中前 5 个是当前已完成的正式交换量；`neutral_rhs / NSRHS` 目前仍是**实验增强路径**，不计入当前正式完成变量。更具体地说：

- 当前 live 正式主流程：`mage_waccmx_feedback_rank*.txt` 仍是 5 列 `sigmap/sigmah` 主反馈，bridge 兼容可选第 6 列，但当前实测默认回填 `neutral_rhs=0`
- 独立实验线 `cesm_kaiju_bridge_nsrhs`：`neutral_rhs / NSRHS` 已能通过 sidecar 非零回传并进入 `Kaiju step2`

## 5 个正式交换变量 + 1 个实验增强项

| 方向 | 变量 | 物理含义 | 坐标腿 | 单位 | 文件层握手 | 主要代码入口 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MAGE -> WACCM-X` | `POT` | 高纬电势 | `APEX -> WACCM-X` 磁网格 | `kV` | `mage_waccmx_epot_global.txt` | [kaiju_forward_to_cesm_import.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py), [dpie_coupling.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/dpie_coupling.F90) | 已真实生效 |
| `MAGE -> WACCM-X` | `AVG_ENG` | 极光平均能量 | `GEO` | `keV` | `mage_waccmx_import_rank*.txt` | [kaiju_forward_to_cesm_import.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py), [ionosphere_interface.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90) | 已真实生效 |
| `MAGE -> WACCM-X` | `NUM_FLUX` | 粒子数通量 | `GEO` | `1/cm^2 s` | `mage_waccmx_import_rank*.txt` | [kaiju_forward_to_cesm_import.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py), [ionosphere_interface.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90) | 已真实生效 |
| `WACCM-X -> MAGE` | `SIGMAP` | Pedersen 电导 | `APEX` | `S` | `mage_waccmx_feedback_rank*.txt` -> `feedback_apex_*` | [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90), [waccmx_stub_backend.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/waccmx_stub_backend.F90) | 已真实生效 |
| `WACCM-X -> MAGE` | `SIGMAH` | Hall 电导 | `APEX` | `S` | `mage_waccmx_feedback_rank*.txt` -> `feedback_apex_*` | [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90), [waccmx_stub_backend.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/waccmx_stub_backend.F90) | 已真实生效 |
| `WACCM-X -> MAGE` | `neutral_rhs / NSRHS` | GEO 侧中性动力学代理项 / 显式 dynamo RHS 实验量 | `GEO` | `cm/s` 或实验 `arb` | `正式主线：mage_waccmx_feedback_rank*.txt` 可选第 6 列；实验线：`mage_waccmx_nsrhs_rank*.txt` / `mage_waccmx_nsrhs_geo_rank*.txt` | [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90), [waccmx_stub_backend.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/waccmx_stub_backend.F90), [mixsolver.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/mixsolver.F90) | 实验增强项；当前 live 正式主流程默认未激活 |

## 当前文件格式

### `MAGE -> WACCM-X`

`mage_waccmx_import_rank*.txt`

- 列格式：`cid lat lon avg_eng num_flux`

`mage_waccmx_epot_global.txt`

- 第一行：全局点数
- 后续：展平后的全局 `epot`

### `WACCM-X -> MAGE`

`mage_waccmx_feedback_rank*.txt`

- 当前 live 正式主流程列格式：`cid lat lon sigmap sigmah`
- bridge 兼容可选第 6 列：`neutral_rhs`

`mage_waccmx_nsrhs_rank*.txt` / `mage_waccmx_nsrhs_geo_rank*.txt`

- 仅用于独立 `NSRHS` 实验线

## 当前是否“完全最终版”

就**真实文件桥双向闭环**而言：已经完成。  
就**当前正式完成变量**而言：建议只按前 5 个量表述。  
`neutral_rhs / NSRHS` 目前更适合放在“实验增强项/第二阶段工作”里。

- `POT`, `AVG_ENG`, `NUM_FLUX`, `SIGMAP`, `SIGMAH`
  - 可以按“当前已完成交换量”表述
- `neutral_rhs / NSRHS`
  - 可以按“当前已验证的实验增强回传路径”表述
  - 不建议计入“当前正式完成交换量”
  - 不建议表述成“最终严格定义的 neutral-dynamo RHS”

## 现在最稳妥的对外表述

当前 `MAGE-WACCMX` 真实文件桥已经完成双向闭环。  
当前正式完成交换变量为：

- `POT / AVG_ENG / NUM_FLUX`
- `SIGMAP / SIGMAH`

另外还存在一条已经跑通、但当前仍与正式主流程分开管理的实验增强项：

- `neutral_rhs / NSRHS`

但它当前仍不计入正式完成变量。

## 哪些变量在当前真实链路里最“敏感”

如果只看“当前耦合能不能稳定跑完”，并不是 5 个正式交换量都同等敏感。

当前主导稳定性的变量排序可以概括为：

1. `POT`
2. `AVG_ENG` 与 `NUM_FLUX` 的联合放大
3. `SIGMAP / SIGMAH`
4. `neutral_rhs`

更具体地说：

- `POT` 是当前最敏感的主导变量。
  - 证据：未平滑条件下，`epot x13` 成功，而 `epot x14` 已出现 `CESM rank 3 SIGSEGV`
  - 对应结论：当前失稳首先是由外部电势输入幅值与梯度触发的，不是由反馈电导本身先触发的
- `AVG_ENG` 与 `NUM_FLUX` 单独不是最早失稳源，但与 `POT` 叠加后会明显压缩稳定余量。
  - 证据：未平滑条件下，`all x12` 还能成功，而 `all x16` 已失败
  - 平滑后也是如此：`all x14 smooth2` 成功，而 `all x15 smooth2` 已出现 `te_map: Lagrangian levels are crossing`
- `SIGMAP / SIGMAH` 是当前已经稳定闭环回传的量，但从现有结果看，它们更像是“响应结果”，不是当前第一失稳触发源。
- `neutral_rhs` 目前只是实验增强项和一阶代理量，当前没有证据表明它是主稳定性边界的决定变量。

## 当前实用稳定边界

这些边界不是理论极限，而是**你这套真实环境下、当前文件桥实现下的实测边界**。

### 1. 未平滑条件

- `epot x13`：成功
- `epot x14`：失败
  - 失败签名：`SIGSEGV` on `rank 3`
- `all x12`：成功
- `all x16`：失败
  - 失败签名：`SIGSEGV` on `rank 3`

所以当前未平滑的实用判断是：

- `POT` 单轴阈值大致在 `x13 ~ x14` 之间
- 联合强迫阈值大致在 `all x12 ~ all x16` 之间

### 2. 当前 `smooth2` 条件

当前 bridge 侧已经验证：

- `epot x14 smooth2`：成功
- `epot x14.5 smooth2`：成功
- `epot x15 smooth2`：失败
  - 失败签名：`te_map: Lagrangian levels are crossing`，随后 `MPI_ABORT`
- `all x14 smooth2`：成功
- `all x14.5 smooth2`：成功
- `all x15 smooth2`：失败
  - 失败签名：`te_map: Lagrangian levels are crossing`，随后 `MPI_ABORT`

所以当前 `smooth2` 下的实用判断是：

- `POT` 单轴边界目前已收紧到 `x14.5~x15`
- 联合强迫边界目前已收紧到 `all x14.5~all x15`
- 平滑后首个失稳模式不再只是 `SIGSEGV`，而是先出现更物理/更低层的 `te_map` 层结交叉异常

如果后续对外只按整数倍汇报，不再继续细分中点测试，那么当前最稳妥的整数口径是：

- `smooth2` 下，`epot x14` 成功，`epot x15` 失败
- `smooth2` 下，`all x14` 成功，`all x15` 失败

### 3. 长期 continuation 检查

但这里要和“单轮成功”分开看。

在 `2026-03-28` 的长期闭环检查里，主案例那套真实多周期 continuation 结果是：

- `all x14 + smooth2`：
  seed 成功，但第一个 `CESM` continuation 周期失败
- `epot x14 + smooth2`：
  seed 成功，但第一个 `CESM` continuation 周期失败
- `x1 baseline`：
  seed 成功，但第一个 `CESM` continuation 周期仍失败

三条路径的共同失败签名都是：

- 已经从 `00300` restart 续跑
- 已经开始写 `00600` restart
- 然后在 `med_phases_restart_read` 之后出现 `rank 0 SIGSEGV`

但到 `2026-03-29`，隔离控制又把这个结论继续收紧了：

- 自洽 `edyn off` 的隔离 `startup -> continue` 已成功跑到 `00600`
- 自洽默认 `edyn on` 的隔离 `startup -> continue` 也已成功跑到 `00600`
- 自洽默认 `edyn on` 且带真实 import 文件的隔离 `startup -> continue` 也已成功跑到 `00600`

所以当前“长期稳定性”的首要结论已经不是泛泛的：

- `CESM/WACCM-X` continuation/restart path 全面不稳定

而是更具体的：

- 当前主案例那套 `00300` restart 谱系仍不稳定
- 但 generic continuation 本身已经被隔离控制证明**可以成功**
- bridge import 文件的存在本身也**不足以单独触发失败**

随后同一天又做了 restart transplant matrix，这一步把“当前最敏感的长期 continuation 变量/文件”继续收紧成了**主案例 `cam.r.00300`**：

- 用成功隔离谱系自己的 `00300` restart 做 existing-restart continue：
  成功
- 把主案例失败的整套 `00300` restart 搬到干净隔离目录：
  失败
- 更关键的是混合覆盖结果：
  - 只覆盖主案例 `cam.r.00300`：
    失败
  - 只覆盖主案例 `cam.rs + cam.rh*`：
    成功
  - 只覆盖主案例 `cpl.r.00300`：
    成功

所以当前如果要再往下问“长期 continuation 真正最敏感的是什么”，答案已经不再只是泛泛的：

- `restart path`

而是更具体的：

- **主案例 `cam.r.2005-12-31-00300.nc` 里的状态本身**

并且在 `2026-03-29` 的 `cam.r` 状态比较里，这个“状态本身”又继续被收紧成了更具体的变量类别：

- `U / V / PT`

因为：

- 两个 `cam.r.00300` 的头信息一致，没有 schema 差异
- `U / V / DELP / PT / Q / PS / TEOUT` 这些关键字段里都没有 `NaN/Inf`
- 但主案例失败 `cam.r.00300` 在：
  - `U max`
  - `V min`
  - `PT max`
  这几个动力学主状态极值上，明显大于成功隔离谱系
- 相反：
  - `DELP`
  - `Q`
  - `PS`
  基本与成功谱系一致

所以当前如果要把“长期 continuation 的最敏感量”讲得再落地一点，已经可以说成：

- **单轮强迫稳定性最敏感的是 `POT`**
- **多周期 continuation 当前最敏感的是主案例 `cam.r` 中的动力学主状态，尤其 `U / V / PT`**

但这里还要补一句最新的限制条件：

- 我们已经做了两轮修复型补丁：
  - 只补 `U / V / PT`
  - 再补 `U / V / PT / Optm1 / DTCORE / DUCORE / DVCORE`
- 这两轮都**没有**把 continuation 救活

所以当前最准确的说法是：

- `U / V / PT` 仍然是最显眼、最值得盯的动力学主状态
- 但根因很可能不是这几个变量孤立决定的
- 更像是主案例 `cam.r` 中更大范围的 dycore-related state 组合一致性问题

## 为什么说 `POT` 比 `AVG_ENG/NUM_FLUX` 更敏感

因为当前所有最早出现的失败，都是沿着“电势幅值或其空间梯度”这条轴先发生的：

- 未平滑：
  - `epot x14` 先失败
  - 但 `stress_all_x8` 仍能成功
- 平滑后：
  - 仅靠硬截断 `epot` 并不能解决失败
  - 引入空间平滑后，`epot x14.5` 和 `all x14.5` 都恢复成功

这说明当前影响 `WACCM-X` 稳定性的，不只是 `epot` 绝对值，更重要的是：

- `epot` 的空间梯度
- 由此驱动的电动力学/热层响应陡峭度

## 对外最稳妥表述

如果你要对外讲“当前哪些变量完成了、哪些变量最敏感”，最稳妥的说法是：

- 当前正式完成交换变量仍然是：
  - `POT / AVG_ENG / NUM_FLUX`
  - `SIGMAP / SIGMAH`
- 其中当前主导稳定性边界的首要变量是 `POT`
- `AVG_ENG / NUM_FLUX` 在和 `POT` 联合放大时会进一步压缩稳定余量
- `neutral_rhs` 已经真实接入，但当前仍属于实验增强项，不建议表述成“最终正式交换量”
- 如果讲“长期稳定性”，需要单独补一句：
  当前 blocker 已经收窄到“主案例那套 `00300` restart 谱系”，而不再只是 forcing 强度，也不是 generic continuation 本身
