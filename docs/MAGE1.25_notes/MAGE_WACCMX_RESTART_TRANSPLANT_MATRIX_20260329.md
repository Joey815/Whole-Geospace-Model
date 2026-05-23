# MAGE-WACCMX Restart Transplant Matrix

Date: 2026-03-29

## Purpose

这组测试只回答一个问题：

- 主案例 `00300 -> 00600` continuation 的崩溃，
  到底是由主案例 run 目录态触发，
  还是已经被固化进了那套 `00300` restart 文件集本身

## Sources

成功对照的 `00300` restart 来源：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue/seed_continue_20260329_001326/run`

失败主案例的 `00300` restart 来源：

- `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run`

测试驱动：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_isolated_existing_restart_continue.sh`

## Matrix

### 1. Control: successful isolated restart set

- run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_015448`
- base restart source:
  isolated successful `00300`
- bridge imports:
  present
- result:
  success

Meaning:

- 新的 transplant 脚本本身不会把成功谱系打坏

### 2. Full main-case restart transplant

- run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_015637`
- base restart source:
  main-case failing `00300`
- bridge imports:
  absent
- result:
  fail

Observed signature:

- entered `med_phases_restart_read`
- opened `cam.r/rh*.2005-12-31-00600.nc`
- rank 0 `SIGSEGV`

Meaning:

- 即使放到干净隔离目录里，主案例这套 `00300` restart 谱系仍然足以复现崩溃

### 3. Hybrid: only override `cam.r`

- run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_015909`
- base restart source:
  isolated successful `00300`
- override source:
  main-case failing `00300`
- override mode:
  `cam_r`
- bridge imports:
  present
- result:
  fail

Observed signature:

- entered `med_phases_restart_read`
- opened `cam.r/rh*.2005-12-31-00600.nc`
- rank 0 `SIGSEGV`

Meaning:

- **只替换主案例的 `cam.r.00300`，就足以把成功谱系打坏**

### 4. Hybrid: only override `cam history`

- run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_020046`
- base restart source:
  isolated successful `00300`
- override source:
  main-case failing `00300`
- override mode:
  `cam_hist`
  (`cam.rs + cam.rh*`)
- bridge imports:
  present
- result:
  success

Meaning:

- 主案例的 `cam.rs/rh*` 并不会单独触发这次 continuation 崩溃

### 5. Hybrid: only override `cpl.r`

- run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_020238`
- base restart source:
  isolated successful `00300`
- override source:
  main-case failing `00300`
- override mode:
  `cpl_r`
- bridge imports:
  present
- result:
  success

Meaning:

- 主案例的 `cpl.r.00300` 也不会单独触发这次 continuation 崩溃

## Difference Summary

这轮最关键的“区别”不是文件大小，而是**哪一类文件一替换就会把成功谱系打坏**：

1. `cam.r`
   - 主案例 `cam.r.00300` 单独覆盖：失败
   - 结论：当前主嫌疑已经收紧到 `cam.r.00300`

2. `cam.rs + cam.rh*`
   - 主案例 history restart 单独覆盖：成功
   - 结论：它们不是当前首要触发源

3. `cpl.r`
   - 主案例 `cpl.r.00300` 单独覆盖：成功
   - 结论：它也不是当前首要触发源

4. bridge imports
   - bridge import 存在与否都不是决定条件
   - 因为：
     - isolated control with imports: success
     - full main-case restart transplant without imports: fail
     - `cam.r`-only override with imports: fail

## File-Level Notes

三个关键 restart 文件在成功谱系和主案例谱系之间都不是同一个字节流：

- main-case `cam.r.00300` md5:
  `ba101147de723b67416f02008697e3da`
- isolated-success `cam.r.00300` md5:
  `5507fd0714b092851027108fcbd73ecd`

- main-case `cam.rs.00300` md5:
  `71692da6ca8e4bbee030787d28179077`
- isolated-success `cam.rs.00300` md5:
  `36baada8f0de6dbbf77ac0ab4578c881`

- main-case `cpl.r.00300` md5:
  `4ad90e01f20762bd0587b9d875edea32`
- isolated-success `cpl.r.00300` md5:
  `929b429fb823376c6d35f1a0215b984a`

但真正有诊断价值的是上面的 transplant matrix：

- 不是“文件不同”本身有意义
- 而是“只有 `cam.r` 的不同，会稳定地带来失败”

## Current Conclusion

截至这轮矩阵，长期 continuation 的 blocker 可以继续收紧成：

- **当前主案例 `00300` 谱系中的 `cam.r.2005-12-31-00300.nc`**

更准确地说：

- 问题已不再需要归因到 generic continuation
- 不再需要归因到 generic `edyn on`
- 不再需要归因到 bridge imports
- 也不再需要归因到 `cam history` 或 `cpl.r`

当前最值得继续做的下一步，是直接比较：

- 主案例失败 `cam.r.00300`
- 隔离成功 `cam.r.00300`

在状态变量层面到底差在哪里

到 2026-03-29 的后续 species-level 切片测试之后，这个结论又继续收紧成：

- **`cam.r.2005-12-31-00300.nc` 中 `ShortLivedSpecie` 的 species `12 = Op`**

## `cam.r` State Diagnostic

这一步也已经做了。工具和输出分别在：

- tool:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/tools/cam_restart_compare`
- source:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/tools/cam_restart_compare.c`
- report:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cam_r_compare_report_20260329.txt`

