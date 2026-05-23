# MAGE-WACCMX Outflow Payload Driver

这个 driver 是隔离 `MAGE` 原型里最轻量的一层 adaptor 出口。

它不重新做物理处理，也不改现有 ingest/adaptor 合同，只做一件事：

- 读取现有 ingest 包里的 `return_outflow_north` 和 `return_outflow_south`
- 按固定顺序写出 `IMAG/MHD` 风格的 5 标量 payload

固定顺序是：

`[im_d_ring, im_p_ring, im_d_cold, im_p_cold, im_tscl]`

## 入口

- driver: [waccmx_stub_outflow_payloadx.F90](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/src/drivers/waccmx_stub_outflow_payloadx.F90)
- case: [WACCMX_STUB_OUTFLOW_PAYLOAD_CASE.xml](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/WACCMX_STUB_OUTFLOW_PAYLOAD_CASE.xml)

## 读取对象

这个 driver 直接读取 ingest 包里的两个 return sidecar 组：

- `/return_outflow_north`
- `/return_outflow_south`

实现上它用的是原型现有的 `ioH5` 读层，而不是 adaptor stub 的对象恢复层。

## 输出

默认会写两个文件：

- payload: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_outflow_payload.txt`
- report: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_proto/tmp/waccmx_stub_outflow_payload_report.md`

payload 的格式是简单定序文本：

```text
# IMAG/MHD-style outflow payload
# order: im_d_ring im_p_ring im_d_cold im_p_cold im_tscl
north <5 ordered scalars>
south <5 ordered scalars>
```

## 目的

这层的意义是把较重的 ingest/adaptor 合同，压缩成一个磁层侧更容易消费的极简 outflow sidecar。

这样后面不管你接的是：

- `IMAG`
- `MHD`
- 还是另一个轻量耦合 stub

都可以先围绕这 10 个标量做最小回路验证，而不需要整包重读全部 `aurora/edyn/state` 数据。
