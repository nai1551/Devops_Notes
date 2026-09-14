# GitHub Actions for a React Project — Beginner's Guide

A complete walkthrough of how to run CI/CD for a React project using **GitHub Actions** with a **self-hosted runner**, written so a complete beginner can understand not just the "what" but the "why" behind each step.

**Project reference:** https://github.com/nai1551/react-ci-cd-demo.git

---

## 1. What is GitHub Actions? (The Big Picture)

GitHub Actions is GitHub's built-in automation system. Instead of manually running `npm install`, `npm test`, `npm run build` every time you change code, you write a **workflow file** that tells GitHub: *"Whenever someone pushes code, automatically do these steps for me."*

Think of it like a robot assistant that watches your repository. The moment you push code, the robot wakes up, follows your instructions step by step, and reports back whether everything worked (green checkmark) or something broke (red X).

This is the same idea as Jenkins — but GitHub Actions lives *inside* GitHub itself, so there's no separate server UI to manage (unless you use a self-hosted runner, explained below).

---

## 2. Key Concepts You Need to Know

| Term | What it means |
|---|---|
| **Workflow** | The full automation recipe, written in a `.yml` file. Lives in `.github/workflows/` in your repo. |
| **Job** | A group of steps that run together (e.g. `build-and-test`). A workflow can have multiple jobs. |
| **Step** | A single action inside a job (e.g. "Install dependencies"). Steps run in order, top to bottom. |
| **Runner** | The actual machine that executes your steps. Can be GitHub's own cloud machine, or **your own computer/server** (a "self-hosted runner"). |
| **Trigger (`on:`)** | The event that starts the workflow — e.g. a push to `main`, a pull request, or a manual click. |
| **Secret / Credential** | Sensitive values (like tokens) stored securely in GitHub, never written directly in your workflow file. |

---

## 3. Why We Used a Self-Hosted Runner

GitHub offers free cloud runners, but we used our **own server** (`Worker-server`, IP `192.168.56.102`) as the runner instead. Reasons this matters:

- The server already had Node.js, npm, and other tools installed and configured exactly how we wanted.
- It's the same machine we'd already tested the app on manually and through Jenkins — so we knew the environment worked.
- Self-hosted runners are useful when you need specific software, internal network access, or more control over the execution environment than a generic cloud machine gives you.

**How it works:** you install a small program (the "runner agent") on your server. That agent sits idle and constantly checks in with GitHub, saying "I'm here and ready." When a workflow triggers, GitHub sends the job to that agent, and it runs the steps locally on your server.

---

## 4. Step-by-Step: What We Actually Did

### Step 1 — Install and register the runner on the server

On the server (`Worker-server`), we downloaded GitHub's runner package and configured it to connect to our specific repository:

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.337.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.337.0/actions-runner-linux-x64-2.337.0.tar.gz
tar xzf actions-runner-linux-x64-2.337.0.tar.gz

./config.sh --url https://github.com/nai1551/react-ci-cd-demo --token <TOKEN_FROM_GITHUB>
```

**Why the token?** It proves to GitHub that this machine is authorized to act as a runner for *this specific repo*. You get this token fresh from GitHub each time: repo → **Settings → Actions → Runners → New self-hosted runner**. It's short-lived and single-use for security — someone can't reuse an old token to hijack your runner registration.

**Important gotcha we hit:** a self-hosted runner registered to one repo only listens to that repo. Our runner was originally connected to a different project (`nai1551-python-project`). To reuse it for the React project, we had to:
1. Stop and uninstall the old service
2. Remove the old registration from GitHub
3. Re-run `./config.sh` pointing at the new repo

### Step 2 — Run the runner as a background service

Instead of running the agent in a terminal window (which stops the moment you close it), we installed it as a **systemd service** so it runs permanently in the background, even after reboot:

```bash
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

A healthy status looks like:
```
√ Connected to GitHub
Listening for Jobs
```

This means the runner is idle, connected, and waiting for GitHub to send it work.

### Step 3 — Write the workflow file

On our local Windows machine (where the actual project code lives), inside the cloned repo, we created:

```
.github/workflows/react-ci.yml
```

**Why this exact path?** GitHub Actions only looks for workflow files inside `.github/workflows/`. Any `.yml` file there is automatically detected and activated — no extra registration needed.

```yaml
name: React CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-and-test:
    runs-on: self-hosted

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Verify Node.js
        run: |
          node --version
          npm --version

      - name: Install dependencies
        run: npm install

      - name: Lint code
        run: npm run lint

      - name: Format code
        run: npm run format

      - name: Run tests
        run: npm test -- --watchAll=false
        env:
          CI: true

      - name: Build app
        run: npm run build

      - name: Show build output
        run: ls -lh build/
```