结论如下：

1. 两个 `cam.r.00300` 的 `ncdump -h` 头信息没有差异
   - 维度、变量集合、属性结构都一致
   - 所以问题不是 schema 损坏

2. 两个 `cam.r.00300` 在关键动力学字段里都没有 `NaN/Inf`
   - `U / V / DELP / PT / Q / PS / TEOUT` 的 `nan=0 inf=0`

3. 但主案例失败 `cam.r.00300` 在动力学主状态上有显著更强的极值
   - `U`:
     - failing main-case `max = 1.215e+03`
     - isolated success `max = 7.414e+02`
   - `V`:
     - failing main-case `min = -1.559e+03`
     - isolated success `min = -8.372e+02`
   - `PT`:
     - failing main-case `max = 2.573e+06`
     - isolated success `max = 1.357e+06`

4. 与之相对，质量/湿度/地表压这类量几乎一致
   - `DELP`:
     `max_abs_diff = 1.608e-07`
   - `Q`:
     `max_abs_diff = 1.121e-10`
   - `PS`:
     `max_abs_diff = 1.520e-06`

因此，这一步把诊断又往前推了一层：

- 当前 continuation 崩溃不只是“主案例 `cam.r` 会触发失败”
- 更像是**主案例 `cam.r` 中的动力学主状态，尤其 `U / V / PT`，已经偏离成功谱系很多**
- 这与前面回溯稳定落在 `FV dycore` 路径上是相互一致的

## `ShortLivedSpecie` Species-Level Isolation

在上面的变量级诊断之后，又继续把 `ShortLivedSpecie` 拆成 species block。

这一步的依据是：

- 当前 case 走的是 `pp_waccm_ma`
- 其 `slvd_lst(:14)` 在
  `/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/chemistry/pp_waccm_ma/mo_sim_dat.F90`
  里定义为：
  `e, HO2, N2D, N2p, NOp, Np, O1D, O2_1D, O2_1S, O2p, OH, Op, Op2D, Op2P`
- `ShortLivedSpecie(pbuf_01764,lat,lon)` 中
  `1764 = 14 * 126`
  所以每个 species block 正好占 `126` 个垂直层

对应工具与输出：

- species compare / patch tool source:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/tools/cam_shortlived_species_tool.c`
- compiled binary:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/tools/cam_shortlived_species_tool_caseenv`
- main-case vs successful-lineage compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_maincase_vs_success_20260329.txt`

这个 compare 的关键结果是：

- species `12 = Op` 的差异量级显著最大
- `max_abs_diff = 1.5647451938488177e-01`
- 其他 13 个 species 都明显更小

### `Op`-Only Sufficiency Test

- patched restart set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_shortlived_op_only_from_maincase_20260329h`
- verification compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_op_only_vs_success_20260329.txt`
- continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_op_only`
- result:
  fail

Observed signature:

- entered `med_phases_restart_read`
- opened `cam.r/rh*.2005-12-31-00600.nc`
- rank 0 `SIGSEGV`

Meaning:

- **只把 `ShortLivedSpecie` 里的 species `12 = Op` 单独换进去，就已经足以复现同一条 crash 链**

