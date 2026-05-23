# MAGE 与 WACCM-X 当前真实握手字段表

日期：2026-03-26
更新：2026-03-30

## 1. 一句话结论

当前这条真实 `MAGE 1.25 <-> WACCM-X(CESM)` 文件桥里，当前**正式完成并建议对外表述**的字段是：

- `MAGE -> WACCM-X`: `POT`, `AVG_ENG`, `NUM_FLUX`
- `WACCM-X -> MAGE`: `SIGMAP`, `SIGMAH`

另外，当前还存在一条已经技术跑通、但**与当前 live 正式主流程分开管理**的实验增强项：

- `neutral_rhs`

其中 `neutral_rhs` 当前要分成两种状态看：

- 当前 live 正式主流程：
  `mage_waccmx_feedback_rank*.txt` 仍是 5 列 `sigmap/sigmah` 主反馈；bridge 解析器会兼容可选第 6 列，但当前实测 run 默认回填为 `0`
- 独立实验线 `cesm_kaiju_bridge_nsrhs`：
  `neutral_rhs/NSRHS` 已经可以通过 sidecar 非零回传并进入 `Kaiju step2`

也就是说，当前代码里确实已经存在一个**一阶真实代理量**定义：

- `CESM` 侧定义：Pedersen 电导加权的纬向中性风
- 桥内单位：`cm/s`
- `Kaiju` 侧映射：`GEO neutral_rhs -> NEUTRAL_WIND slot`

但它还不是最终定稿的 neutral-dynamo 物理闭合，只能表述为“真实代理回传”，不能表述为“最终物理量完全完成”。

## 2. 当前真实生效的握手字段

| 方向 | 物理量 | 当前文件/对象 | 当前列格式或 group | 坐标腿 | 单位 | 在对方中的用途 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MAGE -> WACCM-X` | `AVG_ENG` | `mage_waccmx_import_rank*.txt` | `cid lat lon avg_eng num_flux` | `GEO` | `keV` | 极光平均能量，进入 `prescr_kev` | 已真实生效 |
| `MAGE -> WACCM-X` | `NUM_FLUX` | `mage_waccmx_import_rank*.txt` | `cid lat lon avg_eng num_flux` | `GEO` | `1/cm^2 s` | 与 `AVG_ENG` 一起形成极光能量通量 | 已真实生效 |
| `MAGE -> WACCM-X` | `POT` | `mage_waccmx_epot_global.txt` | 首行为点数，后面为展平后的全局电势数组 | `APEX -> WACCM-X 磁网格` | `kV` | 外部高纬电势，送入 `d_pie_set_external_epot(...)` | 已真实生效 |
| `WACCM-X -> MAGE` | `SIGMAP` | `mage_waccmx_feedback_rank*.txt` -> `feedback_apex_*` | `cid lat lon sigmap sigmah` | `APEX` | `S` | 回写 `REMIX` Pedersen conductance | 已真实生效 |
| `WACCM-X -> MAGE` | `SIGMAH` | `mage_waccmx_feedback_rank*.txt` -> `feedback_apex_*` | `cid lat lon sigmap sigmah` | `APEX` | `S` | 回写 `REMIX` Hall conductance | 已真实生效 |
| `WACCM-X -> MAGE` | `neutral_rhs` | `正式主线：feedback main file 可选第 6 列；实验线：nsrhs sidecar -> feedback_geo_*` | `正式主线默认无第 6 列；实验线独立 sidecar` | `GEO` | `cm/s` 或实验 `arb` | 作为 GEO 侧中性动力学代理项写入 `NEUTRAL_WIND` 或显式 `NSRHS` 槽位 | 实验线已技术跑通；当前 live 正式主流程默认未激活 |

## 3. 文件层握手格式

### 3.1 `MAGE -> WACCM-X`

真实桥接入口：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py`

它从 `voltron` 写出的前向包中读取：

- `/NORTH_GEO/AVG_ENG`
- `/NORTH_GEO/NUM_FLUX`
- `/SOUTH_GEO/AVG_ENG`
- `/SOUTH_GEO/NUM_FLUX`
- `/NORTH_APEX/POT`
- `/SOUTH_APEX/POT`

然后生成两类 `CESM` 可读输入：

1. rank 局部极光文件  
   示例：
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/with_import_inputs/mage_waccmx_import_rank000000.txt`

   第一行：
   - 本 rank 本地列数

   后续每行：
   - `cid`
   - `lat`
   - `lon`
   - `avg_eng`
   - `num_flux`

2. 全局电势文件  
   示例：
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/with_import_inputs/mage_waccmx_epot_global.txt`

   第一行：
   - 全局点数

   后续每行：
   - 一个展平后的 `epot` 数值

