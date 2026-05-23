# MAGE-WACCMX NSRHS Unfolding Validation

日期：2026-03-27

## 结论

在当前 `NSRHS` 工作点下，bridge 默认不再需要
`mirror_south_folded_source_to_north`。

更准确地说：

- `raw/no-mirror` 反馈包已经可以被 `step2 Kaiju` 两个半球同时摄入
- 与此前 `mirror` 参考相比，`CPCP` 在当前输出精度下没有可见差异
- `mirror` 的主要效果，是把北半球 `NSRHS` 人工抬高到和南半球完全相同
- 因此，`mirror` 现在应降级为 legacy/debug unfolding 选项，而不是默认路径

## 关键证据

### 1. raw/no-mirror probe

- 作业：`4728246`
- 结果目录：
  [raw_geo_nomirror_4p18e5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_raw/raw_geo_nomirror_4p18e5)
- `step2` 合同：
  [waccmx_voltron_contract.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_raw/raw_geo_nomirror_4p18e5/step2_kaiju_feedback/waccmx_voltron_contract.txt)

raw/no-mirror 的 `step2` 合同显示：

- H1 `NSRHS absmax = 5.4874E+07 arb`
- H2 `NSRHS absmax = 5.5451E+07 arb`

说明 raw 包并不是“北半球全零”，而是南北半球都已真实非零摄入。

### 2. mirror reference

- 参考目录：
  [nsrhs_cycle_20260327d](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d)
- `step2` 合同：
  [waccmx_voltron_contract.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/step2_kaiju_feedback_mirror/waccmx_voltron_contract.txt)

mirror 参考的 `step2` 合同显示：

- H1 `NSRHS absmax = 5.5451E+07 arb`
- H2 `NSRHS absmax = 5.5451E+07 arb`

也就是 mirror 做的事情，主要是把北半球抬到和南半球完全相同。

### 3. CPCP 对照

raw/no-mirror:

- [launcher.log](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_raw/raw_geo_nomirror_4p18e5/step2_kaiju_feedback/launcher.log)
- `CPCP = 14.882 18.189 [kV, N/S]`

mirror:

- [launcher.log](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/step2_kaiju_feedback_mirror/launcher.log)
- `CPCP = 14.882 18.189 [kV, N/S]`

在当前输出精度下，两者没有可见差异。

## 定量差异

按 `step2` 合同里的 `NSRHS absmax`：

- raw 北/南比值：`0.989594`
- raw 北半球相对南半球低约：`1.041%`
- mirror 相对 raw 北半球抬高约：`1.051%`

这说明 `mirror` 并没有改变当前工作点的主响应量级，只是在北半球做了一个约 `1%` 的人工补齐。

## 当前建议

- bridge 默认 `NSRHS_UNFOLDING` 改为 `none`
- `mirror_south_folded_source_to_north` 保留为 legacy/debug 选项
- 后续若要继续改 `NSRHS` 物理语义，应优先围绕：
  - `solver/coupler` 尺度
  - 符号
  - `TIEGCM gnsrhs` 对齐

而不再把 `mirror` 是否默认启用当成主问题。
