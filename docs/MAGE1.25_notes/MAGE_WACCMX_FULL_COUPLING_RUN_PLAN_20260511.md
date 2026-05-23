# MAGE-WACCMX 完全耦合运行规划

Date: 2026-05-11

## 目标定义

目标不是继续证明局部文件桥能跑，而是实现可称为 `MAGE-WACCMX` 的完整耦合运行：

- 磁层/内磁层侧：`GAMERA + RAIJU + REMIX + VOLTRON`，必要时包含 `CHIMP`
- 上层大气侧：真实 `CESM/WACCM-X`
- 双向变量交换：
  - `MAGE -> WACCM-X`: `POT / AVG_ENG / NUM_FLUX`
  - `WACCM-X -> MAGE/REMIX`: `SIGMAP / SIGMAH`
  - 后续增强：`neutral_rhs / NEUTRAL_DYNAMO_RHS`
- 运行形态至少达到“完整物理文件耦合”，最终目标是“在线 MPI/mediator 耦合”

## 当前边界

已经完成：

- 真实 `CESM/WACCM-X` 可独立大规模运行。
  - 代表 case: `waccmx_control_f09_20231013_latest`
  - job `4802772`
  - 资源：`9` 节点，`576` MPI tasks，`4500G`
  - 配置确认：`-waccmx -ionosphere wxie`，`waccmx_opt='ionosphere'`
- 真实 `MAGE-TIEGCM` 在线 MPI 路线可运行。
- `MAGE-WACCMX` 文件桥已能完成变量闭环。
  - `POT / AVG_ENG / NUM_FLUX`
  - `SIGMAP / SIGMAH`
  - 1 小时文件桥基线：job `4747824`，`NUM_CYCLES=12`，墙钟 `01:09:34`
- `neutral_rhs` 路线已有第一阶段探测，但还不是正式动力学闭环。

仍未完成：

- Kaiju/Voltron 侧仍存在 `WACCMX_STUB` 后端，不能称为正式 WACCM-X backend。
- 当前文件桥会反复启停 CESM/Kaiju，效率和物理连续性都不是最终形态。
- 还没有把 `MAGE` 作为 CESM/CIME/Mediator 内的在线组件接入。
- 还没有大规模 `WACCM-X + GAMERA + RAIJU` 同一作业内的生产级运行记录。

## 推荐路线

建议分两阶段，不直接跳到 CESM mediator。原因是 mediator 集成跨度大，失败后很难判断是接口、资源、重启、还是物理变量问题。

### 阶段 A：完整物理文件耦合

目标：去掉“stub 语义”，让完整 MAGE 侧和真实 WACCM-X 侧以文件方式稳定耦合运行。

这一步仍然用文件交换，但不再把它表述为 smoke/stub。它应作为正式在线耦合前的物理集成基线。

关键改动：

1. 在 Kaiju/Voltron 中新增正式后端名，例如 `gcmBackend="WACCMX_FILE"`。
2. `WACCMX_FILE` 后端只做真实文件交换：
   - 不生成占位 `SIGMAP/SIGMAH`
   - 只读取真实 WACCM-X feedback package
   - 写出 MAGE 侧真实 forward package
3. 将当前 `waccmx_stub_backend.F90` 中可复用的 HDF5/text I/O 拆成中性名字：
   - `waccmx_file_backend.F90`
   - `waccmx_feedback_io.F90`
   - `waccmx_forward_io.F90`
4. 把 non-MPI 和 MPI Voltron 都接入同一套 backend。
5. 使用完整 MAGE 侧 MPI 配置，而不是只依赖 non-MPI smoke 路径。
6. WACCM-X 侧使用已验证的 `576` task case 作为模板，而不是继续依赖小规模 `qpx2000` 桥接测试 case。

阶段 A 的成功标准：

- 同一个 Slurm 作业内完成：
  - MAGE 全模块推进一个耦合段
  - WACCM-X 读取 MAGE forcing 并推进一个耦合段
  - WACCM-X feedback 被 MAGE/REMIX 消费
