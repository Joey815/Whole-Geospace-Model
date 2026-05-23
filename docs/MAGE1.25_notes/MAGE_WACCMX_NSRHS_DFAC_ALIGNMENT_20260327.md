# NSRHS Dfac Alignment Summary

## Constants

- `WACCM_DFAC_M = 6.468220000e+06 m`
- `TIEGCM_DFAC_M = 6.461220000e+06 m`

## Transform Factors

- `solver_to_tiegcm_coupler_like = -2.390179042947e-14`
- `solver_to_tiegcm_coupler_crossmodel = -2.392768531201e-14`
- `relative_difference = 1.083386728822e-03`

## Package Absmax

| Package | North absmax | South absmax |
| --- | ---: | ---: |
| mirror solver-scale | 5.545069933882e+07 | 5.545069933882e+07 |
| coupler-like | 1.325370994764e-06 | 1.325370994764e-06 |
| coupler-crossmodel | 1.326806884110e-06 | 1.326806884110e-06 |

## Interpretation

- `coupler-like` uses `-1 / WACCM_DFAC^2`.
- `coupler-crossmodel` uses `-1 / (WACCM_DFAC * TIEGCM_DFAC)`.
- The difference between these two transforms is small because the two models use very similar `r0` values.
- Therefore, current uncertainty is dominated much more by folded-source semantics and GEO projection than by the `WACCM_DFAC` vs `TIEGCM_DFAC` constant mismatch.

## Working-Point Validation

This constant-level conclusion was also checked at the current experimental workpoint:

- `KAIJU_NSRHS_SCALE ~ 4.18e5`

Comparison output:

- [nsrhs_workpoint_compare_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs_crossmodel/nsrhs_workpoint_compare_20260327.md)

Result:

- `coupler-like @ 4.18e5` and `coupler-crossmodel @ 4.18e5` produce nearly identical `step2` responses.
- `POT` span difference is only:
  - North: `1.7e-02 kV`
  - South: `1.62e-02 kV`

So the practical conclusion is stronger than the constant-only comparison:

- not only are the two transforms close analytically
- they are also nearly indistinguishable at the present working calibration point

## Updated Practical Conclusion

At the current stage:

- keep `~4.18e5` as the working `NSRHS` scale
- do not spend more time splitting hairs between `coupler-like` and `coupler-crossmodel`
- move the calibration focus to:
  - folded-source semantics
  - sign convention against `TIEGCM mage_ucurrent`
  - `mag -> geo` projection equivalence