**Breaking this down line by line:**

- `on:` — defines what triggers this workflow. Here: pushing to `main`, opening a pull request into `main`, or manually clicking "Run workflow" in GitHub's UI (`workflow_dispatch`).
- `runs-on: self-hosted` — tells GitHub "don't use your cloud machines, send this job to any runner I've registered as self-hosted." This is how GitHub finds our `Worker-server`.
- `uses: actions/checkout@v4` — a pre-built action (made by GitHub) that clones the repo's code onto the runner. Without this step, the runner would have no code to work with.
- Each `run:` step is just a shell command, executed exactly like you'd type it yourself in a terminal on that machine.
- `env: CI: true` — this is critical for React specifically. Create React App's test runner defaults to "watch mode," which waits forever for you to press keys. Setting `CI=true` tells it to run once and exit, which is required for automation to work at all.

### Step 4 — Push the workflow file to GitHub

```bash
git add .github/workflows/react-ci.yml
git commit -m "Add GitHub Actions CI workflow"
git push origin main
```

The moment this push reaches GitHub, GitHub notices the new file inside `.github/workflows/` and the `on: push` trigger fires immediately — the workflow starts running automatically, with zero manual intervention.

### Step 5 — Fix the token scope error

We hit this error on push:
```
refusing to allow a Personal Access Token to create or update workflow 
`.github/workflows/react-ci.yml` without `workflow` scope
```

**Why this happens:** GitHub treats workflow files as more sensitive than regular code, because they can execute arbitrary commands on your runner. A normal token with just `repo` access isn't allowed to create or modify anything inside `.github/workflows/` — it needs the separate `workflow` permission explicitly granted.

**Fix:** Go to GitHub → **Settings → Developer settings → Personal access tokens → Tokens (classic)** → open your token → check the `workflow` scope checkbox → update the token → use the new token value the next time Git asks for a password.

### Step 6 — Watch it run

Repo → **Actions tab** → click the workflow run → click the job name. You get a live, expandable log of every step, and can see exactly which machine executed it (confirming it's your self-hosted runner, not GitHub's cloud).

---

## 5. How to Read a Workflow Run

- **Green checkmark ✅** — every step succeeded.
- **Red X ❌** — a step failed; click it to expand and see the exact error line, just like a terminal.
- **Yellow dot 🟡** — currently in progress.
- Each step shows how long it took, useful for spotting slow steps (e.g. `npm install` is usually the longest).

---

## 6. Common Things That Go Wrong (and Why)

| Problem | Cause | Fix |
|---|---|---|
| Runner never picks up the job | Runner registered to a different repo | Re-register with `./config.sh` pointed at the correct repo URL |
| `npm test` hangs forever | CRA defaults to watch mode | Set `CI: true` in the workflow's `env:` |
| Push rejected — missing `workflow` scope | Token lacks permission to touch `.github/workflows/` | Add the `workflow` scope to your PAT |
| `lint` / `format` step fails | Script not defined in `package.json` | Check `package.json`'s `"scripts"` section matches what the workflow calls |
| Runner shows "inactive (dead)" | Service was stopped/uninstalled | `sudo ./svc.sh start` (or reinstall with `./svc.sh install` first) |

---

## 7. Quick Command Reference

**On the runner server (Linux):**
```bash
cd /home/worker/actions-runner
sudo ./svc.sh status      # check if runner is connected
sudo ./svc.sh start       # start the runner service
sudo ./svc.sh stop        # stop it
./config.sh remove --token <TOKEN>   # unregister from current repo
./config.sh --url <REPO_URL> --token <TOKEN>   # register to a new repo
```

**On your local machine (Git Bash):**
```bash
git clone https://github.com/nai1551/react-ci-cd-demo.git
cd react-ci-cd-demo
mkdir -p .github/workflows
# create react-ci.yml inside that folder
git add .github/workflows/react-ci.yml
git commit -m "Add GitHub Actions CI workflow"
git push origin main
```

---

## 8. Mental Model Summary

```
You push code
      ↓
GitHub sees .github/workflows/react-ci.yml and the "on: push" trigger
      ↓
GitHub looks for a runner labeled "self-hosted"
      ↓
Your registered runner (Worker-server) picks up the job
      ↓
Runner clones the code, runs each step in order (install → lint → test → build)
      ↓
Results (pass/fail + logs) are reported back to the Actions tab
```

That's the entire loop. Everything else — tokens, scopes, service installation — exists to make that loop secure and reliable.
