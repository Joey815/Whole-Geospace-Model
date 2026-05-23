# MAGE-WACCMX 当前执行路线

Date: 2026-05-12

## 当前判断

目标是实现可报告的 `MAGE-WACCMX` 完整耦合，而不是继续做局部 smoke test。

当前路线应以 `D -> O` 为主线：

- `D` 档用于接口、变量、restart、driver 的快速闭环。
- `O` 档用于正式 MAGE 分辨率验证。
- `Q` 档只作为可选中间网格验证，不作为主线。
- `H/Hex` 暂不推进；源码有预留，但本地没有实际 `lfmH.h5`，且 VOLTRON 对 `Nkp>=512` 默认有保护性 stop。

## 当前已完成边界

已经完成并可作为基线的部分：

- 文件桥变量闭环：
  - `MAGE/VOLTRON -> WACCM-X`: `POT / AVG_ENG / NUM_FLUX`
  - `WACCM-X -> MAGE/REMIX`: `SIGMAP / SIGMAH`
- `NUM_CYCLES=12` 代表约 `1 h` 模拟时间；历史 1h 文件桥参考作业墙钟约 `01:09:34`。
- fresh rebuild 路径可以在 `NSRHS=off` 下跑通正式电动力学闭环。

尚未完成或不能算正式完成的部分：

- 当前仍带有 `WACCMX_STUB` 语义残留，工程命名上不能称为正式 backend。
- 当前文件桥主要证明变量交换闭环，不等同于 CESM mediator/native MPI 在线耦合。
- `neutral_rhs / NEUTRAL_DYNAMO_RHS` 仍是增强线，不应阻塞电动力学主线。
- `H/Hex` 不是当前可用生产档位。

## 网格档位路线

| 档位 | 当前用途 | 是否进入主线 | 理由 |
| --- | --- | --- | --- |
| `D` | 快速闭环、debug、1-cycle/3-cycle/12-cycle | 是，第一主线 | 资源低，已有完整本地运行证据 |
| `Q` | 可选中间验证 | 可选 | 有网格但缺完整输出；REMIX 默认仍与 D 同为 `360 x 45` |
| `O` | 正式高分辨率验证 | 是，第二主线 | 当前本地已有 officialO 输出，是正式 MAGE 侧高档验证对象 |
| `H/Hex` | 暂不推进 | 否 | 无本地网格文件，源码默认拦截，资源和风险都过高 |

## 主执行路线

### Phase 0: 冻结当前基线

目的：确保后续每次运行都知道从哪个代码、case、restart、driver 出发。

产出：

- 更新 baseline manifest。
- 记录当前 `D/O` 网格维度、XML、可执行文件、driver、Python env、CESM case、restart 起点。
- 标记当前正式基线为 `NSRHS=off` 电动力学闭环。

验收：

- 能明确复现 `1-cycle` 和 `12-cycle` 文件桥。
- 报告中区分 `5 min/cycle`、`12 cycles=1 h`、墙钟时间。

### Phase 1: 固化网格交换契约

目的：先把 WACCM-X 与 MAGE 的网格关系定义清楚，再推进更大规模运行。

必须明确的映射：

- WACCM-X native `lon-lat-lev` 到 REMIX 高纬 `Np x Nt` conductance 网格。
- REMIX/VOLTRON 的 `POT / AVG_ENG / NUM_FLUX` 到 WACCM-X 可读 forcing 网格。
- D 档：REMIX `360 x 45`，VOLTRON `180 x 90`。
- O 档：REMIX `720 x 90`，VOLTRON `720 x 360`。

验收：

- 每个 exchange package 写入维度、单位、缺测值、南北半球顺序、经纬方向。
- 每轮生成维度检查 summary。
- 禁止靠文件名猜维度，必须读 HDF5/NetCDF 元数据。

### Phase 2: `WACCMX_STUB -> WACCMX_FILE`

目的：把已经能跑的文件桥改造成正式文件耦合 backend。

工作：

- 新增或重命名正式 backend：`WACCMX_FILE`。
- I/O 模块去掉 stub 语义，只保留真实 forward/feedback package。
- non-MPI 和 MPI Voltron 使用同一份 file backend contract。

