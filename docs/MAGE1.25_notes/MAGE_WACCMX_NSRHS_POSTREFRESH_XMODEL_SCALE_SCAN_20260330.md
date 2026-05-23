# MAGE-WACCMX `NSRHS` Postrefresh Crossmodel Scale Scan

日期：2026-03-30

## 结论

在最新 `postrefresh` 非零 `geo_sidecar` 源场上，

- `solver_to_tiegcm_coupler_crossmodel`

这条路线仍然稳定可用，而且旧的工作点判断没有失效：

- `KAIJU_NSRHS_SCALE = 4.18378699684e5`

仍然是当前三点矩阵里最平衡的工作点。

更具体地说：

- `1e5` 已经有可见响应，但偏弱
- `4.18e5` 响应清晰且仍然受控
- `1e6` 响应明显偏强

## 背景

这次扫描不是为了再证明 `NSRHS` 链路能通。

前一步已经确认：

- `CESM -> bridge -> Kaiju`

的 `geo_sidecar` 非零链路已经在 `postrefresh` 后真正打通。

这次要回答的是：

- 在最新 `postrefresh` 源场下，
- 旧的 `crossmodel` 工作点是否仍然有效。

## 使用的源场

反馈包：

- [postrefresh_coupler_crossmodel.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_transform_tests_20260330a/postrefresh_coupler_crossmodel.h5)

其中：

- `nsrhs_source = nsrhs_geo_sidecar`
- `nsrhs_transform = solver_to_tiegcm_coupler_crossmodel`
- `feedback_geo_north/neutral_rhs absmax = 1.2752501100279053e-06`
- `feedback_geo_south/neutral_rhs absmax = 1.1901544967421317e-06`

## 运行目录

三点矩阵总目录：

- [postrefresh_crossmodel_scale_scan_20260330b](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b)

三组运行：

- [postrefresh_xmodel_1e5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_1e5)
- [postrefresh_xmodel_4p18e5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_4p18e5)
- [postrefresh_xmodel_1e6](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_1e6)

## 结果

### 1. 合同中的 `NSRHS absmax`

三个点都稳定完成，而且合同里的 `NSRHS absmax` 完全一致：

| Scale | H1 `NSRHS absmax` | H2 `NSRHS absmax` |
| --- | ---: | ---: |
| `1e5` | `1.2753e-06` | `1.1902e-06` |
| `4.18378699684e5` | `1.2753e-06` | `1.1902e-06` |
| `1e6` | `1.2753e-06` | `1.1902e-06` |

对应 summary：

- [1e5 summary](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_1e5/nsrhs_scale_probe_summary.txt)
- [4.18e5 summary](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_4p18e5/nsrhs_scale_probe_summary.txt)
- [1e6 summary](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_1e6/nsrhs_scale_probe_summary.txt)

这不是异常，而是当前 `phase2` 实现的预期行为：

- 合同里打印的是输入场本身
- `KAIJU_NSRHS_SCALE` 真正影响的是求解器中的注入强度

## 2. `POT` 响应

真正区分三个尺度点的是 `POT` 响应：

| Scale | North `POT min/max` (kV) | South `POT min/max` (kV) |
| --- | --- | --- |
| `1e5` | `-12.2349 / 11.4050` | `-15.7811 / 14.0827` |
| `4.18378699684e5` | `-9.39842 / 18.1181` | `-15.4908 / 15.3819` |
| `1e6` | `-14.1217 / 35.8689` | `-24.2196 / 17.9971` |

对应 exchange：

- [1e5 exchange](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_1e5/step2_kaiju_feedback/waccmx_voltron_exchange.md)
- [4.18e5 exchange](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_4p18e5/step2_kaiju_feedback/waccmx_voltron_exchange.md)
- [1e6 exchange](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/postrefresh_crossmodel_scale_scan_20260330b/postrefresh_xmodel_1e6/step2_kaiju_feedback/waccmx_voltron_exchange.md)

## 解释

这三点的意义很清楚：

- `1e5`
  - 相比控制态已有响应
  - 但偏保守，仍接近弱扰动区
- `4.18e5`
  - 响应已经明显
  - 但还没有进入 `1e6` 那种过强放大量级
- `1e6`
  - 数值上依然可跑
  - 但北半球 `POT` 已到 `35.9 kV`，明显偏强

## 当前建议

因此，`postrefresh` 之后的 `crossmodel` 基线建议正式收紧为：

1. 默认实验工作点仍用 `KAIJU_NSRHS_SCALE = 4.18378699684e5`
2. `1e5` 保留为偏弱参考点
3. `1e6` 保留为偏强参考点

## 说明

这些短 probe 的 `launcher.log` 末尾会看到 `SIGTERM / forrtl error 78`。

这是脚本在拿到：

- `contract`
- `exchange`
- `forward package`

后主动结束 `voltron.x`，不是数值崩溃。
