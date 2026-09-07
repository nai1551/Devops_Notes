# End-to-End DevOps CI/CD Pipeline Setup with Github Guide

**Level:** Beginner-friendly
**Tools used:** Jenkins, Ansible, GitHub, Git, Make

This guide walks through building a 3-stage Continuous Delivery (CD) pipeline using a **Jenkinsfile**, integrated with a **GitHub** repository, and configured with **Ansible** to provision dependencies on a remote **Jenkins Worker** node.

If you're new to any of these tools, read the [Prerequisites & Glossary](#0-prerequisites--glossary) section first — it explains every term used later in the guide.

---

## Table of Contents

1. [Prerequisites & Glossary](#0-prerequisites--glossary)
2. [Architecture Overview](#1-architecture-overview)
3. [Local Project Configuration](#2-local-project-configuration)
4. [Remote Node Configuration via Ansible](#3-remote-node-configuration-via-ansible)
5. [Version Control Integration (Git & GitHub)](#4-version-control-integration-git--github)
6. [Jenkins Pipeline Setup & Execution](#5-jenkins-pipeline-setup--execution)
7. [Troubleshooting Reference](#6-troubleshooting-reference)
8. [Summary & Next Steps](#7-summary--next-steps)

---

## 0. Prerequisites & Glossary

### What you need before starting
- A Linux machine (or VM) to act as the **Jenkins Controller** (runs Jenkins itself).
- A second Linux machine (or VM) to act as the **Jenkins Worker** — in this guide, `192.168.56.102`.
- Jenkins installed on the controller, with network access to the worker.
- Ansible installed on the controller (it manages the worker as the **Ansible Master**).
- A free [GitHub](https://github.com) account and a repository to push code to.
- SSH access configured between the Ansible Master and the worker node (usually via SSH keys).

### Key terms explained

| Term | What it means |
|---|---|
| **CI/CD** | Continuous Integration / Continuous Delivery — automatically building, testing, and deploying code every time it changes. |
| **Jenkins** | An automation server that runs your CI/CD pipeline steps. |
| **Jenkinsfile** | A text file (written in Groovy) that defines the pipeline's stages. It lives in your project's repository, so the pipeline is version-controlled along with your code. |
| **Pipeline** | A sequence of automated steps (e.g., Build → Test → Deploy) that Jenkins executes in order. |
| **Agent** | The machine that actually runs a pipeline's steps. `agent any` means "run on any available machine." |
| **Ansible** | A tool for automating server setup (installing packages, configuring files) without logging into each machine by hand. |
| **Ansible Master / Control Node** | The machine from which you run Ansible commands. |
| **Inventory file** | A list of machines (hosts) that Ansible is allowed to manage, typically at `/etc/ansible/hosts`. |
| **Playbook / Module** | Ansible uses "modules" (like `ping`, `apt`, `command`) to perform tasks on remote hosts. |
| **Makefile** | A file defining shortcut commands (`make build`, `make test`, etc.) so the Jenkinsfile doesn't need to know the project's internal build details. |
| **SCM** | Source Control Management — in this guide, Git/GitHub, which stores your project's version history. |
| **Refspec** | A Git concept that maps branches on a remote repository to branches Jenkins should track. |

---

## 1. Architecture Overview

```
 ┌─────────────────┐        git push        ┌──────────────────┐
 │ Developer PC     │ ─────────────────────▶│     GitHub       │
 │(Jenkinsfile, etc)│                       │   Repository     │
 └─────────────────┘                        └────────┬─────────┘
                                                       │ webhook / poll
                                                       ▼
                                          ┌─────────────────────────┐
                                          │   Jenkins Controller     │
                                          │ (runs the pipeline job)  │
                                          └────────────┬─────────────┘
                                                        │ delegates steps
                                                        ▼
                                          ┌─────────────────────────┐
                                          │    Jenkins Worker       │
                                          │   192.168.56.102        │
                                          │(provisioned by Ansible) │
                                          └─────────────────────────┘
```

**Flow in plain English:**
1. You write code + a `Jenkinsfile` + a `Makefile`, and push them to GitHub.
2. Jenkins detects the change and starts a pipeline run.
3. The pipeline runs its stages (Build, Test, Deploy) on the Jenkins Worker.
4. The Worker already has the tools it needs (like `make`) because Ansible installed them ahead of time.

---

## 2. Local Project Configuration

Two files are created at the **root directory** of your application code. These are the files Jenkins reads to know what to do.

### A. `Jenkinsfile`

This is a **declarative pipeline** — a structured, easy-to-read way of defining stages. Each `stage` block represents one phase of your CD process.

```groovy
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'make'
            }
        }

        stage('Test') {
            steps {
                sh 'make check'
            }
        }

        stage('Deploy') {
            steps {
                sh 'make publish'
            }
        }
    }
}
```

> **Beginner note:** `sh 'make'` just tells Jenkins to run a shell command — in this case, calling a target inside your `Makefile`. Jenkins doesn't need to know *how* your project builds, tests, or deploys; it just needs to know *which command to run*.

### B. `Makefile`

The `Makefile` defines what each command (`make`, `make check`, `make publish`) actually does. In a real project, these would run your compiler, test suite, or deployment scripts — here they're simplified to `echo` statements so you can confirm the pipeline works end-to-end before adding real logic.

```make
all:
	@echo "Building application..."
	@echo "Build completed successfully"

check:
	@echo "Running tests..."
	@echo "All tests passed"

publish:
	@echo "Deploying application..."
	@echo "Deployment completed successfully"
```

> **Tip:** Make sure indentation inside a `Makefile` uses actual **tab characters**, not spaces — this is a common source of `make` errors for beginners.

---

## 3. Remote Node Configuration via Ansible

The Jenkins Worker (`192.168.56.102`) needs the `make` utility installed before it can run the pipeline. Rather than installing it by hand, we use Ansible to automate this from the Ansible Master.

### Step 1: Create the Inventory File

The inventory file tells Ansible which machines it's allowed to manage.

```bash
sudo mkdir -p /etc/ansible
sudo nano /etc/ansible/hosts
```

Add the worker node under a group called `jenkins_workers`:

```ini
[jenkins_workers]
192.168.56.102 ansible_user=worker
```

> **Saving in `nano`:** Press `Ctrl + O` (write out), then `Enter` to confirm the filename, then `Ctrl + X` to exit.

### Step 2: Verify Connectivity (Ping)

Confirm Ansible can reach the worker node using its built-in `ping` module (this checks connectivity, not an actual ICMP ping):

```bash
ansible jenkins_workers -m ping -i /etc/ansible/hosts
```

**Expected output:**
```
192.168.56.102 | SUCCESS => {"ping": "pong"}
```

If this fails, double-check SSH access and that the `ansible_user` has permission to log in.

### Step 3: Install `make` on the Worker

Push the installation out to the worker using the `apt` module, with `-b` (become / sudo escalation) and `-K` (prompt for the sudo password):

```bash
ansible jenkins_workers -m apt -a "name=make state=present update_cache=yes" -b -i /etc/ansible/hosts -K
```

### Step 4: Confirm the Installation

Check that `make` installed correctly by asking for its version:

```bash
ansible jenkins_workers -m command -a "make --version" -i /etc/ansible/hosts
```

---

## 4. Version Control Integration (Git & GitHub)

Push the `Jenkinsfile` and `Makefile` to GitHub so Jenkins can pull them when a build is triggered.

```bash
# Check which files have changed or are untracked
git status

# Stage the new pipeline files
git add Jenkinsfile Makefile

# Commit the changes with a clear message
git commit -m "Add valid Jenkinsfile and Makefile for pipeline"

# Push to the main branch on GitHub
git push origin main
```

> **Beginner note:** Jenkins doesn't watch your local machine — it watches the **GitHub repository**. Nothing changes on the Jenkins side until you push.

---

## 5. Jenkins Pipeline Setup & Execution

### Dashboard Configuration

1. In Jenkins, create a new **Pipeline Job** named `new_pipeline`.
2. Scroll to the **Pipeline** section of the job configuration.
3. Set **Definition** to `Pipeline script from SCM`.
4. Set **SCM** to `Git`, and enter the Repository URL:
   `https://github.com/nai1551/jenkins-pipeline-demo.git`
5. Save the configuration and click **Build Now**.

### Bug Resolution: Refspec Matching Issue

* **Initial failure:** Build `#1` failed with:
  ```
  java.lang.IllegalArgumentException: Invalid refspec refs/heads/**
  ```
* **Root cause:** The **Branch Specifier** field was left as the wildcard `**`, which Jenkins couldn't resolve into a valid Git refspec.
* **Fix:** Changed the **Branch Specifier (blank for 'any')** field from `**` to the explicit branch path `*/main`.

### Outcome

Re-running the job with **Build Now** triggered build `#2`, which completed successfully (green checkmark / **SUCCESS**).

---

## 6. Troubleshooting Reference

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Invalid refspec refs/heads/**` | Branch Specifier left as wildcard `**` | Set it to `*/main` (or your actual branch name) |
| Ansible `ping` fails | SSH access not configured, or wrong `ansible_user` | Verify SSH keys and that the user exists on the worker |
| `make: command not found` on Jenkins Worker | `make` wasn't installed | Re-run Step 3 in [Section 3](#3-remote-node-configuration-via-ansible) |
| `apt` module fails with permission denied | Missing `-b` (become) flag or wrong sudo password | Re-run with `-b -K` and confirm the password |
| Jenkins can't find the Jenkinsfile | Wrong repository URL or branch, or file not pushed to GitHub | Confirm `git push` succeeded and the branch matches the job config |
| Makefile targets fail silently | Tabs vs. spaces indentation issue | Ensure Makefile recipes use tab characters, not spaces |

---

## 7. Summary & Next Steps

You now have a working 3-stage pipeline (**Build → Test → Deploy**) that:
- Is defined in version control (`Jenkinsfile`, tracked in GitHub)
- Runs on a Jenkins Worker provisioned automatically by Ansible
- Triggers on demand via **Build Now** (and can be extended to trigger automatically via GitHub webhooks)

**Suggested next steps for going further:**
1. Replace the `echo` statements in the `Makefile` with real build/test/deploy commands for your project.
2. Set up a GitHub webhook so Jenkins builds automatically on every push, instead of manually clicking **Build Now**.
3. Add a `post` block to the Jenkinsfile to send notifications (e.g., Slack or email) on build success/failure.
4. Explore Ansible **playbooks** (YAML files) instead of one-off commands, for more complex provisioning tasks.
