# License And Publication Notes

This snapshot is meant for collaboration, not as a clean public release.

Before making the GitHub repository public, review:

```text
CESM/WACCM-X source and input-data license constraints
SAMI3 source distribution terms
MAGE/kaiju source license constraints
cluster-specific paths and Slurm configuration
any institution-specific or unpublished model coupling details
```

This package deliberately excludes:

```text
compiled binaries
large NetCDF/HDF5/binary payload outputs
full upstream source trees
full run directories
large live-dump arrays
large ESMF weight and runtime-map files
```

Some copied SourceMod/module files may still derive from upstream model code.
Treat this repository as private/internal unless those files are cleared for
public redistribution.
