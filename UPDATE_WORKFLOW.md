# Update Workflow

This repository is the shared remote record for the WACCM-X / SAMI3 / MAGE
coupling work.

## Rule

After every meaningful local implementation, validation, or plan/handoff update:

```text
1. Copy or edit the relevant collaboration files in this repository.
2. Commit the update with a concrete message.
3. Push `main` to `Joey815/Whole-Geospace-Model`.
4. Verify the remote HEAD and relevant file/tree state.
5. Report the GitHub commit hash in the work summary.
```

## Remote

```text
https://github.com/Joey815/Whole-Geospace-Model
visibility: PRIVATE
default branch: main
```

## Local Working Copy

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
```

## Standard Sync Commands

```bash
cd /home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
git status --short
git add <changed files>
git commit -m '<specific update message>'
git push
git ls-remote origin refs/heads/main
```

Keep large generated artifacts out of git.  Update
`manifests/large_artifacts_not_committed.txt` instead when new large files are
important for reproducibility.
