# Limitations

1. This is an integrated evidence package, not one single production full-chain run.
2. SAMI3 -> RAIJU/GAMERA currently passes scalar moments only: `Pavg`, `Davg`, `Pstd`, `Dstd`, and `tiote`.
3. Bulk velocity, momentum density, anisotropic pressure tensor, field-aligned flow, and ExB drift are not coupled.
4. The conservative exclude-Lmax product is diagnostic. The production-readiness validator intentionally fails.
5. The current source bVol skipped above target Lmax is `0.999595965103914`.
6. WACCM-X feedback consumption from MAGE/RAIJU/GAMERA should still get stronger per-frame runtime diagnostics before science claims.
7. The WACCM-X -> SAMI3 live neutral evidence is f19-based; f09/finer production scaling remains separate work.
8. Large HDF5 model products are not copied into this archive; source paths are recorded in manifests.