### 3.2 `WACCM-X -> MAGE`

真实桥接入口：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cesm_feedback_to_kaiju_feedback.py`

`CESM/WACCM-X` 先写每个 rank 的反馈文件：

- `mage_waccmx_feedback_rank000000.txt`
- `mage_waccmx_feedback_rank000001.txt`
- ...

示例：
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs/replay_verify_20260325a/with_import_feedback/mage_waccmx_feedback_rank000000.txt`

第一行：
- 本 rank 本地列数

后续每行在当前 live 正式主流程里是：
- `cid`
- `lat`
- `lon`
- `sigmap`
- `sigmah`

bridge 解析器兼容可选第 6 列：
- `neutral_rhs`

但当前 `2026-03-30` live 三轮 run 的实际 `mage_waccmx_feedback_rank*.txt` 仍然只有 5 列；因此 formal 主线里的 `feedback_geo_*/neutral_rhs` 当前默认是 bridge 回填的零场。

桥接脚本把它们重映射回 `kaiju` 反馈包中的：

- `/feedback_apex_north/sigmap`
- `/feedback_apex_north/sigmah`
- `/feedback_apex_south/sigmap`
- `/feedback_apex_south/sigmah`

## 4. 这些字段在代码里如何被消费

### 4.1 `WACCM-X` 如何消费 `MAGE` 输入

`CESM` 侧字段注册位置：

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/cpl/nuopc/atm_import_export.F90`

当前已接入的导入字段：

- `Sx_mage_epot`
- `Sx_mage_avg_energy`
- `Faxx_mage_numflux`

实际消费位置：

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90`

对应关系：

- `mage_waccmx_copy_aurora(...)` 读出 `AVG_ENG` 和 `NUM_FLUX`
- `prescr_kev` 直接取 `AVG_ENG`
- `prescr_efx = AVG_ENG * NUM_FLUX * 1.602e-13`
- `mage_waccmx_copy_epot(...)` 读出外部 `POT`
- `d_pie_set_external_epot(...)` 用该 `POT` 覆盖电势场

### 4.2 `MAGE/REMIX` 如何消费 `WACCM-X` 回传

`CESM` 侧反馈缓存与写文件位置：

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90`

当前 formal 主反馈文件真实导出的字段是：

- `sigmap`
- `sigmah`

同一份 stub 代码内部同时维护：

- `neutral_rhs_proxy_cache`
- `neutral_rhs_edyn_cache`
- `neutral_rhs_edyn_geo_cache`

并可在实验开关下写独立 `NSRHS` sidecar，但它不属于当前 live 正式主流程默认输出。

`kaiju` 侧读反馈包并写入 `gcm_T` 的位置，最早在实验副本中实现，随后已并入隔离主线 worktree：

- 早期实验副本：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling/src/remix/waccmx_stub_backend.F90`
- 隔离主线 worktree：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_mainline/src/remix/waccmx_stub_backend.F90`

对应关系：

- `sigmap -> gcm%APEX%mixInput(h,1)`
- `sigmah -> gcm%APEX%mixInput(h,2)`
- `neutral_rhs -> gcm%GEO%mixInput(h,1)`

随后在 `run_mix(...,gcm=vApp%gcm)` 路径中被写回 `REMIX` 状态：

- `St%Vars(:,:,SIGMAP)`
- `St%Vars(:,:,SIGMAH)`
- `St%Vars(:,:,NEUTRAL_WIND)`（GEO 侧代理项）

再进入：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_mainline/src/remix/mixsolver.F90`

参与电势求解矩阵。

## 5. 元数据和辅助定位量

除核心物理字段外，当前桥里还会携带这些辅助量：

| 类型 | 量 | 作用 |
| --- | --- | --- |
| 点定位 | `cid` | 对应 `CESM` 本地列 ID |
| 点定位 | `lat`, `lon` | rank 文本文件中用于空间定位 |
| 网格定位 | `theta`, `phi` | HDF5 包中保存的二维网格角坐标 |
| 时间元数据 | `time_seconds` | 当前前向包时刻 |
| 时间元数据 | `mjd` | 修改儒略日 |

这些不是主要耦合物理量，但没有它们就无法做桥接重映射和时刻对齐。

## 6. `neutral_rhs` 现在是什么状态

它当前不是一个单一状态，而是“formal 主线默认未激活 + 实验线已技术贯通”的双轨状态。

