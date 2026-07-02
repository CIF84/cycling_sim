# Git Cheat Sheet --- Bike Science Pro

A practical reference for the Git commands you'll use most often while
developing Bike Science Pro.

------------------------------------------------------------------------

## Where am I?

``` bash
pwd
```

Current working directory.

``` bash
ls
```

List files.

``` bash
ls -la
```

Detailed list including hidden files.

------------------------------------------------------------------------

## Repository status

``` bash
git branch
```

Shows branches (`*` marks the current one).

``` bash
git status
```

Shows current branch and all modified, staged, deleted and untracked
files.

------------------------------------------------------------------------

## Switch branches

``` bash
git switch v2-scenario-engine
```

``` bash
git switch main
```

------------------------------------------------------------------------

## Save work

``` bash
git add .
```

Stage all changes.

``` bash
git commit -m "Phase 9.1: adaptive decision engine"
```

Create a checkpoint.

------------------------------------------------------------------------

## History

``` bash
git log --oneline
```

``` bash
git log --oneline -- streamlit_app_v2.py
```

------------------------------------------------------------------------

## Compare

``` bash
git diff
```

``` bash
git diff --staged
```

------------------------------------------------------------------------

## Restore

``` bash
git restore filename.py
```

``` bash
git checkout v2-scenario-engine -- streamlit_app_v2.py
```

------------------------------------------------------------------------

## Find files

``` bash
find . -name "streamlit_app_v2.py"
```

------------------------------------------------------------------------

## Tags

``` bash
git tag phase-9
```

``` bash
git tag
```

------------------------------------------------------------------------

## Push

``` bash
git push
```

``` bash
git push --tags
```

------------------------------------------------------------------------

## Daily workflow

``` text
git switch v2-scenario-engine
git status

# work

git add .
git commit -m "Meaningful message"
git push
```

------------------------------------------------------------------------

## Recovery

``` bash
find . -name "filename"
```

``` bash
git branch
```

``` bash
git status
```

``` bash
git log --oneline -- filename
```

------------------------------------------------------------------------

## Mental model

Repository → Branches → Commits → Files

For Bike Science Pro:

-   `main` = stable milestones
-   `v2-scenario-engine` = active development
