# SAMI3 -> RAIJU Source-Domain L Scan

Date: 2026-05-26 CST

## Purpose

The schema v7 exclude-Lmax product made the outside-domain policy explicit, but
the remaining physics question is whether extending the RAIJU target L domain is
reasonable.  This checkpoint quantifies how far the RAIJU target Lmax would
need to move to capture meaningful fractions of positive active Voltron source
bVol.

## Script

New repeatable analyzer:

```text
scripts/analyze_sami3_raiju_source_domain_lscan.py
```

Inputs:

```text
--audit-h5 <sami3_raiju_flux_volume_geometry_audit*.h5>
--weights-h5 <sami3_to_raiju_weights*.h5>
```

Default datasets:

```text
source L = /source/Lb_cc
source bVol = /source/bvol_active_cc when present, otherwise /source/bvol_cc
target L edge = /dst/L_edge
```

Outputs:

```text
logs/sami3_raiju_source_domain_lscan_20260526/sami3_raiju_source_domain_lscan_active_20260526.json
logs/sami3_raiju_source_domain_lscan_20260526/sami3_raiju_source_domain_lscan_active_20260526.txt
```

## Source Distribution

The scan uses the active bVol ledger from the exclude-Lmax audit:

```text
source_positive_cell_count = 33676
source_positive_bvol_sum = 2268463.9951948179
source_L_min = 1.0192675590515137
source_L_max = 553.77520751953125
source_L_bvol_weighted_mean = 354.10948435454907
current_target_Lmax = 33.163437477526358
current_target_dipole_lat_deg = 10.0
```

The `dipole_lat_deg` column is the dipole-equivalent latitude from:

```text
L = 1 / sin(lat)^2
```

It is not a recommendation to run RAIJU at that latitude; it is a diagnostic
translation of L-domain extent.

## Threshold Scan

Positive active bVol included if the target Lmax were set to:

```text
Lmax        lat_deg   included_fraction   excluded_fraction
33.1634     10.0000   0.000404035        0.999595965
50           8.1301   0.001747031        0.998252969
100          5.7392   0.017065090        0.982934910
150          4.6834   0.052912858        0.947087142
200          4.0548   0.108782366        0.891217634
250          3.6261   0.211903066        0.788096934
300          3.3098   0.309611665        0.690388335
350          3.0640   0.523022953        0.476977047
400          2.8660   0.565912727        0.434087273
450          2.7020   0.796474763        0.203525237
500          2.5632   0.866714372        0.133285628
553.7752     2.4355   1.000000000        0.000000000
```

## Quantile Inversion

Lmax required to include active-bVol quantiles:

```text
quantile   Lmax_required   lat_deg
0.001      42.9641         8.7754
0.005      71.1299         6.8096
0.010      83.3803         6.2873
0.050      145.1508        4.7612
0.100      180.7591        4.2655
0.250      275.2610        3.4555
0.500      317.8696        3.2153
0.750      448.2438        2.7072
0.900      530.3418        2.4888
0.950      545.7606        2.4533
0.990      553.7748        2.4355
0.999      553.7752        2.4355
```

## Interpretation

This scan argues against treating the current outside-domain failure as a small
RAIJU grid-extent tuning problem.

To include even half of the positive active Voltron source bVol, the RAIJU
target Lmax would need to move from about 33 to about 318, corresponding to a
dipole-equivalent latitude near 3.2 degrees.  To include 90%, Lmax would need
to move to about 530, near 2.5 degrees.

That would push the RAIJU target grid far outside the current inner
magnetosphere shell-grid regime used by these runs:

```text
RAIJU XML grid = SHGRID, ThetaL=15, ThetaU=50
current target L_edge max = 33.1634
```

Therefore the practical next policy is:

```text
1. Do not extend RAIJU target Lmax to catch the high-L Voltron bVol in this
   prototype without a separate RAIJU/grid physics review.
2. Treat the schema v7 exclude-Lmax product as the current safe runtime adapter
   for target-domain density-only experiments.
3. If production coupling needs that high-L source volume, define a different
   source subset or a different target-domain model instead of forcing the
   current RAIJU grid to L~300-550.
```

This supports freezing the current SAMI3 -> RAIJU path as a validated
diagnostic/runtime adapter while moving the main coupling work back to the
remaining WACCM-X/SAMI3 and REMIX/SAMI3 production-cadence issues.
