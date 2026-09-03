---
title: Jenkins Installation on Ubuntu 24.04 via Ansible
version: 1.0
scope: Single-node Jenkins install on a remote worker, driven from an Ansible control node
---

# Jenkins Installation on Ubuntu 24.04 Worker Node using Ansible

A step-by-step reference for installing Jenkins on an Ubuntu 24.04 host using ad-hoc Ansible commands, including the reasoning behind each step, verification checks, a full troubleshooting matrix, and a reusable playbook version at the end.

## Environment

| Item | Value |
|---|---|
| Control node | `master-server` |
| Managed node(s) | `worker1` (inventory group: `workers`) |
| Worker OS | Ubuntu 24.04 LTS (Noble Numbat) |
| Java | OpenJDK 21 (JRE) |
| Jenkins port | `8080` (default) |
| Package manager | `apt` |

## Prerequisites

- Ansible installed on the control node, with SSH access to `worker1`
- A `workers` group defined in your inventory (`/etc/ansible/hosts` or a project inventory file)
- A sudo-capable SSH user on the worker
- Outbound internet access from the worker to `pkg.jenkins.io`

## Table of Contents

1. [Verify the Worker OS](#1-verify-the-worker-os)
2. [Update the APT Cache](#2-update-the-apt-cache)
3. [Install Java 21](#3-install-java-21)
4. [Install Repository Prerequisites](#4-install-repository-prerequisites)
5. [Create the APT Keyring Directory](#5-create-the-apt-keyring-directory)
6. [Download the Jenkins Signing Key](#6-download-the-jenkins-signing-key)
7. [Add the Jenkins Repository](#7-add-the-jenkins-repository)
8. [Update APT Again](#8-update-apt-again)
9. [Install Jenkins](#9-install-jenkins)
10. [Verify the Jenkins Package](#10-verify-the-jenkins-package)
11. [Check the Jenkins Service](#11-check-the-jenkins-service)
12. [Start and Enable Jenkins](#12-start-and-enable-jenkins)
13. [Open the Firewall for Port 8080](#13-open-the-firewall-for-port-8080)
14. [Check Port 8080 Is Listening](#14-check-port-8080-is-listening)
15. [Retrieve the Initial Admin Password](#15-retrieve-the-initial-admin-password)
16. [Complete Setup in the Browser](#16-complete-setup-in-the-browser)
17. [Security Considerations](#security-considerations)
18. [Troubleshooting Matrix](#troubleshooting-matrix)
19. [Useful Jenkins Commands](#useful-jenkins-commands)
20. [Ansible Concepts Practiced](#ansible-concepts-practiced)
21. [Appendix A — Reusable Playbook](#appendix-a--reusable-playbook)

Each numbered step below follows the same structure: **Command → Parameters → Why → Verification**.

---

## 1. Verify the Worker OS

```bash
ansible workers -a "cat /etc/os-release"
```

**Why:** Package managers and paths differ across distributions (`apt` vs `dnf`/`yum`, `/etc/apt` vs `/etc/yum.repos.d`). Confirming Ubuntu up front justifies every `apt`-based step that follows.

**Expected:** `PRETTY_NAME="Ubuntu 24.04.x LTS"`, `ID=ubuntu`.

---

## 2. Update the APT Cache

```bash
ansible workers -b -m apt -a "update_cache=yes" -K
```

| Flag/Arg | Meaning |
|---|---|
| `workers` | Target inventory group |
| `-b` | Become (sudo) on the remote host |
| `-m apt` | Use Ansible's `apt` module |
| `-a` | Module arguments |
| `update_cache=yes` | Refresh the local package index |
| `-K` | Prompt for the become (sudo) password |

**Why:** Ubuntu caches a local list of available packages and versions. Refreshing it ensures apt knows about current package metadata before anything is installed.

---

## 3. Install Java 21

```bash
ansible workers -b -m apt -a "name=openjdk-21-jre state=present" -K
```

**Why:** Jenkins runs on the JVM. The JRE (not the full JDK) is sufficient since Jenkins only needs to *run* Java bytecode, not compile it.

**Verify:**
```bash
ansible workers -a "java -version"
```
**Expected:** `openjdk version "21.0.x"`

---

## 4. Install Repository Prerequisites

```bash
ansible workers -b -m apt -a "name=curl,gnupg state=present" -K
```

**Why:**
- `curl` — fetches resources over HTTP/HTTPS (used implicitly by later steps and useful for manual checks)
- `gnupg` — provides the tooling apt relies on to handle signing keys for third-party repositories

**Note on syntax:** package names are comma-separated *within* `name=`; separate arguments (like `state=`) are space-separated, not comma-separated. Mixing the two is a common error — see [Troubleshooting §3](#troubleshooting-matrix).

---

## 5. Create the APT Keyring Directory

```bash
ansible workers -b -m file -a "path=/etc/apt/keyrings state=directory mode=0755" -K
```

**Why:** Modern Debian/Ubuntu apt discourages dropping keys into the global trusted-key store, since a key added there is trusted for *every* repository on the system. Storing each third-party key under `/etc/apt/keyrings/` and referencing it per-repository with `signed-by=` scopes trust to only that repository.

`mode=0755` — owner (root) can read/write/execute; group and others can read/execute (needed for apt itself to traverse and read the directory).

---

## 6. Download the Jenkins Signing Key

```bash
ansible workers -b -m get_url -a "url=https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key dest=/etc/apt/keyrings/jenkins-keyring.asc mode=0644" -K
```

**Why:** This key lets apt cryptographically verify that Jenkins packages actually come from the Jenkins project and haven't been tampered with in transit.

**Why `get_url` over a shell `wget`/`curl` task:** it's idempotent (won't re-download an unchanged file), reports a checksum of what was fetched, and fits Ansible's declarative model better than an ad-hoc shell command.

**Verify:**
```bash
ansible workers -a "ls -l /etc/apt/keyrings/jenkins-keyring.asc"
```

---

## 7. Add the Jenkins Repository

```bash
ansible workers -b -m apt_repository -a "repo='deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/' filename=jenkins state=present" -K
```

**Why:** Tells apt where to find Jenkins packages, and which key (from Step 6) to trust for them. `filename=jenkins` names the resulting file `/etc/apt/sources.list.d/jenkins.list` rather than an auto-generated name.

**Verify:**
```bash
ansible workers -a "cat /etc/apt/sources.list.d/jenkins.list"
```
**Expected:**
```text
deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/
```

---

## 8. Update APT Again

```bash
ansible workers -b -m apt -a "update_cache=yes" -K
```

**Why:** The Jenkins repository was only added in Step 7 — apt still doesn't know what packages it offers until the cache is refreshed again. Skipping this produces `Unable to locate package jenkins` in the next step.

---

## 9. Install Jenkins

```bash
ansible workers -b -m apt -a "name=jenkins state=present" -K
```

**Why `state=present`:** declares the desired end state ("Jenkins should be installed") rather than issuing an imperative "install" command. If Jenkins is already present, Ansible reports `changed: false` and does nothing further — this is Ansible's idempotence at work, and it's what makes rerunning the same playbook safe.

The postinstall script also creates and enables the `jenkins` systemd service automatically.

---

## 10. Verify the Jenkins Package

```bash
ansible workers -b -m shell -a "dpkg -l | grep jenkins" -K
```

**Expected:** a line beginning `ii  jenkins  <version>  all  ...`. The `ii` prefix means the package is fully installed and configured.

---

## 11. Check the Jenkins Service

```bash
ansible workers -b -m command -a "systemctl status jenkins --no-pager" -K
```

**Why:** Confirms Jenkins is actually running as a background `systemd` service, not just installed on disk. `--no-pager` prevents the command from hanging waiting for pager input over a non-interactive SSH session.

**Expected:** `Active: active (running)`

---

## 12. Start and Enable Jenkins

If the service isn't already running:

```bash
ansible workers -b -m service -a "name=jenkins state=started" -K
```

To ensure Jenkins survives a reboot:

```bash
ansible workers -b -m service -a "name=jenkins state=started enabled=yes" -K
```

**Why:** `state=started` is idempotent — it won't restart an already-running service. `enabled=yes` registers Jenkins with systemd so it starts automatically at boot, without needing a manual `systemctl start` after every reboot.

---

## 13. Open the Firewall for Port 8080

```bash
ansible workers -b -m ufw -a "rule=allow port=8080 proto=tcp" -K
```

**Why:** If `ufw` is active on the worker, it will silently drop inbound connections to 8080 even though Jenkins is listening — the browser will simply time out. This step is a no-op if `ufw` is inactive.

**Check `ufw` status first:**
```bash
ansible workers -b -a "ufw status" -K
```
If it reports `Status: inactive`, this step can be skipped. On cloud VMs, also check the provider's security group / network ACL — a local firewall rule doesn't override a cloud-level block.

---

## 14. Check Port 8080 Is Listening

```bash
ansible workers -b -m shell -a "ss -lntp | grep 8080" -K
```

**Why:** Confirms Jenkins is bound to and listening on TCP 8080, independent of whether the firewall allows reaching it. Useful for isolating "service problem" vs. "network/firewall problem" when the browser can't connect.

---

## 15. Retrieve the Initial Admin Password

```bash
ansible workers -b -m command -a "cat /var/lib/jenkins/secrets/initialAdminPassword" -K
```

**Why:** Jenkins generates a one-time bootstrap password on first launch, required to unlock the setup wizard. The file is only readable by root/`jenkins`, hence `-b` is required.

**Keep this value private** — treat it like any other credential, even though it's only used once.

---

## 16. Complete Setup in the Browser

This part is manual — there's no headless Ansible module for the Jenkins setup wizard.

1. **Open Jenkins:** `http://<worker-ip>:8080` (find the IP with `ansible workers -a "hostname -I"` if needed)
2. **Unlock Jenkins:** paste the password from Step 15, click **Continue**
3. **Install plugins:** choose **Install suggested plugins** — gives a working baseline (Git, pipelines, credentials) without manually selecting dozens of plugins up front; more can be added later under **Manage Jenkins → Plugins**
4. **Create the first admin user:** username, strong password, full name, email — this replaces the one-time bootstrap password with a named, ongoing credential
5. **Instance configuration:** confirm the Jenkins URL (default is fine for a lab), then **Save and Finish → Start using Jenkins**

---

## Security Considerations

- **Rotate/retire the bootstrap password.** Once the admin user is created in Step 16, the `initialAdminPassword` file is no longer needed — it isn't automatically deleted, so don't rely on it as a long-term credential.
- **Scope the firewall rule.** `ufw allow 8080` opens the port to any source by default. For anything beyond a lab, restrict it to a specific source (e.g. `ufw allow from <trusted-ip> to any port 8080 proto tcp`) or put Jenkins behind a reverse proxy (nginx/Apache) with TLS instead of exposing 8080 directly.
- **Don't run build jobs as root.** Jenkins itself runs under the `jenkins` system user by default — avoid granting it broader sudo rights than a given pipeline actually needs.
- **Keep Jenkins and plugins patched.** Jenkins and its plugins are common attack surface; enable and check **Manage Jenkins → Plugins → Updates** periodically, and track the Jenkins security advisories.
- **Protect the become (sudo) password.** `-K` prompts interactively; avoid hardcoding sudo passwords in scripts or committing them to version control. Prefer SSH-key-based `become` alternatives (e.g. `NOPASSWD` sudoers entries scoped narrowly, or Ansible Vault for secrets used inside playbooks).

---

## Troubleshooting Matrix

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | `"msg": "Missing sudo password"` | Used `-b` without `-K` | Add `-K`: `ansible workers -b -m apt -a "update_cache=yes" -K` |
| 2 | `UNREACHABLE ... Permission denied (publickey,password)` after running `sudo ansible ...` | Running Ansible itself as root can use root's SSH keys/config instead of your normal user's | Don't prefix with `sudo`. Use `ansible workers -b -K ...` so escalation happens on the *remote* host via your normal SSH login |
| 3 | `"msg": "No package matching 'state' is available"` | Wrote `name=pkg,state=present` — the comma merges `state=present` into the package name list | Space-separate distinct arguments: `name=pkg state=present`. Commas are only for multiple values *within* one argument, e.g. `name=curl,gnupg` |
| 4 | `FAILED! => {"msg": "Incorrect sudo password"}` | Mistyped the become password at the `-K` prompt | Re-run the command and enter the correct sudo password for the user on the worker |
| 5 | `java: command not found` / `[Errno 2] No such file or directory: b'java'` | Java isn't installed yet | Run Step 3, then verify with `ansible workers -a "java -version"` |
| 6 | `Unable to locate package jenkins` | Repository added but apt cache not refreshed afterward | Check `ansible workers -a "cat /etc/apt/sources.list.d/jenkins.list"`, then re-run Step 8, then Step 9 |
| 7 | `NO_PUBKEY` or `repository is not signed` | Signing key missing, moved, or `signed-by` path mismatch | Confirm the key exists (`ls -l /etc/apt/keyrings/jenkins-keyring.asc`) and that the `signed-by=` path in `jenkins.list` matches it exactly |
| 8 | Jenkins service not running | Service failed to start or was never started | Check `systemctl status jenkins --no-pager`; start with `ansible workers -b -m service -a "name=jenkins state=started" -K`; inspect `journalctl -u jenkins -n 50 --no-pager` for the root cause |
| 9 | Browser can't reach `http://<worker-ip>:8080` | Service down, firewall blocking 8080, or wrong IP | Check `systemctl is-active jenkins`, check `ss -lntp \| grep 8080`, confirm IP with `hostname -I`, confirm `ufw` allows 8080 (Step 13). On VirtualBox/cloud, also check host-level network reachability |
| 10 | Port 8080 already in use | Another process bound to 8080 before Jenkins started | `ss -lntp \| grep :8080` to identify the process; check `journalctl -u jenkins -n 100 --no-pager` for the resulting bind error |
| 11 | `cat: .../secrets/<password-value>`: No such file or directory | Accidentally used the *password string* as a path instead of the actual secrets file path | Re-run: `cat /var/lib/jenkins/secrets/initialAdminPassword` — the password is a value, not a filename |
| 12 | Permission denied reading `initialAdminPassword` | Command run without privilege escalation | Ensure `-b` (and `-K` if needed) is present: `ansible workers -b -m command -a "cat /var/lib/jenkins/secrets/initialAdminPassword" -K` |

---

## Useful Jenkins Commands

| Purpose | Command |
|---|---|
| Check status | `ansible workers -b -m command -a "systemctl status jenkins --no-pager" -K` |
| Start | `ansible workers -b -m service -a "name=jenkins state=started" -K` |
| Stop | `ansible workers -b -m service -a "name=jenkins state=stopped" -K` |
| Restart | `ansible workers -b -m service -a "name=jenkins state=restarted" -K` |
| Enable at boot | `ansible workers -b -m service -a "name=jenkins enabled=yes" -K` |
| View recent logs | `ansible workers -b -m command -a "journalctl -u jenkins -n 50 --no-pager" -K` |
| Check Java | `ansible workers -a "java -version"` |
| Check Jenkins package | `ansible workers -b -m shell -a "dpkg -l \| grep jenkins" -K` |
| Check listening port | `ansible workers -b -m shell -a "ss -lntp \| grep 8080" -K` |
| Check firewall status | `ansible workers -b -a "ufw status" -K` |

---

## Ansible Concepts Practiced

**Modules used:** `apt`, `file`, `get_url`, `apt_repository`, `command`, `shell`, `service`, `ufw`

**Concepts covered:** privilege escalation (`become`/`-K`/sudo), third-party package repositories, GPG signing keys, systemd service management, Java runtime dependencies, firewall rules, network port verification, service log inspection, remote package installation, idempotence.

---

## Appendix A — Reusable Playbook

The ad-hoc commands above are useful for learning and one-off debugging, but the natural next step is converting them into a single, reusable, idempotent playbook — this is the core advantage of configuration management over manual commands.

`jenkins-install.yml`:

```yaml
---
- name: Install Jenkins on Ubuntu workers
  hosts: workers
  become: true

  vars:
    jenkins_key_url: https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key
    jenkins_keyring: /etc/apt/keyrings/jenkins-keyring.asc
    jenkins_repo: "deb [signed-by={{ jenkins_keyring }}] https://pkg.jenkins.io/debian-stable binary/"

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes

    - name: Install Java 21 (JRE)
      apt:
        name: openjdk-21-jre
        state: present

    - name: Install repository prerequisites
      apt:
        name:
          - curl
          - gnupg
        state: present

    - name: Create apt keyrings directory
      file:
        path: /etc/apt/keyrings
        state: directory
        mode: "0755"

    - name: Download Jenkins signing key
      get_url:
        url: "{{ jenkins_key_url }}"
        dest: "{{ jenkins_keyring }}"
        mode: "0644"

    - name: Add Jenkins apt repository
      apt_repository:
        repo: "{{ jenkins_repo }}"
        filename: jenkins
        state: present

    - name: Update apt cache after adding repository
      apt:
        update_cache: yes

    - name: Install Jenkins
      apt:
        name: jenkins
        state: present

    - name: Ensure Jenkins is started and enabled at boot
      service:
        name: jenkins
        state: started
        enabled: yes

    - name: Allow port 8080 through ufw
      community.general.ufw:
        rule: allow
        port: "8080"
        proto: tcp
      ignore_errors: true   # no-op safely if ufw isn't installed/active

    - name: Wait for Jenkins to report ready in the log
      wait_for:
        path: /var/log/jenkins/jenkins.log
        search_regex: "Jenkins is fully up and running"
        timeout: 180
      ignore_errors: true   # log path can vary; don't fail the whole run on this check

    - name: Read the initial admin password
      command: cat /var/lib/jenkins/secrets/initialAdminPassword
      register: jenkins_initial_password
      changed_when: false

    - name: Show the initial admin password
      debug:
        msg: "Initial Jenkins admin password: {{ jenkins_initial_password.stdout }}"
```

**Run it with:**

```bash
ansible-playbook jenkins-install.yml -K
```

**Why this is worth doing:**
- **Idempotent by design** — every task uses `state:` declarations, so re-running the playbook against a host that's already configured makes no unnecessary changes
- **Reusable** — install Jenkins on a second worker by adding it to the `workers` group and running the same playbook, no manual command repetition
- **Self-documenting** — the task names and structure describe the install process better than a shell history ever could
- **Extensible** — variables (`jenkins_key_url`, etc.) can be overridden per-environment (e.g. a different Jenkins release line) without editing the tasks themselves

The `community.general.ufw` module requires the `community.general` collection (`ansible-galaxy collection install community.general`) — if it's not installed, that task will fail; it's marked `ignore_errors` so it doesn't block the rest of the install on a lab box without it.
