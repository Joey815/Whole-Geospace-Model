## MAGE-WACCMX `neutral_rhs` Calibration on 2026-03-27

### Goal

Check whether `WACCM-X edynamo rhs` can directly replace the current `neutral_rhs` proxy in the existing `MAGE <-> WACCM-X` file bridge.

Compared two modes under the same `MAGE -> WACCM-X` import forcing:

- `proxy`
  - current bridge definition
  - Pedersen-conductance-weighted zonal neutral wind
- `edyn_rhs`
  - direct use of `WACCM-X edynamo rhs`, regridded from magnetic grid to physics columns

### Runs

Output root:

- [calibration_neutral_rhs_20260327d](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327d)

Proxy mode:

- [manual_cesm_proxy.log](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327d/proxy/manual_cesm_proxy.log)
- [mage_waccmx_feedback_rank000000.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327d/proxy/mage_waccmx_feedback_rank000000.txt)
- [mage_waccmx_feedback_rank000000_summary.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327d/proxy/mage_waccmx_feedback_rank000000_summary.txt)

`edyn_rhs` mode:

- [manual_cesm_edyn_rhs.log](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327d/edyn_rhs/manual_cesm_edyn_rhs.log)
- [mage_waccmx_feedback_rank000000.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327d/edyn_rhs/mage_waccmx_feedback_rank000000.txt)
- [mage_waccmx_feedback_rank000000_summary.txt](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327d/edyn_rhs/mage_waccmx_feedback_rank000000_summary.txt)

### Key Results

Per-rank summary averages over 4 MPI ranks:

- `proxy_absmax`: `4.207716e+04`
- `edyn_rhs_absmax`: `3.384770e+07`
- `edyn_rhs / proxy` absmax ratio: `804.42`
- mean `proxy_rhs_corr`: `0.0115`

Whole-field statistics over all `13852` local-column values:

- `proxy`
  - nonzero fraction: `1.000000`
  - mean: `-1.825279e+03`
  - mean absolute value: `7.328110e+03`
- `edyn_rhs`
  - nonzero fraction: `0.477260`
  - mean: `3.885909e+05`
  - mean absolute value: `1.269952e+06`

Rank-0 sample:

- proxy row 2 `neutral_rhs`: `1.4996407507422578E+03`
- `edyn_rhs` row 2 `neutral_rhs`: `6.7516685131346630E+06`

Rank-0 overlap diagnostics:

- overlapping nonzero points: `1702`
- `edyn_rhs == 0` points: `1754`
- ratio range `edyn_rhs/proxy`: `-4.254869e+05` to `1.851645e+05`
- ratio mean on overlap: `-4.758057e+02`

### Interpretation

`WACCM-X edynamo rhs` is not a simple rescaling of the current proxy.

Main evidence:

- magnitude is about `8e2` larger in absmax on average
- pointwise correlation with the proxy is near zero overall
- sign changes are mixed instead of a consistent single factor
- `edyn_rhs` contains large zero/nonzero structure that the proxy does not

So the current calibration does **not** support the statement:

- "`edyn_rhs` can be dropped into the current `NEUTRAL_WIND` slot as-is"

### Engineering Conclusion

What is supported:

- `WACCM-X edynamo rhs` is a plausible **candidate physical source term** for a future `neutral-dynamo` coupling variable.
- It is more physically aligned with `TIEGCM nsrhs/gnsrhs` than the current weighted-wind proxy.

What is not supported:

- direct replacement of the existing `neutral_rhs` proxy in the current `Kaiju` `NEUTRAL_WIND` slot
- interpreting `edyn_rhs` as the same quantity with the same units as the current proxy

### Recommended Next Step

Do not overwrite the current production bridge variable with raw `edyn_rhs`.

Instead:

1. Keep the current proxy only as a temporary bridge variable for the existing `NEUTRAL_WIND` slot.
2. Introduce a new explicit `Kaiju` variable, e.g. `NEUTRAL_DYNAMO_RHS` or `NSRHS`.
3. Feed `WACCM-X edynamo rhs` into that new variable.
4. Perform a second calibration pass against `TIEGCM nsrhs/gnsrhs` for:
   - sign
   - normalization
   - units
   - GEO projection / hemisphere folding

### Code Paths Used

WACCM-X source:

- [edynamo.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90)
- [mage_waccmx_feedback_stub.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/mage_waccmx_feedback_stub.F90)

Bridge runner:

- [run_neutral_rhs_calibration.sh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_neutral_rhs_calibration.sh)

Related design note:

- [MAGE_WACCMX_NEUTRAL_DYNAMO_COUPLING_PLAN_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NEUTRAL_DYNAMO_COUPLING_PLAN_CN.md)