### `No-Op` Necessity Test

- patched restart set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_shortlived_no_op_from_maincase_20260329i`
- verification compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_no_op_vs_success_20260329.txt`
- continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_no_op`
- result:
  success

Observed signature:

- entered `med_phases_restart_read`
- opened all `cam.r/rh*.2005-12-31-00600.nc`
- opened `cam.rs.2005-12-31-00600.nc`
- `med_finalize max rss=5245419520.0 MB`
- `exit_status 0`

Meaning:

- **把另外 13 个 short-lived species 都换成主案例值，但显式保留成功谱系的 `Op`，continuation 仍能成功到 `00600`**

### Main-Case Minimal Repair Test

- patched restart set:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/maincase_op_repaired_from_success_20260329j`
- verification compare:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_maincase_repaired_vs_maincase_20260329.txt`
- continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_maincase_op_repaired`
- result:
  success

Observed signature:

- relative to the original main-case `cam.r.00300`, only species `12 = Op`
  differs
- entered `med_phases_restart_read`
- opened `cam.r/rh*.2005-12-31-00600.nc`
- opened `cam.rs.2005-12-31-00600.nc`
- `med_finalize max rss=5245644800.0 MB`
- `exit_status 0`

Meaning:

- **在原始主案例失败谱系里，只修 `ShortLivedSpecie -> Op`，就已经足以把 `00300 -> 00600` continuation 救活**

### Repaired-Lineage Follow-On Continuation Test

- restart source:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_maincase_op_repaired/run`
- continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00600_20260329_maincase_op_repaired_step2`
- result:
  success

Observed signature:

- used `rpointer.cam = 00600`
- entered `med_phases_restart_read`
- opened `cam.r.2005-12-31-00900.nc`
- opened `cam.rs.2005-12-31-00900.nc`
- `med_finalize max rss=5245648896.0 MB`
- `exit_status 0`

Meaning:

- **`ShortLivedSpecie -> Op` 最小修复不是只救活一次 `00300 -> 00600`**
- **同一条修复后的主案例谱系已经继续稳定跑过 `00600 -> 00900`**

### Repaired-Lineage Third Continuation Test

- restart source:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00600_20260329_maincase_op_repaired_step2/run`
- continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00900_20260329_maincase_op_repaired_step3`
- result:
  success

Observed signature:

- used `rpointer.cam = 00900`
- entered `med_phases_restart_read`
- opened `cam.r.2005-12-31-01200.nc`
- opened `cam.rs.2005-12-31-01200.nc`
- `med_finalize max rss=5245452288.0 MB`
- `exit_status 0`

Meaning:

- **同一条最小修复后的主案例谱系已经连续成功到 `01200`**
- **`Op` 最小修复当前表现为可持续 continuation 修复，而不是一次性补丁**

### Repaired-Lineage Fourth Continuation Test

- restart source:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00900_20260329_maincase_op_repaired_step3/run`
- continuation run root:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01200_20260329_maincase_op_repaired_step4`
- result:
  success

Observed signature:

- used `rpointer.cam = 01200`
- entered `med_phases_restart_read`
- opened `cam.r.2005-12-31-01500.nc`
- opened `cam.rs.2005-12-31-01500.nc`
- `med_finalize max rss=5246791680.0 MB`
- `exit_status 0`

Meaning:

- **同一条最小修复后的主案例谱系已经连续成功到 `01500`**
- **当前证据说明这个 `Op` 最小修复至少已经跨过四段 true continuation**

### Repaired-Lineage Aggressive Chain Test

- chain tag:
  `20260329_maincase_op_repaired_chainA`