### 6.1 当前 `CESM` 代码里已经定义了 `neutral_rhs` 代理和 `edyn rhs` 候选源

真实 `CESM` 反馈 stub：

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90`

当前会缓存并写出：

- `sigmap_cache`
- `sigmah_cache`
- `neutral_rhs_cache`

其中：

- `neutral_rhs_proxy_cache` 是 Pedersen 电导加权的纬向中性风，从 `m/s` 转成 `cm/s`
- `neutral_rhs_edyn_cache` 来自 `rhs_bothhem -> regrid_mag2phys_2d(...)`
- `neutral_rhs_cache` 由 `MAGE_WACCMX_NEUTRAL_RHS_MODE` 在 `proxy` 和 `edyn_rhs` 之间选择

但当前 formal 主反馈写文件时每行仍是：

- `cid lat lon sigmap sigmah`

真正显式导出的 `NSRHS` 当前只在实验开关下通过独立 sidecar 写出：

- `mage_waccmx_nsrhs_rank*.txt`
- `mage_waccmx_nsrhs_geo_rank*.txt`

### 6.2 formal bridge 解析器兼容 `neutral_rhs`，但当前 live 主流程默认回填为零

在：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cesm_feedback_to_kaiju_feedback.py`

里，解析器会：

- 如果 rank 反馈文件只有 5 列，就把 `neutral_rhs` 回填为 `0.0`
- 如果存在第 6 列，再把它读成 `neutral_rhs`

然后统一重映射到：

- `/feedback_geo_north/neutral_rhs`
- `/feedback_geo_south/neutral_rhs`

所以当前 formal bridge 的代码能力是“兼容 `neutral_rhs`”，但当前 live 正式主流程的实际产物仍然是零场；非零 `neutral_rhs/NSRHS` 属于独立实验线。

### 6.3 主线 `kaiju` 仍然没有原生启用 GEO 侧正式回传

主线：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/tgcm.F90`

默认设置里：

- `gcm%GEO%gcm2mix_nvar = 0`

注释已经写明是：

- `Neutral Winds (eventually)`

也就是说，原始主线代码仍然只把 `APEX` 侧 `SIGMAP/SIGMAH` 当成正式完成态；`GEO` 侧 neutral-wind/dynamo 回传在主线设计上仍然属于“以后再做”的位置。

### 6.4 实验副本里已经把它真正接回了 `REMIX`

在实验副本：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling/src/remix/waccmx_stub_backend.F90`

里，`neutral_rhs` 已经会被读入并映射到：

- `NEUTRAL_WIND` slot

并且实验副本的：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling/src/remix/mixsolver.F90`

也确实加了一个很小的代理项：

- `neutral_rhs_scale * St%Vars(:,:,NEUTRAL_WIND) * G%cosd`

这一步说明实验线里的 `neutral_rhs/NSRHS` 已经真实回到第二轮 `Kaiju` 求解里。  
但当前 live 正式主流程仍然没有把非零 `neutral_rhs` 作为默认正式回传量。

## 7. 要让 `neutral_rhs` 从“真实代理回传”升级成“正式耦合量”，还缺什么

至少还缺下面三步：

1. `CESM/WACCM-X` 侧需要把当前代理定义升级成最终物理定义  
   选项可以是：
   - 真实 `neutral wind` 分量
   - 已投影好的 dynamo forcing
   - 或物理意义更严格的 `neutral_rhs`

2. 文件桥必须把这个量从 `CESM` 真实反馈文件转成 `kaiju` 反馈包  
   当前这一步已经能做，但还需要单位、方向和物理语义最终定稿

3. `MAGE/REMIX` 侧要把它接到一个物理上自洽的槽位  
   目前的 `NEUTRAL_WIND` proxy 是最小可运行接口，但还不足以代表正式完成态

## 8. 当前最准确的表述

当前真实闭环可以准确表述为：

- 当前正式完成：`POT / AVG_ENG / NUM_FLUX <-> SIGMAP / SIGMAH`
- 已验证的实验增强项：`neutral_rhs / NSRHS`

所以如果你在汇报里要写一句最稳妥的话，建议写成：

> 当前 `MAGE-WACCMX` 真实文件桥已完成 `POT / AVG_ENG / NUM_FLUX -> WACCM-X` 与 `SIGMAP / SIGMAH -> MAGE/REMIX` 的双向闭环；另外，`neutral_rhs / NSRHS` 实验增强通道也已技术跑通，但它当前仍与 live 正式主流程分开管理，尚不是默认启用的最终 neutral-dynamo 物理闭合。
