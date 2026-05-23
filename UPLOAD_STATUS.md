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

GitHub upload was completed after installing a user-local GitHub CLI:

```text
/home/jiaoy_group/jiaoy/.local/gh-2.92.0/bin/gh
```

The first direct push attempt failed before authentication because the GitHub
CLI was not installed:

```text
gh: command not found
```

and direct `git push` over HTTPS failed because the local shell initially had
no GitHub credential available:

```text
fatal: could not read Username for 'https://github.com': No such device or address
```

SSH push also failed with the current local key:

```text
fatal: Could not read from remote repository.
```

After GitHub device authentication as `Joey815`, the local repository was
pushed to GitHub.

Current remote HEAD after upload:

```text
d5e16b2 Merge remote initial commit
```

Local bundle backup:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524.bundle
```

Remote verification:

```text
origin/main = d5e16b2b31beceab1d3b7420adc7ebc0cda9517d
tree entries = 116
README raw URL = https://raw.githubusercontent.com/Joey815/Whole-Geospace-Model/main/README.md
```

Future pushes from this shell can use:

```bash
cd /home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
git remote set-url origin https://github.com/Joey815/Whole-Geospace-Model.git
git push -u origin main
```
