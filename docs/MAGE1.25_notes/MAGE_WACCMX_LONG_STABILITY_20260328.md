# MAGE-WACCMX Long Stability Check

Date: 2026-03-28
Updated: 2026-03-29

## Scope

这份记录只总结一个问题：

- 当前真实文件桥在“单轮闭环成功”之后，是否还能继续做真实 `CESM` continuation，
  把时间从 `00300` 再推进到 `00600`

为避免把问题误归因到某一种外部 forcing，本次做了 3 条对照：

1. `all x14 + smooth2`
2. `epot x14 + smooth2`
3. `x1 baseline`

## Test Roots

### 1. `all x14 + smooth2`

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_all_x14_smooth2_c4_20260328_190627`

Result:

- seed `kaiju` forward run: success
- `cycle01` CESM continuation: failure

Observed signature:

- read existing restart:
  `mage_qpx2000_f19_qhslurm_gnu.cam.r.2005-12-31-00300.nc`
- external forcing accepted:
  `d_pie_set_external_epot: input/limited absmax 169.702 -> 150.000`
- continuation phase entered:
  `med_phases_restart_read ... 2005 12 31 0 5 0 0`
- new restart writing began:
  `cam.r.2005-12-31-00600.nc`, `cam.rh*.2005-12-31-00600.nc`
- then:
  `Program received signal SIGSEGV`
  `rank 0 ... signal 11`

Primary log:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_all_x14_smooth2_c4_20260328_190627/manual_cesm_cycle01.log`

### 2. `epot x14 + smooth2`

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_epot_x14_smooth2_c4_20260328_191116`

Result:

- seed `kaiju` forward run: success
- `cycle01` CESM continuation: failure

Observed signature:

- read existing restart:
  `mage_qpx2000_f19_qhslurm_gnu.cam.r.2005-12-31-00300.nc`
- external forcing accepted:
  `d_pie_set_external_epot: input/limited absmax 169.702 -> 150.000`
- continuation phase entered:
  `med_phases_restart_read ... 2005 12 31 0 5 0 0`
- new restart writing began:
  `cam.r.2005-12-31-00600.nc`, `cam.rh*.2005-12-31-00600.nc`
- then:
  `Program received signal SIGSEGV`
  `rank 0 ... signal 11`

Primary log:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_epot_x14_smooth2_c4_20260328_191116/manual_cesm_cycle01.log`

### 3. `x1 baseline`

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_baseline_x1_c1_20260328_191538`

Result:

- seed `kaiju` forward run: success
- `cycle01` CESM continuation: failure

Observed signature:

- read existing restart:
  `mage_qpx2000_f19_qhslurm_gnu.cam.r.2005-12-31-00300.nc`
- external forcing remained mild:
  `d_pie_set_external_epot: input/limited absmax 12.122 -> 12.122`
- continuation phase entered:
  `med_phases_restart_read ... 2005 12 31 0 5 0 0`
- new restart writing began:
  `cam.r.2005-12-31-00600.nc`, `cam.rh*.2005-12-31-00600.nc`
- then:
  `Program received signal SIGSEGV`
  `rank 0 ... signal 11`

Primary log:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/long_baseline_x1_c1_20260328_191538/manual_cesm_cycle01.log`

## Practical Conclusion

当前长期稳定性结论已经进一步收紧：

- 对于当前主案例里那套生产式 `00300` restart 谱系：
  第一次 `00300 -> 00600` continuation 仍然会崩
- 这个崩溃在：
  - `all x14 + smooth2`
  - `epot x14 + smooth2`
  - `x1 baseline`
  三条路径上都复现了
- 但后续新增的自洽隔离控制已经证明：
  - `edyn off` 的 `startup -> continue` 能成功到 `00600`
  - 默认 `edyn on` 的 `startup -> continue` 也能成功到 `00600`

所以当前长期稳定性的首要 blocker，已经从更宽泛的：

- `CESM continuation / restart-after-restart path`

收窄成更具体的：

- `当前主案例那套 bridge-enabled / production-lineage 00300 restart set`