验收：

- 日志中不再出现 `WACCMX_STUB contract summary`。
- `gcmBackend=WACCMX_FILE` 或等价正式名明确出现在运行配置和报告中。
- `SIGMAP/SIGMAH` 必须来自真实 WACCM-X feedback。
- `POT/AVG_ENG/NUM_FLUX` 必须来自真实 MAGE/REMIX/VOLTRON 输出。

### Phase 3: D 档正式文件耦合稳定性

目的：用最低风险配置证明正式 backend 能连续运行。

运行顺序：

1. `D + WACCMX_FILE + NSRHS=off`: `1 cycle`
2. `D + WACCMX_FILE + NSRHS=off`: `3 cycles`
3. `D + WACCMX_FILE + NSRHS=off`: `12 cycles = 1 h`

验收：

- 每轮 MAGE forward package、WACCM-X feedback package、MAGE feedback ingest 都成功。
- restart/continuation 不依赖历史 repair hook。
- `SIGMAP/SIGMAH` 范围稳定，无 NaN/Inf，无维度错配。
- 墙钟、CPU、内存、输出大小全部记录。

### Phase 4: O 档正式 MAGE 验证

目的：从 debug 档升级到正式 MAGE 侧高分辨率档。

运行顺序：

1. `O + WACCMX_FILE + NSRHS=off`: 只跑 `1 cycle`
2. 若成功，再跑 `3 cycles`
3. 若稳定，再考虑 `12 cycles = 1 h`

验收：

- O 档 GAMERA/RAIJU/REMIX/VOLTRON 都参与。
- O 档 REMIX `720 x 90` 和 VOLTRON `720 x 360` 的映射检查通过。
- 文件大小和内存增长符合预期，没有异常膨胀。

### Phase 5: `neutral_rhs / NEUTRAL_DYNAMO_RHS` 增强线

目的：在电动力学闭环稳定后，再推进中性动力学耦合。

策略：

- 不把 `neutral_rhs` 放进 Phase 3/4 的硬门槛。
- 先沿 TIEGCM-MAGE 的 `gnsrhs` 方案做对照。
- 先用 sidecar/diagnostic 模式输出，不直接强迫主动力学。
- 通过 D 档完成量纲、符号、投影、经纬顺序校验后，再进入 O 档。

验收：

- `NEUTRAL_DYNAMO_RHS` 非零且量级合理。
- 与 TIEGCM 路线的变量定义、投影方式、单位转换有逐项对照。
- 打开该项后不破坏 `POT/AVG_ENG/NUM_FLUX` 与 `SIGMAP/SIGMAH` 主闭环。

### Phase 6: 在线耦合路线

目的：从文件桥升级到更接近 MAGE-TIEGCM 的正式在线耦合。

推荐顺序：

1. 先做 MPMD 同作业外部耦合。
2. 文件 I/O 改为轻量内存/pipe/MPI side-channel。
3. 最后才考虑 CESM/CIME mediator 集成。

不建议现在直接做 CESM mediator，原因是跨度太大，失败后很难定位是网格、变量、restart、CIME 时间管理还是 MPI communicator 问题。

## 下一步具体动作

下一步不是跑 `H/Hex`，也不是先开 `neutral_rhs`。

推荐立即做：

1. 更新 baseline manifest，明确当前采用 `D/O`，不采用 `H/Hex`。
2. 实现或整理正式 `WACCMX_FILE` backend 命名。
3. 用 `D + WACCMX_FILE + NSRHS=off` 跑 `1 cycle`。
4. 通过后跑 `3 cycles`。已完成：`waccmx_file_formal_c3_20260512_S7276731`。
5. 通过后跑 `12 cycles = 1 h`。已完成 clean-exit 验证：`waccmx_file_formal_1h_clean_20260512_S7276927`。
6. 再把同一套 backend 切到 `O` 档做 `1 cycle`。

只有完成以上步骤后，才进入：

- `O` 档多 cycle
- `neutral_rhs`
- MPMD/native MPI
- CESM mediator