- chained run roots:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01500_20260329_maincase_op_repaired_chainA`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-01800_20260329_maincase_op_repaired_chainA`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-02100_20260329_maincase_op_repaired_chainA`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-02400_20260329_maincase_op_repaired_chainA`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-02700_20260329_maincase_op_repaired_chainA`
- result:
  all success

Observed signature:

- each segment completed with `exit_status 0`
- the last segment wrote `cam.r.2005-12-31-03000.nc`
- the last segment wrote `cam.rs.2005-12-31-03000.nc`
- the last segment exited via `med_finalize max rss=5245898752.0 MB`

Meaning:

- **同一条 `ShortLivedSpecie -> Op` 最小修复后的主案例谱系，已经从 `00300` 连续稳定推进到 `03000`**
- **当前它已经不只是“最小修复候选”，而是最强的可操作工程修复路径**

## Updated Conclusion

到这一步为止，当前最强的工程结论已经不再只是：

- `ShortLivedSpecie` 是最小已知触发体

而是更进一步：

- **`ShortLivedSpecie` 中 species `12 = Op` 既是已验证的充分触发体，也是当前最强的必要触发候选**
- **在原始主案例失败谱系里，只替换 `Op` 就能完成一次最小修复**
- **同一条最小修复后的主案例谱系已经连续成功到 `03000`**
- 就当前证据强度而言，生产谱系 `00300 -> 00600` continuation 的决定性 blocker，
  已经可以压缩到
  `cam.r.2005-12-31-00300.nc -> ShortLivedSpecie -> Op`

补充说明：

- 现在还多了一条更强的 compare 证据：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cam_r_compare_all_maincase_vs_maincase_op_repaired_20260329.txt`
- 这份全变量 compare 表明，相对原始主案例 `cam.r.00300`，
  修复版 `cam.r.00300` 的差异变量仍然只有 `ShortLivedSpecie`
- `2026-03-30` 的 pre-`00300` 窗口 compare 又把时间定位前推了一步：
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/rh0_compare_maincase_vs_success_00000_20260330.txt`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/rh0_compare_maincase_vs_success_00300_20260330.txt`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/rh2_compare_maincase_vs_success_00300_20260330.txt`
- 这三份 compare 说明：
  - `00000` 时刻两条 startup 谱系在 `Op / UI / VI / WI / TElec / TIon`
    上仍完全一致
  - `00300` 时刻这些 ionosphere-facing 字段已经全部明显分叉
  - 因而 `ShortLivedSpecie -> Op` 的写坏窗口已收紧到第一次 startup 的
    `00000 -> 00300`
- 结合日志与文件时间戳，还可以给出一个当前最强的工程推断：
  失败主案例 `cam.r.00300` 很可能来自旧的高-`epot` clamp startup 谱系，
  而不是后来那条 `~12.122 kV` 的温和 startup 谱系

## Causal Startup Replay

为了把上面这条“旧高-`epot` startup 谱系”推断继续推进到更接近因果验证，
`2026-03-30` 又做了两条隔离 startup replay。

### 1. Replay `169.702 -> 150.000`

isolated startup root:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/causal_replays/causal_startup_169702_20260330a`

startup signature:

- `d_pie_set_external_epot: input/limited absmax      169.702 ->      150.000`

state-compare outcome:

- replayed `00300` is already materially closer to the failing main-case than
  to the successful isolated seed
- but it is still not close enough to be considered the same restart lineage

continuation outcome:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260330_causal169702_from00300`
- wrote the `00600` restart set
- then failed by
  `te_map: Lagrangian levels are crossing`
  rather than the original `rank 0 SIGSEGV`

meaning:

- `169.702` replay proves that a strong clamped startup can already push the
  system into the same unstable neighborhood
- but it is not yet the closest known replay of the original failing lineage

### 2. Replay `178.793 -> 150.000`

isolated startup root:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/causal_replays/causal_startup_178793_20260330a`

startup signature:

- `d_pie_set_external_epot: input/limited absmax      178.793 ->      150.000`

state-compare outcome:

- relative to the original failing main-case `00300`, this replay is
  dramatically closer than the `169.702` replay
- supporting compares:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/shortlived_species_compare_maincase_vs_causal178793_20260330.txt`
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/rh0_compare_maincase_vs_causal178793_20260330.txt`
- key numbers:
  - `ShortLivedSpecie -> Op`:
    `max_abs = 1.75864739934566972e-03`
  - `cam.rh0 Op`:
    `max_abs_diff = 1.0256851671754386e-03`
  - `cam.rh0 UI`:
    `max_abs_diff = 6.6820859687673419e+01`
  - `cam.rh0 VI`:
    `max_abs_diff = 1.8508794439846042e+01`
  - `cam.rh0 WI`:
    `max_abs_diff = 6.1992805641979132e+00`