而不是：

- 单纯的 `x14` forcing 太强
- 或者所有 continuation 都天然不可用
- 或者 `edyn on` 本身一打开就天然会崩

到 2026-03-29 的最新补充诊断为止，这个 blocker 又进一步收紧了一步：

- 在一组已经成功的 isolated `00300` restart 谱系上，
  只把主案例 `cam.r.00300` 里的 `ShortLivedSpecie` 单独换进去，
  就足以再次复现完全相同的
  `med_phases_restart_read -> write 00600 restart -> rank 0 SIGSEGV`
  崩溃链

因此当前最强的工程表述已经变成：

- 当前主案例 `00300 -> 00600` continuation 的首要触发体，
  已经可以压缩到 `cam.r.2005-12-31-00300.nc` 里的
  `ShortLivedSpecie`

到同一天的 species-level 补充测试为止，这个结论又继续收紧成：

- 只换 `ShortLivedSpecie` 的 species `12 = Op`，就足以复现同一条
  `med_phases_restart_read -> write 00600 restart -> rank 0 SIGSEGV`
  崩溃链
- 反过来，把另外 13 个 short-lived species 都换成主案例值，但显式保留
  成功谱系的 `Op`，continuation 仍可成功到 `00600`

因此当前最强的工程表述已经进一步更新为：

- 当前主案例 `00300 -> 00600` continuation 的决定性触发体，
  已经可以压缩到 `cam.r.2005-12-31-00300.nc` 里的
  `ShortLivedSpecie -> Op`

同一天的 repair-oriented replay 还进一步说明：

- 直接在原始主案例失败谱系里，只把 `cam.r.00300` 中
  `ShortLivedSpecie -> Op` 换成成功谱系值，
  `00300 -> 00600` continuation 就能重新成功到 `00600`
- 更进一步，把这条修复后的主案例谱系继续拿来做下一段 true continue，
  `00600 -> 00900` 也已经成功，且正常写出
  `cam.r.2005-12-31-00900.nc` 与 `cam.rs.2005-12-31-00900.nc`
- 随后第三段 true continue 也已经成功：
  `00900 -> 01200` 正常写出
  `cam.r.2005-12-31-01200.nc` 与 `cam.rs.2005-12-31-01200.nc`
- 再下一段 true continue 也已经成功：
  `01200 -> 01500` 正常写出
  `cam.r.2005-12-31-01500.nc` 与 `cam.rs.2005-12-31-01500.nc`
- 随后的 aggressive chain 也已经整段跑通：
  `01500 -> 01800 -> 02100 -> 02400 -> 02700 -> 03000`
  全部正常写出下一时刻 `cam.r/cam.rs` restart 并 `med_finalize`

所以截至当前，长期稳定性的最小工程修复候选也已经出现：

- `cam.r.2005-12-31-00300.nc -> ShortLivedSpecie -> Op`

并且这条最小修复候选不再只是“一次性把 `00300 -> 00600` 救活”，而是：

- 已经连续通过 `00300 -> 00600 -> 00900 -> 01200 -> 01500 -> 01800 -> 02100 -> 02400 -> 02700 -> 03000`

`2026-03-30` 的 root-cause 追踪又补上了一条关键时间定位：

- 对成功隔离 seed 与失败主案例做 `cam.rh0/cam.rh2` compare 后发现，
  `00000` 的 `Op / UI / VI / WI / TElec / TIon` 仍完全一致
- 但到 `00300`，这些 ionosphere-facing 字段已经全部明显分叉
- 所以当前最早已知的坏化窗口不是“startup 之前”，而是第一次 startup 的
  `00000 -> 00300`
- 这也解释了为什么后续 `00300 -> 00600` pure continuation 即使不再依赖外部
  `MAGE epot` 注入，也仍然会崩：因为坏状态已经被写进 `cam.r.00300`

## Diagnostic Findings

这次进一步检查后，时间线可以压得更清楚：

- 当前 case 的 dycore 是 `FV`
  证据在
  `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run/atm_in`
  里的 `&dyn_fv_inparm`
