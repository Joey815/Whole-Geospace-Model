# MAGE-WACCMX Neutral-Dynamo 耦合方案

## 结论

`neutral-dynamo` 不应该继续按“电导加权中性风”去耦合。  
与 `MAGE-TIEGCM` 思路最一致、并且在你当前 `WACCM-X` 代码里最可落地的方案是：

- `WACCM-X` 侧直接导出 electrodynamo 方程的 **2D dynamo RHS**，也就是本地代码里已经存在的 `rhs` / `rhs_glb`
- 文件桥继续把这个量命名为 `neutral_rhs`
- `Kaiju/REMIX` 侧不要再把它当 `NEUTRAL_WIND(cm/s)` 理解，而是新增一个显式变量，例如 `NEUTRAL_DYNAMO_RHS` 或 `NSRHS`
- `mixsolver` 里把这个量作为与 `FAC` 并列的 GEO-side electrodynamic forcing 项加入势方程右端

这条路线的优点是：

- 物理语义与 `TIEGCM` 的 `nsrhs/gnsrhs` 最接近
- `WACCM-X` 本地代码已经算出了这个量，工程代价低
- 不再把“风”误当成“dynamo source term”

## 2026-03-27 校准结果

这条路线在概念上成立，但最新一次同 forcing 校准说明：

- `WACCM-X edynamo rhs` 不能直接替代当前 bridge 里的 `neutral_rhs proxy`
- 当前 `edyn_rhs` 与 proxy 的平均 `absmax` 比约为 `804`
- 4 个 MPI rank 的平均相关系数只有 `0.0115`
- 也就是说，`edyn_rhs` 不是“同一个量乘一个常数”这种关系

对应记录见：

- [MAGE_WACCMX_NEUTRAL_RHS_CALIBRATION_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NEUTRAL_RHS_CALIBRATION_20260327.md)

因此，当前最合理的工程路径不是：

- 直接把 `edyn_rhs` 塞进现有 `NEUTRAL_WIND(cm/s)` 槽位

而是：

- 保留当前 proxy 作为临时桥
- 新增显式 `NEUTRAL_DYNAMO_RHS` / `NSRHS` 变量
- 再继续做 `rhs <-> nsrhs/gnsrhs` 的符号、缩放和 GEO 投影校准

## 为什么当前 proxy 不够

当前真实桥里 `neutral_rhs` 的定义是：

- `Pedersen` 电导加权的纬向中性风
- 再从 `m/s` 转为 `cm/s`

这个做法只能算“数据通路已经打通”的一阶 proxy，不是最终物理闭合。原因是：

- 它只用了纬向风 `u`
- 没有显式包含经向风 `v`
- 没有包含 `Hall` 项
- 没有包含 Apex/Quasi-Dipole 几何因子
- 没有包含由 `rim1/rim2` 导出的电流连续性约束
- 它本质上是“风的代表量”，不是“电势方程 RHS/source term”

## MAGE-TIEGCM 里真正接近目标的量是什么

先说清楚一点：在你当前 `MAGE-TIEGCM` 主线里，GEO 导出其实没有正式打开：

- `nmixoutgeo = 0`
- 见 [mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F)

但 `TIEGCM` 内部已经明确算了 neutral-dynamo 相关量：

- `mage_ucurrent` 的注释直接写明，它计算的是  
  `height-integrated neutral wind generated field-aligned current (dynamo)`
- 返回量是 `nsrhs`
- 然后又经 `mag2geo_2d` 映射为 `gnsrhs`

关键代码：

- [mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F)
  - `This subroutine calculate height-integrated neutral wind generated field-aligned current`
  - `RETURN VALUE: nsrhs`
- [pdynamo.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/pdynamo.F)
  - `call mage_ucurrent(..., nsrhs)`
  - `call mag2geo_2d(nsrhs, gnsrhs, ..., 'NSRHS')`

而 `nsrhs` 的形成方式，不是对风做平均，而是：

- 先用场线积分得到 `rim1/rim2`
- 再对 `rim1/rim2` 做经纬向微分
- 再按参考半径做缩放

也就是说，`TIEGCM` 想耦出去的量，本质上是：

- **neutral-wind-driven current continuity / PDE RHS**

而不是：

- 原始中性风
- 或任意一维风 proxy

## 公开资料和 WACCM-X 本地代码是否支持这条思路

支持，而且支持得很强。

### 1. 公开资料

`WACCM-X 2.0` 官方科学文档明确说明：

- `WACCM-X` 电动力学改编自 `TIE-GCM`
- 在 `modified magnetic apex coordinates` 中求电势
- 使用 `Richmond (1995)` 的 `field-line integrated quantities`
- 风驱动项是 `K^D`
- 电流连续性把这些风驱动电流转成电势方程 RHS

官方文档：

- `Liu et al., 2018, WACCM-X 2.0`
  - 官方 PDF: <https://www2.hao.ucar.edu/sites/default/files/2021-12/LiuJames2018.pdf>
- `WaccmX2science.pdf`
  - 官方 PDF: <https://www2.hao.ucar.edu/sites/default/files/2021-12/WaccmX2science.pdf>
- `Richmond 1995`
  - <https://www.jstage.jst.go.jp/article/jgg1949/47/2/47_2_191/_article>

公开资料里最关键的两点是：