- 至少完成 `12` 个 cycle，也就是 `1 h` 模拟时间。
- 输出中不再出现 `WACCMX_STUB contract summary`。
- contract/summary 中明确写 `gcmBackend=WACCMX_FILE` 或等价正式名。
- `SIGMAP/SIGMAH` 来自真实 WACCM-X feedback。
- `POT / AVG_ENG / NUM_FLUX` 来自真实 MAGE/REMIX/Voltron 输出。

推荐资源：

- 第一轮开发验证：`1` 节点，`4` CPU，`256G`，保持当前文件桥基线。
- 第一次完整 WACCM-X 模板验证：`9` 节点，`576` tasks，`4500G`，复用 `waccmx_control_f09_20231013_latest` 布局。
- MAGE 侧并行验证：参考当前 `MAGE-TIEGCM` 作业布局，至少 `2` 节点，`128` CPU 级别。
- 阶段 A 联合运行预估：先按 `11-12` 节点申请，其中 WACCM-X 占 `9` 节点，MAGE 占 `2-3` 节点。

阶段 A 的直接工作包：

1. 固化两个控制样例。
   - WACCM-X 控制样例：`waccmx_control_f09_20231013_latest`
   - MAGE 控制样例：当前可完成的 `gtrd_20260812_1200_2400_quiet_*` 或 `gtrd_20211204_0500_0510_official`
2. 把 `WACCMX_STUB` 改造成正式 `WACCMX_FILE` 后端。
3. 写一个新的 Slurm driver。
   - 名称建议：`run_mage_waccmx_filecoupled_1h.sbatch`
   - 先串行 orchestration，稳定后再 MPMD 同作业调度
4. 先跑 `1 cycle = 5 min`。
5. 再跑 `3 cycles = 15 min`。
6. 最后跑 `12 cycles = 1 h`。
7. 每轮生成统一状态文件：
   - `cycleXX_forward_summary.md`
   - `cycleXX_waccmx_feedback_summary.md`
   - `cycleXX_mage_feedback_summary.md`
   - `final_coupling_report.md`

### 阶段 B：生产级在线耦合

目标：从文件桥升级为真正在线耦合，接近 `MAGE-TIEGCM` 的耦合方式。

有两条候选路线：

#### B1：MPMD 在线外部耦合

在同一个 Slurm allocation 中同时启动：

- `voltron_mpi.x`
- `cesm.exe`

通过 MPI communicator 或轻量 socket/ESMF side-channel 交换数据。

优点：

- 比 CIME mediator 接入简单。
- 更接近当前 MAGE-TIEGCM 的运行模式。
- 可以逐步替代文件 I/O。

缺点：

- CESM/CIME 的启动和 MPI communicator 管理较复杂。
- 如果不进入 CIME mediator，长期维护性一般。

#### B2：CESM/CIME mediator 集成

把 MAGE 作为 CESM 外部组件或 mediator 数据源接入。

优点：

- 最符合 CESM 体系的长期生产方式。
- 历史、重启、时间管理、component coupling 更正规。

缺点：

- 工程量最大。
- 需要定义 MAGE component interface、field bundle、grid mapping、restart 规则。
- 调试周期长，不适合作为下一步立即目标。

推荐顺序：

1. 先完成阶段 A。
2. 再做 B1。
3. 最后根据稳定性决定是否投入 B2。

## 变量与接口清单

第一阶段必须稳定：

| 方向 | 变量 | 状态 | 下一步 |
| --- | --- | --- | --- |
| MAGE -> WACCM-X | `POT` | 已在文件桥验证 | 移入正式 `WACCMX_FILE` |
| MAGE -> WACCM-X | `AVG_ENG` | 已在文件桥验证 | 移入正式 `WACCMX_FILE` |
| MAGE -> WACCM-X | `NUM_FLUX` | 已在文件桥验证 | 移入正式 `WACCMX_FILE` |
| WACCM-X -> MAGE | `SIGMAP` | 已在文件桥验证 | 保持真实 WACCM-X 来源 |
| WACCM-X -> MAGE | `SIGMAH` | 已在文件桥验证 | 保持真实 WACCM-X 来源 |
| WACCM-X -> MAGE | `NEUTRAL_DYNAMO_RHS` | 仍是未完成增强项 | 放到阶段 A 后半或阶段 B |

第二阶段再处理：

