# Git, Bit by Bit

A step-by-step Git guide, structured topic by topic.

---

## 1. Introduction to Version Control

Version control is a system that records changes to files over time, so you can:
- Recall specific versions later
- See who changed what, and when
- Undo mistakes safely
- Work on the same project with others without overwriting each other's work

Git is a **distributed** version control system — every developer has a full copy of the project's history on their own machine, not just on a central server.

**Why it matters:**
- No more `file_final_v2_reallyfinal.js`
- Safe to experiment — you can always go back
- Enables teamwork without stepping on each other's changes

---

## 2. Setting Up Git

```bash
# Check if Git is installed
git --version

# Set your identity (used in every commit you make)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# See your current settings
git config --list
```

This is a one-time setup per machine.

---

## 3. Putting the Project Under Version Control

**Starting a brand-new project:**
```bash
git init
```
This creates a hidden `.git` folder — that folder *is* the repository. It stores all history.

**Or copying an existing project:**
```bash
git clone <repository-url>
```

**Getting files into the repo (the core loop):**
```bash
git status              # see what's changed
git add <file>           # stage a specific file
git add .                 # stage everything
git commit -m "message"   # save a permanent snapshot
```

**The three areas involved:**

| Area | Role |
|---|---|
| Working Directory | Your files as you edit them |
| Staging Area | Changes queued up for the next commit |
| Repository | Saved commit history |

---

## 4. Resetting Unwanted Changes

Mistakes happen — Git gives you several ways to undo them, depending on how far you want to roll back.

**Unstage a file (keep the edits):**
```bash
git restore --staged <file>
```

**Discard changes in a file (back to last commit):**
```bash
git restore <file>
```

**Undo the last commit but keep your changes:**
```bash
git reset --soft HEAD~1
```

**Undo the last commit and discard the changes:**
```bash
git reset --hard HEAD~1
```
⚠️ `--hard` permanently deletes uncommitted work — use carefully.

**Fix the last commit's message or add a forgotten file:**
```bash
git commit --amend -m "Corrected message"
```

**Undo a commit safely by adding a new reverting commit (good for shared history):**
```bash
git revert <commit-hash>
```

---

## 5. Tagging and Branching

**Branching** — a separate line of development, so you can build something new without touching the stable code:
```bash
git branch                    # list branches
git branch new-feature        # create a branch
git checkout new-feature      # switch to it
git checkout -b new-feature   # create + switch in one step
git switch new-feature        # modern way to switch
git branch -m master main     # rename of branch 
```

**Merging** — bringing a branch's changes back in:
```bash
git merge new-feature
git branch -d new-feature     # delete branch once merged
```

**Tagging** — marking a specific commit as important, usually for releases:
```bash
git tag v1.0.0                       # lightweight tag on current commit
git tag -a v1.0.0 -m "First release" # annotated tag (recommended, stores message/author)
git tag                               # list all tags
git push origin v1.0.0                # push a tag to the remote
```

---

## 6. History

**View commit history:**
```bash
git log                  # full detailed history
git log --oneline        # condensed, one line per commit
git log --graph --all    # visual branch/merge history
git show <commit-hash>   # full details of one commit
```

**Compare changes:**
```bash
git diff                    # unstaged changes vs last commit
git diff --staged           # staged changes vs last commit
git diff <commit1> <commit2> # compare two commits
```

**Find who changed a line:**
```bash
git blame <file>
```

---

## 7. Remotes and GitHub

A **remote** is a version of your repository hosted elsewhere (e.g. GitHub, GitLab).

```bash
git remote add origin <url>   # connect your repo to a remote named "origin"
git remote -v                  # list connected remotes
```

**Sending and receiving changes:**
```bash
git push origin main    # upload your commits
git pull origin main    # download + merge remote commits
git fetch                # download commits without merging yet
```

**Typical daily workflow with a remote:**
```bash
git pull                          # 1. get the latest changes
# ... edit files ...
git add .                         # 2. stage changes
git commit -m "Describe change"   # 3. save snapshot
git push                          # 4. upload to GitHub
```

**Cloning someone else's project:**
```bash
git clone <repository-url>
```

---

## Quick Reference

```bash
git init                  # start a repo
git clone <url>           # copy a remote repo
git status                # check current state
git add .                 # stage changes
git commit -m "msg"       # save snapshot
git restore <file>        # discard changes
git reset --soft HEAD~1   # undo last commit, keep changes
git branch <name>         # create branch
git checkout -b <name>    # create + switch branch
git merge <name>          # merge branch
git tag -a v1.0 -m "msg"  # tag a release
git log --oneline         # view history
git remote add origin <url>
git push / git pull       # sync with remote
```

---

## Key Vocabulary

- **Repository (repo):** the project Git is tracking
- **Commit:** a saved snapshot of changes
- **Branch:** an independent line of development
- **Tag:** a named marker on a specific commit (usually a release)
- **Merge:** combining changes from two branches
- **Remote:** a hosted copy of the repo (e.g. GitHub)
- **HEAD:** pointer to your current commit/branch
- **Origin:** default name for your main remote

---

*Practice tip: init a small repo, make a few commits, create a branch, break something, reset it, then merge the branch back. That one exercise covers almost everything above.*