- `cesm.exe` 带 `debug_info`，且三条 continuation 失败路径的低地址回溯完全一致
- 这些地址已经稳定映射到同一条调用链：
  `atm_comp_nuopc:ModelAdvance -> cam_comp:cam_run1 -> stepon:stepon_run1 -> dyn_comp:dyn_run -> cd_core -> sw_core:d_sw -> tp_core:tp2c/tp2d/xtpv`

这说明：

- 崩溃发生在 `CAM` 的 `FV` 动力核链里
- 它不是 bridge Python 脚本本身的异常退出
- 它也不是 `cam.r.00600` 文件“根本没写出来”

更细一点的顺序是：

1. continuation 已进入 `med_phases_restart_read`
2. `cam_run4` 已把 `00600` 的主 restart 和 `cam.rh*` history restart 全部打开并写出
3. `atm.log` 已出现 `WSHIST`、`rpointer.cam.2005-12-31-00600` 和 `QNEG3 summary`
4. 然后 `ModelAdvance` 在下一次 `cam_run1` 里崩到 `FV` 动力核

因此当前更接近下面这个判断：

- **restart 写文件动作本身基本完成了**
- **真正的崩点是在 continuation 读入后的下一段积分里**

从源码路径看，这个 continuation case 还走了你本地 `WACCM-X` 的真实 ionosphere 扩展，而不是 dummy 接口：

- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90`
- `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/dpie_coupling.F90`

其中 `d_pie_set_external_epot` 的确在 continuation 里被调用，但当前证据只能支持下面这句：

- external `epot` 已成功注入 continuation run

还**不能**直接证明：

- 崩溃就是由 `epot` 注入本身触发

因为 `x1 baseline` continuation 也在同一位置崩。

截至这一步，最稳妥的工程判断是：

- 当前主线长期稳定性的首要 blocker 是
  `主案例 00300 restart 谱系里的 continuation state`
- 不是整数倍 forcing 扫描本身
- 也不是简单的 restart 文件缺失
- 也不是“generic edyn-on continuation 一定会坏”

## Matched-Pointer Pure Control

在上面那轮检查之后，又补做了一个更干净的对照：

- run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/pure_continuation_checks/pure_continue_2005-12-31-00300_20260328_230044`
- used pointers:
  `rpointer.cam.2005-12-31-00300`
  `rpointer.cpl.2005-12-31-00300`
- bridge input files removed during the run:
  `mage_waccmx_import_rank*.txt`
  `mage_waccmx_epot_global.txt`

这个对照的目的，是排除两种可能：

- 之前 long-run 脚本把“最新 `cam` 指针”和“最新 `cpl` 指针”分别取用，造成 `00600/00300` 错配
- bridge 外部输入本身导致 continuation 崩溃

结果是：

- 即使强制使用匹配的 `00300/00300` restart 指针
- 即使临时移走全部 `MAGE -> WACCM-X` 导入文件
- `CESM/WACCM-X` 仍然在同一位置复现 `SIGSEGV`

观察到的特征仍然相同：

- `med_phases_restart_read ... 2005 12 31 0 5 0 0`
- `cam.r.2005-12-31-00600.nc` 与 `cam.rh*.2005-12-31-00600.nc` 已打开写出
- 之后 rank 0 `signal 11`
- 低地址回溯仍然是
  `0xb9ae47 -> 0xb9c483 -> 0xb9ca02 -> 0xb8ceef -> 0x8b553d -> 0x57c697 -> 0x725a6b -> 0x512195 -> 0x4ff641`
- 这次日志里**没有** `d_pie_set_external_epot`，说明它甚至不依赖外部 `MAGE epot` 注入就能复现

所以，这个新对照进一步加强了前面的结论：

- continuation 崩溃**不是**由 `rpointer.cam=00600 / rpointer.cpl=00300` 错配单独造成
- continuation 崩溃也**不是** bridge 输入文件存在与否决定的

## `ShortLivedSpecie` Isolation

在上面这些更宽的 transplant / compare 之后，又补做了一个更窄的单变量因果测试。