- 时间插值/保持策略
- 网格映射误差统计
- 单位和符号约定的强校验
- restart/reproducibility
- 多耦合步能量/电流闭合诊断

## 下一步立即执行计划

### Step 1：冻结基线

产出：

- `MAGE_WACCMX_BASELINE_MANIFEST_20260511.md`

内容：

- WACCM-X case 路径、job、PE layout、namelist 关键项
- MAGE case 路径、job、XML 关键项
- 当前文件桥脚本、二进制、Python env
- 当前成功和失败边界

验收：

- 任何后续运行都能明确说明基于哪个 WACCM-X baseline 和哪个 MAGE baseline。

### Step 2：实现 `WACCMX_FILE` backend

产出：

- 新后端源码
- 新 XML 示例
- 新 smoke test

验收：

- `voltron.x` 输出不再出现 `WACCMX_STUB`。
- `gcmBackend="WACCMX_FILE"` 能读取真实 feedback package。
- `SIGMAP/SIGMAH` 数值与输入 feedback package 一致。

### Step 3：重跑 1-cycle 文件耦合

产出：

- `runs/waccmx_file_backend_c1_YYYYMMDD`

验收：

- MAGE forward package 生成。
- WACCM-X consume 成功。
- WACCM-X feedback package 生成。
- MAGE/REMIX ingest 成功。
- 无 `size mismatch`、无 `ESMF rc=51`、无 CESM `SIGSEGV`。

### Step 4：重跑 12-cycle 文件耦合

产出：

- `runs/waccmx_file_backend_1h_YYYYMMDD`

验收：

- `12` cycles 全部完成。
- 1 小时模拟时间跑通。
- 每轮 `SIGMAP/SIGMAH` 合理变化。
- restart/continuation 不再依赖历史 repair hook。

### Step 5：切换到 576-task WACCM-X

产出：

- `waccmx_control_f09_20231013_latest` 的耦合分支 case

验收：

- 大规模 WACCM-X 可读取 MAGE forcing。
- 仍能写出 feedback。
- 至少 1 cycle 成功。

### Step 6：MAGE 侧切换到完整 MPI 配置

产出：

- MAGE full MPI + WACCM-X file backend 的联合 driver

验收：

- 不再使用 non-MPI smoke 路径作为主路径。
- GAMERA/RAIJU/REMIX/VOLTRON 正式参与。
- 至少 1 cycle 成功。

### Step 7：联合大规模 1H run

产出：

- 第一个可报告的完整物理 MAGE-WACCMX 文件耦合 run

建议资源：

- WACCM-X: `9` 节点，`576` tasks
- MAGE: `2` 节点，`128` CPUs 起步
- 总申请：`11-12` 节点，内存按节点默认或保守 `500G/node`

验收：

- `1 h` 模拟完成。
- 所有变量双向交换。
- 输出报告不含 stub 表述。
- 保存完整日志、summary、history/restart 文件。

## 风险项

1. `WACCMX_STUB` 语义残留。
   - 处理：必须新增正式 backend 名称，报告里禁止继续出现 stub。
2. WACCM-X restart/continuation 脆弱。
   - 处理：优先使用 fresh baseline，不依赖丢失的 repair hook。
3. 576-task WACCM-X 与 MAGE forcing 接口不一致。
   - 处理：先只跑 1 cycle，并保留 rank-map/网格维度检查。
4. `neutral_rhs` 物理闭合不成熟。
   - 处理：先不作为阶段 A 的硬门槛；`SIGMAP/SIGMAH` 完整闭环后再加入。
5. 文件 I/O 成本高。
   - 处理：阶段 A 接受文件 I/O，阶段 B 再优化为在线交换。

## 推荐下一条命令级任务

下一步不要继续提交 `submit_fresh_rebuild_plus1h.sh`。

建议先做：

```bash
# 1. 生成完整 baseline manifest
# 2. 从 WACCMX_STUB 拆出正式 WACCMX_FILE backend
# 3. 用 WACCMX_FILE 跑 1-cycle
```

也就是说，下一轮开发的核心不是增加运行时长，而是：

```text
WACCMX_STUB -> WACCMX_FILE
```

只有完成这个替换后，后续的 `1H`、`12H`、多节点大规模运行才有资格称为 `MAGE-WACCMX` 完整耦合推进。
