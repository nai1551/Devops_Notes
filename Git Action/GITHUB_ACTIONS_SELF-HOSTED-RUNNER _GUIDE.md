# GitHub Actions — What It Is and What You Did

This document explains GitHub Actions in plain English, and walks through exactly what was set up in this project (`python-project`), so you can understand and reproduce it later.

---

## 1. What is GitHub Actions?

GitHub Actions is a built-in automation tool on GitHub. It lets you define a set of steps (called a **workflow**) that run automatically whenever something happens in your repository — usually a `git push`.

Think of it as a robot that:
1. Watches your repo for events (like a push to `main`)
2. Spins up a fresh computer (or uses one you provide)
3. Runs a checklist of commands you wrote
4. Reports back success (✅) or failure (❌)

This is the same general idea as **Jenkins** — GitHub Actions is just Jenkins built directly into GitHub, so you don't need a separate Jenkins server for the CI part.

---

## 2. Key concepts

| Term | Meaning |
|---|---|
| **Workflow** | A YAML file describing what to run and when. Lives in `.github/workflows/`. |
| **Trigger (`on:`)** | The event that starts the workflow — e.g. `push`, `pull_request`. |
| **Job** | A group of steps that run together on one machine. A workflow can have multiple jobs. |
| **Step** | A single command or action inside a job. |
| **Runner** | The machine that actually executes the job. Can be: |
| | — **GitHub-hosted runner** (`runs-on: ubuntu-latest`) — a temporary cloud machine GitHub provides for free. |
| | — **Self-hosted runner** (`runs-on: self-hosted`) — your own machine, registered to listen for jobs. |
| **Secret** | An encrypted variable (like a password or SSH key) stored in repo Settings, used inside workflows without exposing it in code. |

---

## 3. What you built in this project

### a) CI workflow — `.github/workflows/ci.yml`

Runs automatically on every push to `main`. Uses a **GitHub-hosted runner**, because it doesn't need access to your private server — it just needs to install Python, install dependencies, and run checks. Steps include:
- Set up Python
- Install dependencies from `requirements.txt`
- Syntax-check `app.py` (and optionally other scripts)
- Run tests with `pytest tests/`

This step catches broken code **before** it ever reaches deployment — same purpose as the "Test" stage in your old Jenkinsfile.

### b) Deploy workflow — `.github/workflows/deploy.yml`

Also triggers on push to `main`. Has two jobs:
1. **`test`** — runs on a GitHub-hosted runner, same checks as above (a safety gate).
2. **`deploy`** — runs on `self-hosted`, meaning it executes directly on your **worker node** (`192.168.56.102`). This job:
   - Copies the app into `/opt/kidney-disease-streamlit`
   - Sets up a Python virtual environment and installs dependencies
   - Restarts the `kidney-streamlit` systemd service
   - Runs a health check against `http://localhost:8501/_stcore/health`

This mirrors your original Jenkinsfile's `Prepare App Directory`, `Python Setup`, `Deploy`, and `Health Check` stages — just triggered by GitHub instead of Jenkins.

### c) Self-hosted runner setup

Because `192.168.56.102` is a private IP, GitHub's cloud runners cannot reach it directly. To solve this, you installed a **self-hosted runner** on the worker machine itself:

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.337.0.tar.gz -L <download URL from GitHub>
tar xzf actions-runner-linux-x64-2.337.0.tar.gz
./config.sh --url https://github.com/nai1551/python-project --token <TOKEN>
sudo ./svc.sh install
sudo ./svc.sh start
```

This registers the worker machine as a listener. When a workflow specifies `runs-on: self-hosted`, GitHub sends the job to this machine instead of spinning up a cloud VM. The runner runs as a **systemd service**, so it stays alive and auto-starts on reboot — functioning like the old Jenkins agent did.

### d) Passwordless sudo for deployment commands

The `deploy` job needs to run `systemctl restart kidney-streamlit` and read logs, which normally require a sudo password. Since GitHub Actions can't type a password interactively, you configured `visudo` to allow these specific commands without a password prompt:

```
worker ALL=(ALL) NOPASSWD: /bin/systemctl restart kidney-streamlit, /bin/systemctl is-active kidney-streamlit, /usr/bin/journalctl -u kidney-streamlit -n 50 --no-pager
```

This is scoped narrowly — only these exact commands skip the password, not all `sudo` usage.

### e) Repository secrets

Early on, `SSH_HOST` and `SSH_USER` secrets were added in **Settings → Secrets and variables → Actions**, for an SSH-based deploy approach. After switching to the self-hosted runner (which doesn't need SSH since it runs locally on the target machine), these secrets became unnecessary and can be deleted if you like.

---

## 4. The full flow, end to end

```
git push origin main
        │
        ▼