- `WACCM-X` 的 solver 不是直接用风，而是用 `field-line integrated quantities`
- `K_m^D` 的散度和 `J_mr` 通过 current continuity 进入电势方程 RHS

另外，NCAR 官方 `SIMA` 更新已经说明，新一代 `WACCM-X` 正在往 **field-line based ionospheric electric dynamo** 方向演进，这会让磁层耦合更物理一致：

- <https://sima.ucar.edu/news/2025/geospace-updates-58>

### 2. 你本地 WACCM-X 代码

你本地 `CESM/WACCM-X` 代码实际上已经把这些量算出来了。

在 [edynamo.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90) 里：

- `rim1/rim2` 已由 `sigmaP/sigmaH`、`ue1/ue2` 和几何因子场线积分得到
- 注释已经直接把它们解释为 `K_(m phi)^D` / `K_(m lam)^D`
- `rhspde()` 又由 `rim1/rim2` 计算出 `rhs`
- `gather_edyn()` 再组装为全局 `rhs_glb`

这意味着：

- `WACCM-X` 已经有一个和 `TIEGCM nsrhs` 非常接近的内部量
- 只是当前桥没有把它导出去

## 推荐方案

### 推荐方案 A：直接导出 WACCM-X 的 dynamo RHS

这是我推荐你采用的正式方案。

#### WACCM-X 侧

1. 保留现在 `SIGMAP/SIGMAH` 的反馈导出
2. 把当前 `mage_waccmx_feedback_stub.F90` 里的 `neutral_rhs` 定义从“Pedersen 加权纬向风”改成：
   - `edynamo` 的 `rhs` 或 `rhs_glb`
3. 优先使用局地磁网格 `rhs(mlon0:mlon1,mlat0:mlat1)`，再通过 `regrid_mag2phys_2d` 映射到 physics columns
4. 最终仍然写到每个 rank 的 feedback 文件第 6 列，字段名继续叫 `neutral_rhs`

这样做的优点：

- 不需要重新发明 proxy
- 不需要自己重新推导 dynamo 方程
- 与 `TIEGCM nsrhs` 的形成机制最接近
- 可以复用现有文件桥格式

#### Kaiju/MAGE 侧

不要再继续把这个量塞进 `NEUTRAL_WIND(cm/s)` 槽位当成最终方案。  
更好的做法是：

1. 在 `mixdefs.F90` 新增一个显式变量，例如：
   - `NEUTRAL_DYNAMO_RHS`
   - 或 `NSRHS`
2. 在 `mixio.F90` 给它单独名字和单位
3. 在 `waccmx_stub_backend.F90` 或后续正式 backend 中，把 GEO 输入指向这个新变量
4. 在 `mixsolver.F90` 里，把它作为与 `FAC` 并列的 RHS forcing 项加入势方程

这样物理语义才是对的：

- `FAC` 是磁层/电流系统 forcing
- `NEUTRAL_DYNAMO_RHS` 是热层中性风发电机 forcing

### 推荐方案 B：兼容过渡方案

如果你短期内不想扩 `Kaiju` 变量表，也可以做一个过渡版：

- `WACCM-X` 还是导出真实 `rhs`
- 但桥接阶段先继续把它塞到 `NEUTRAL_WIND` 槽位
- `mixsolver` 中保留当前“把 GEO 量乘一个系数注入 RHS”的做法

这条路工程上能跑，但我不建议把它当最终版本。主要问题是：

- 单位不自然
- 变量名误导
- 容易和真正中性风语义混淆

## 为什么这是“可行方案”

因为它不需要你重新建设大半套耦合框架，现成条件已经满足：

- `TIEGCM` 侧目标语义已经很明确：`nsrhs/gnsrhs`
- `WACCM-X` 侧已经有 `rim1/rim2 -> rhs -> rhs_glb`
- 文件桥已经有第 6 列 `neutral_rhs`
- `Kaiju` 侧 GEO 输入通道已经打开过，并验证过能收 `neutral_rhs`

所以从工程量上看，真正缺的只是：

1. `WACCM-X` feedback stub 改成导出 `rhs`
2. `Kaiju` 新增一个显式的 `NEUTRAL_DYNAMO_RHS` 变量槽
3. `mixsolver` 用这个量替代当前 proxy 注入

## 不推荐的方案

不推荐把最终方案定成：

- `Pedersen` 电导加权纬向风
- `Pedersen/Hall` 加权风速
- 单独的 `u` 或 `v`
- 风场的简单层平均

这些量都可以做临时 proxy，但都不等价于 `TIEGCM` 的 `nsrhs/gnsrhs`。

## 建议的实施顺序

1. `WACCM-X` feedback stub 从加权风切换到 `rhs`
2. 保持文件桥格式不变，先验证 `neutral_rhs` 非零且稳定
3. `Kaiju` 新增 `NEUTRAL_DYNAMO_RHS` 变量
4. `mixsolver` 用新变量替换对 `NEUTRAL_WIND` 的临时重载
5. 回归测试 `SIGMAP/SIGMAH/neutral_rhs` 三者闭环

## 一句话结论

最可行、最接近 `MAGE-TIEGCM` 原始思路的方案，不是继续回传“风”，而是：

**让 `WACCM-X` 直接导出它已经算好的 electrodynamo PDE RHS (`rhs/rhs_glb`)，并在 `Kaiju` 侧把它作为一个显式的 `NEUTRAL_DYNAMO_RHS` 变量接入 REMIX 势方程。**
