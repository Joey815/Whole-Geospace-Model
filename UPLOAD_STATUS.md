# Upload Status

Prepared locally:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
```

Target GitHub repository:

```text
https://github.com/Joey815/Whole-Geospace-Model.git
```

GitHub connector check:

```text
repository = Joey815/Whole-Geospace-Model
visibility = public
default_branch = main
permissions = admin, maintain, pull, push, triage
size = 0
```

GitHub upload is not completed from this shell because the GitHub CLI is not
installed:

```text
gh: command not found
```

and direct `git push` over HTTPS failed because the local shell has no GitHub
credential available:

```text
fatal: could not read Username for 'https://github.com': No such device or address
```

SSH push also failed with the current local key:

```text
fatal: Could not read from remote repository.
```

The repository has been structured and committed locally so it can be pushed
once a GitHub credential is available.

Current local commit:

```text
1828dcb Add WACCMX SAMI3 coupling collaboration snapshot
```

Local bundle backup:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524.bundle
```

Recommended next command after authenticating GitHub from this shell:

```bash
cd /home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
git remote set-url origin https://github.com/Joey815/Whole-Geospace-Model.git
git push -u origin main
```