GitHub detects the push, triggers workflows in .github/workflows/
        │
        ├── ci.yml        → runs on GitHub's cloud → tests only
        │
        └── deploy.yml
                ├── job "test"    → runs on GitHub's cloud → tests
                └── job "deploy"  → runs on YOUR worker (self-hosted)
                                      → copies files, restarts service,
                                        health-checks the running app
```

---

## 5. Where to check status

- **Live run status:** repo → **Actions** tab → click a run → expand each step's logs.
- **Runner status:** repo → **Settings → Actions → Runners** — should show green "Idle" when ready.
- **On the worker machine:** `sudo ./svc.sh status` (inside `~/actions-runner`) shows if the runner service is alive.
- **App logs on failure:** the workflow automatically prints the last 50 lines of `journalctl -u kidney-streamlit` if the deploy step fails.

---

## 6. Prerequisites checklist (for setting this up on a new project)

Use this if you ever repeat this setup from scratch on another project:

- [ ] A GitHub repository with your app code pushed to `main`
- [ ] A target server (physical, VM, or cloud) with:
  - [ ] Python 3 installed
  - [ ] A systemd service already created and working manually (e.g. `kidney-streamlit.service`) that runs your app
  - [ ] Network reachability confirmed — public IP/DNS for GitHub-hosted runners, or private IP for a self-hosted runner
- [ ] A `requirements.txt` listing all Python dependencies
- [ ] A `tests/` folder with at least one real test file
- [ ] Decide: GitHub-hosted runner (public server) vs self-hosted runner (private/local server) — see the decision table below

| Situation | Use |
|---|---|
| Server has a public IP or is reachable over the internet | GitHub-hosted runner + SSH deploy step |
| Server is on a private/local network (e.g. `192.168.x.x`, office LAN, VirtualBox host-only) | Self-hosted runner installed directly on that server |

---

## 7. Troubleshooting log — real issues hit in this project and their fixes

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | `fatal: pathspec '.github/workflows/ci.yml' did not match any files` | The workflow file existed in the project root, not inside `.github/workflows/` | `mkdir -p .github/workflows` then `mv ci.yml .github/workflows/ci.yml` |
| 2 | `visudo` → `syntax error` | A sudoers line was pasted with literal `<username>` placeholder brackets still in it | Replace the placeholder with the real username, no angle brackets |
| 3 | `pytest tests/` → `collected 0 items`, exit code 5 | The test file only had a `if __name__ == "__main__":` block; pytest only auto-discovers functions starting with `test_` | Added a `def test_smoke():` wrapper function that calls the existing logic |
| 4 | `Syntax check train_model.py` step failed: `No such file or directory` | The workflow assumed a `train_model.py` file existed, but the project never included one (model was already trained and saved) | Made the step conditional — checks `if [ -f train_model.py ]` before compiling, otherwise skips with a message |
| 5 | `Prepare app directory` step: `cp: cannot create regular file ... Permission denied` | `/opt/kidney-disease-streamlit` was owned by `root`, but the deploy job runs as the `worker` user without a `sudo` prefix on `cp`/`mkdir` | `sudo mkdir -p /opt/kidney-disease-streamlit && sudo chown -R worker:worker /opt/kidney-disease-streamlit` — done once, so future deploys don't need sudo for file copies |
| 6 | `systemctl restart kidney-streamlit` would have prompted for a password inside the workflow (non-interactive, so it would hang/fail) | Deploy job needs `sudo` for specific systemd commands, but GitHub Actions can't type a password | Added a scoped `NOPASSWD` rule in `visudo` for exactly those commands only |
| 7 | App unreachable at `http://192.168.56.102:8501/` even after a successful deploy | GitHub's cloud runners cannot route to a private/local IP at all | Installed a **self-hosted runner** directly on the target machine so the deploy job executes locally, with no network hop needed |

---

## 8. Security notes

- The `NOPASSWD` sudoers rule is scoped to **exact commands only** (`systemctl restart kidney-streamlit`, `systemctl is-active kidney-streamlit`, `journalctl -u kidney-streamlit ...`) — never grant blanket `NOPASSWD: ALL`, since that would let *any* process running as that user execute *any* command as root without a password.
- A self-hosted runner executes arbitrary code from your repository's workflows on that machine. Only use self-hosted runners on repositories you fully control, and avoid enabling them on repos that accept public pull requests, since a malicious PR could run code directly on your server.
- Secrets (`SSH_HOST`, `SSH_USER`, etc.) that are no longer used should be deleted from **Settings → Secrets and variables → Actions** to reduce exposure.

---

## 9. Possible next improvements

- Add a `staging` vs `production` environment split so pushes to a `dev` branch deploy to a test server, and only `main` deploys to production.
- Add Slack/email/Discord notification steps on deploy success or failure.
- Add a rollback step: if the health check fails after deploy, automatically restart the previous known-good version.
- Replace the `train_model.py` conditional check by either committing a real training script or removing the step entirely if it will never exist.
- Consider Docker: package the app into a container so "works in CI" and "works on the server" can never drift apart.