关键前提先是两组已有 patched restart set 的直接比较：

- failing set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_all3_plus_chem_from_maincase_20260329d`
- successful set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_all3_plus_chem_no_short_from_maincase_20260329e`

两者 continuation 结果分别是：

- `all3_plus_chem`: fail
- `all3_plus_chem_no_short`: success

而用 `cam_restart_compare_all` 对两份 `cam.r.00300` 逐变量比较时，
唯一发现的差异变量只有：

- `ShortLivedSpecie`

比较结论可以压成一句：

- 这两组 patched `cam.r` 的差别已经缩到单变量层面

随后做了真正的单变量 transplant：

- donor failing `cam.r`:
  `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run/mage_qpx2000_f19_qhslurm_gnu.cam.r.2005-12-31-00300.nc`
- base successful patched set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_all3_plus_chem_no_short_from_maincase_20260329e`
- new `ShortLivedSpecie-only` patched set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_shortlived_only_from_maincase_20260329g`

对应 continuation run：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_shortlived_only`

结果：

- fail
- 仍然进入 `med_phases_restart_read`
- 仍然写出 `cam.r/rh*.2005-12-31-00600.nc`
- 之后仍然是 `Program received signal SIGSEGV`
- 仍然是 `rank 0 signal 11`

所以这一步把结论推进成了强因果表述：

- **主案例 `cam.r.00300` 里的 `ShortLivedSpecie` 单独就足以把成功谱系打坏**

而结合前面那组“只差一个变量”的成功/失败配对，现在最稳妥的诊断就是：

- 当前主案例 continuation blocker 的最小已知触发体是
  `ShortLivedSpecie`

同时，长跑脚本已修正：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_long_coupling_stability.sh`

现在它不再分别取“最新 CAM 指针”和“最新 CPL 指针”，而是只接受**时间戳匹配的一对** restart pointers。

## `ionos_edyn_active = .false.` Probe

随后又尝试了一个更激进的隔离对照：

- still use matched `00300/00300` pointers
- still remove bridge import files
- additionally set `ionos_edyn_active = .false.`

运行根目录：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/pure_continuation_checks/pure_continue_2005-12-31-00300_20260328_230833`

这轮没有进入之前那种 `med_phases_restart_read -> 00600 -> SIGSEGV` 链，而是在更早阶段被
`read_restart_history` 相关逻辑拦住：

- `BLD_HTAPEFLD_INDICES: something wrong, field not found on masterlist`
- missing field:
  `UI`
- then:
  `Unknown error submitted to shr_abort_abort`
  `MPI_ABORT`

关键证据是这轮留下的有效 `atm_in` 副本：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/pure_continuation_checks/pure_continue_2005-12-31-00300_20260328_230833/atm_in_effective`

其中已经能看到：

- `ionos_edyn_active = .false.`
- `fincl7 = 'PHIM2D','POTEN','QIONSUM','ELECDEN','QJOULE'`

但日志仍然要求 `UI`，说明：

- `00300` 的 history restart 状态本身是按 `edyn on` 配置写出来的
- 仅仅修改新的 `atm_in`，还不足以构成一个“合法的 edyn-off restart continuation”

因此，这个 probe 的当前结论不是“edyn off 也失败于同一物理阶段”，而是：

- **`edyn off` continuation control 目前被 restart-history compatibility 卡住**
- 想把 `edyn` 真正从 continuation 里剥离，还需要连 history-restart 配置一起做成自洽的一套

## Self-Consistent `edyn off` Seed+Continue

上面这个 probe 的问题，后来继续往前推进后已经被真正拆开了。

首先做的是一套**自洽的 `edyn off` 隔离 seed**，不再复用 `edyn on` 写出来的
`00300` history restart：

