# Local CIME qhslurm Build Config

This directory stores the local CIME machine override used for the
WACCM-X/SAMI3 prototype case on 2026-05-25.

The active case was built with a temporary HOME containing:

```text
.cime/config_machines.xml -> code/cime/qhslurm_config_machines_v3.xml
.cime/config_compilers.xml -> user local compiler override
.cime/config_batch.xml -> user local Slurm override
```

This avoided the stale global `~/.cime/config_machines.xml` v2/v3 schema
conflict without modifying the user's global CIME files.  The case-local
`EXTRA_MACHDIR` was also cleared because CIME v3 re-read the
`local_machines_v3/qhslurm/config_machines.xml` fragment after loading the root
machine file.