continuation outcome:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260330_causal178793_from00300`
- entered `med_phases_restart_read`
- wrote the `00600` restart set
- then reproduced the same failure class as the original main-case:
  `Program received signal SIGSEGV`
  and `prterun ... exited on signal 11`

meaning:

- this is the strongest evidence so far that the original failing
  `cam.r.00300 -> ShortLivedSpecie -> Op` state can be regenerated by replaying
  a sufficiently similar high-`epot` clamped startup lineage
- in other words, the earlier “old high-`epot` startup lineage” hypothesis is
  no longer just a loose inference from timestamps; it now has a concrete
  replay that reproduces both the `00300` state geometry and the continuation
  `SIGSEGV`

## Repair-Oriented Patch Attempts

为了把相关性继续推进到因果验证，又做了两轮 `cam.r` 定向补丁：

### 1. Patch `U / V / PT`

patched restart source:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/maincase_camr_uvpt_from_isolated_20260329a`

continuation run root:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_021221`

result:

- 仍然失败
- 仍然是写出 `00600` restart 后，`rank 0 SIGSEGV`

meaning:

- `U / V / PT` 的确是强嫌疑
- 但它们**单独还不足以修复**这次 continuation 崩溃

### 2. Patch `U / V / PT / Optm1 / DTCORE / DUCORE / DVCORE`

patched restart source:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/maincase_camr_dyncore_from_isolated_20260329a`

continuation run root:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_021429`

result:

- 仍然失败
- 仍然是写出 `00600` restart 后，`rank 0 SIGSEGV`

meaning:

- 问题虽然明显在主案例 `cam.r` 的动力学状态侧
- 但当前还**不能**把根因压缩到这一小组显著偏离字段
- 更像是：
  - 更大范围的 dycore-related state 组合
  - 或者 `cam.r` 里更广义的内部一致性条件

## Updated Working Diagnosis

截至目前，最稳妥的工程判断是：

- 主案例 `cam.r.00300` 是 continuation 崩溃的必要触发体
- `cam history` 和 `cpl.r` 不是首要触发体
- 主案例 `cam.r` 里最显著偏离成功谱系的是动力学相关状态
- 但只修补一小组明显偏离的动力学变量，还不足以恢复 continuation

所以当前“还差一步”的位置是：

- 已经从“哪个文件有问题”收紧到了 `cam.r`
- 但还没有最终收紧到“哪几个变量单独决定了失败”

## `ShortLivedSpecie` Single-Variable Isolation

随后又做了更细一层的变量隔离。

先比较两组已经跑完 continuation 的 patched restart set：

1. failing:
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_all3_plus_chem_from_maincase_20260329d`
2. successful:
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_all3_plus_chem_no_short_from_maincase_20260329e`

它们的 continuation 结果分别是：

- `all3_plus_chem`: fail
- `all3_plus_chem_no_short`: success

而用 `cam_restart_compare_all` 对两份 `cam.r.00300` 逐变量比较后，
唯一差异变量只有：

- `ShortLivedSpecie`

这说明：

- 这两个 patched `cam.r` 在当前诊断分辨率下，
  差别已经压缩到单变量

在此基础上，又构造了一个新的单变量 patched set：

- new patched restart source:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/isolated_camr_shortlived_only_from_maincase_20260329g`

构造方法是：

- 以成功的
  `isolated_camr_all3_plus_chem_no_short_from_maincase_20260329e`
  为底
- 只从 failing main-case `cam.r.00300` 中替换
  `ShortLivedSpecie`

对应 continuation run：

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue/restart_continue_2005-12-31-00300_20260329_shortlived_only`

结果：

- fail
- 继续进入 `med_phases_restart_read`
- 继续写出 `cam.r/rh*.2005-12-31-00600.nc`
- 然后仍然复现同一条 `rank 0 SIGSEGV`

因此，这一步已经把结论从：

- `cam.r` 有问题

推进到：

- **`ShortLivedSpecie` 单独就足以把成功谱系打坏**

结合前面那组“只差 `ShortLivedSpecie` 就一成一败”的配对，
当前最强诊断可以写成：

- 当前主案例 `00300 -> 00600` continuation crash 的最小已知触发体，
  就是 `cam.r.2005-12-31-00300.nc` 中的 `ShortLivedSpecie`