- first isolated root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260328_235136`

这一步里，`startup` 已经成功写出：

- `mage_qpx2000_f19_qhslurm_gnu.cam.r.2005-12-31-00300.nc`
- `mage_qpx2000_f19_qhslurm_gnu.cam.rs.2005-12-31-00300.nc`
- `mage_qpx2000_f19_qhslurm_gnu.cpl.r.2005-12-31-00300.nc`
- `rpointer.cam.2005-12-31-00300`
- `rpointer.cpl.2005-12-31-00300`

但第一次自动脚本的“continue”其实还是假 continuation，因为隔离脚本第二段沿用了
`nuopc.runconfig` 里的：

- `start_type = startup`

所以那次 `continue_exit_status = 0` 只说明它又成功跑了一遍 `00300`，还不是真正的
`00300 -> 00600`。

随后做了两步修正：

1. 修脚本，在第二段运行前把 `nuopc.runconfig` 改成 `start_type = continue`
2. 在上述同一 run 上手工验证一次真正的 `continue`

手工验证日志：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260328_235136/continue_true.log`

这次已经明确出现：

- `med_phases_restart_read`
- `cam.r.2005-12-31-00600.nc`
- `cam.rh*.2005-12-31-00600.nc`
- `cam.rs.2005-12-31-00600.nc`
- `cpl.r.2005-12-31-00600.nc`
- `med_finalize max rss=...`

并且退出码是：

- `0`

最后又做了一轮**端到端自动化复跑**，确认不再需要手工介入：

- clean rerun root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260329_000102`

这轮的 `summary.txt` 已确认：

- `startup_exit_status 0`
- `continue_exit_status 0`

而 `continue.log` 已确认：

- `med_phases_restart_read`
- `cam.r.2005-12-31-00600.nc`
- `cam.rh*.2005-12-31-00600.nc`
- `cam.rs.2005-12-31-00600.nc`
- `cpl.r.2005-12-31-00600.nc`
- `rpointer.cam.2005-12-31-00600`
- `rpointer.cpl.2005-12-31-00600`
- `med_finalize max rss=5161394176.0 MB`

并且没有出现：

- `SIGSEGV`
- `MPI_ABORT`
- `BLD_HTAPEFLD_INDICES`
- `d_pie_set_external_epot`

因此，这一轮新增控制把结论进一步收紧为：

- **generic `CESM/WACCM-X` continuation 并没有彻底坏掉**
- **自洽的 `edyn off` seed + true continue 已成功跑通到 `00600`**

## Self-Consistent Default `edyn on` Seed+Continue

在确认 `edyn off` 自洽路径可以工作之后，又继续做了默认配置的隔离控制：

- clean default root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260329_000715`

这轮保持：

- `ionos_edyn_active` 默认值
- `ionos_xport_active` 默认值
- 无 bridge import 文件
- 第二段运行前自动把 `nuopc.runconfig` 改成 `start_type = continue`

这轮 `summary.txt` 已确认：

- `startup_exit_status 0`
- `continue_exit_status 0`

而 `continue.log` 已确认：

- `med_phases_restart_read`
- `cam.r.2005-12-31-00600.nc`
- `cam.rh*.2005-12-31-00600.nc`
- `cam.rs.2005-12-31-00600.nc`
- `cpl.r.2005-12-31-00600.nc`
- `rpointer.cam.2005-12-31-00600`
- `rpointer.cpl.2005-12-31-00600`
- `med_finalize max rss=5245419520.0 MB`

并且没有出现：

- `SIGSEGV`
- `MPI_ABORT`
- `d_pie_set_external_epot`

因此，现在的结论要再往前推一步：

- **self-consistent default `edyn on` continuation 也能成功**
- **所以 generic continuation 和 generic `edyn on` 都不是根因**
- **剩下最可疑的是主案例那套 `00300` restart 谱系本身**

## Self-Consistent Default `edyn on` + Bridge Imports

为了继续排除“是不是只要有 bridge import 就会坏”，又做了一轮更贴近主案例的隔离控制：

- root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260329_001326`

这轮保持：

- 默认 `edyn on`
- 默认 `ionosphere` 配置
- 从模板 run 目录复制真实
  `mage_waccmx_import_rank*.txt` 与 `mage_waccmx_epot_global.txt`
- 第二段运行前自动改成 `start_type = continue`

这轮 `summary.txt` 已确认：

- `startup_exit_status 0`
- `continue_exit_status 0`
- `copy_bridge_imports_from_template 1`

而日志也已确认：

- `startup.log` 中出现
  `d_pie_set_external_epot: input/limited absmax 12.122 -> 12.122`
- `continue.log` 中也出现
  `d_pie_set_external_epot: input/limited absmax 12.122 -> 12.122`
- `continue.log` 进入
  `med_phases_restart_read`
- 并成功写出：
  - `cam.r.2005-12-31-00600.nc`
  - `cam.rh*.2005-12-31-00600.nc`
  - `cam.rs.2005-12-31-00600.nc`
  - `cpl.r.2005-12-31-00600.nc`
  - `rpointer.cam.2005-12-31-00600`
  - `rpointer.cpl.2005-12-31-00600`
- 最终正常
  `med_finalize`

并且没有出现：

- `SIGSEGV`
- `MPI_ABORT`

因此，结论需要再缩一次：

- **bridge import 的存在本身并不足以触发主案例里的 continuation 崩溃**
- **generic continuation、generic `edyn on`、以及 import 存在本身都已经被隔离控制排除**
- **现在最可疑的仍然是主案例那套 `00300` restart 谱系，或与之绑定的 main-case 运行态**

## Operational Note

每次长跑脚本退出后，都已把 case 恢复到：

- `CONTINUE_RUN=FALSE`
- `nuopc.runconfig` 回到 `start_type = startup`

所以当前活动 case 没有被留在 continuation 模式。

## Restart Transplant Matrix

`2026-03-29` 又补了一轮更强的文件级剥离对照，专门回答：

- 崩溃是不是已经被固化进主案例 `00300` restart 文件集本身

详细矩阵见：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_RESTART_TRANSPLANT_MATRIX_20260329.md`

这里先压结论：

1. 用成功隔离谱系自己的 `00300` restart，
   通过新脚本做 existing-restart continue，仍然成功：
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_015448`

2. 把主案例失败的整套 `00300` restart 搬进干净隔离目录，
   仍然复现老的 `rank 0 SIGSEGV`：
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_015637`

3. 更关键的是混合覆盖结果：
   - 只覆盖主案例 `cam.r.00300`：
     失败
     `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_015909`
   - 只覆盖主案例 `cam.rs + cam.rh*`：
     成功
     `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_020046`
   - 只覆盖主案例 `cpl.r.00300`：
     成功
     `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_020238`

因此，长期 continuation 的当前 blocker 又进一步收紧成：

- **主案例 `cam.r.2005-12-31-00300.nc`**

也就是说，当前问题已经不需要再宽泛描述成：

- “continuation 普遍有问题”
- “bridge import 存在就会坏”
- “`cam history` 或 `cpl.r` 可能同样是主嫌疑”

目前最合理的下一个诊断方向，是直接对比：

- 主案例失败 `cam.r.00300`
- 隔离成功 `cam.r.00300`

在变量/状态层面到底差了什么。

这一步现在也已经完成，结论见：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_RESTART_TRANSPLANT_MATRIX_20260329.md`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cam_r_compare_report_20260329.txt`

新增结论是：

- 两个 `cam.r.00300` 的头信息一致，没有 schema 差异
- 关键动力学字段里也没有 `NaN/Inf`
- 但主案例失败 `cam.r.00300` 在 `U / V / PT` 上有明显更强的极值
- `DELP / Q / PS` 则几乎一致
- 进一步的 repair-oriented patch 也已经做过：
  - 只补 `U / V / PT`：
    仍失败
  - 再扩大到
    `U / V / PT / Optm1 / DTCORE / DUCORE / DVCORE`：
    仍失败

因此当前最稳妥的描述已经可以写成：

- **主案例 `cam.r.00300` 中的动力学主状态，尤其 `U / V / PT`，是 continuation 崩溃的首要嫌疑**
- 但当前还不能把根因收紧到这几项单独字段；
  更像是 `cam.r` 内更大范围的 dycore-related state 组合问题
