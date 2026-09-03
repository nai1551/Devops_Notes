# Installing Jenkins on Ubuntu Workers with Ansible

This guide documents installing Jenkins on Ubuntu 24.04 (Noble) worker nodes from a control machine (`master-server`) using ad-hoc Ansible commands. Each step explains *why* it's needed, and a troubleshooting section covers the errors that came up along the way.

## Prerequisites

- A `workers` group defined in your Ansible inventory
- SSH access from the master to the worker(s), with a sudo-capable user
- Worker OS: Ubuntu 24.04.3 LTS ("Noble Numbat") — confirmed with:

```bash
ansible workers -a "cat /etc/os-release"
```

---

## Step 1 — Check connectivity and sudo access

```bash
ansible workers -m ping
```

**Why:** Before touching packages, confirm Ansible can reach the host and that Python is available for module execution. A healthy response looks like `"ping": "pong"`.

If you plan to run privileged (`-b`/`--become`) tasks, always pass `-K` so Ansible prompts for the become (sudo) password:

```bash
ansible workers -b -m apt -a "update_cache=yes" -K
```

**Why `-K` matters:** Without it, Ansible either fails with `"Missing sudo password"` or, if you prefix the whole command with `sudo` (running Ansible itself as root instead of asking each host to become root), you can end up authenticating with the *wrong* SSH identity and get `UNREACHABLE` / `Permission denied (publickey,password)`. `-K` (become) is the correct way to escalate privileges *on the remote host*, not on the control node.

---

## Step 2 — Install Java (Jenkins requirement)

Jenkins runs on the JVM, so a JDK/JRE must be present first.

```bash
ansible workers -b -m apt -a "name=openjdk-21-jre state=present update_cache=yes" -K
```

**Why:** Jenkins 2.4xx+ requires Java 17 or 21. We install the JRE (not the full JDK) since Jenkins only needs to *run* on the JVM, not compile Java code.

**Common mistake to avoid:** writing the module args as
```
name=openjdk-21-jre,state=present
```
This fails with `No package matching 'state' is available` because the comma makes Ansible treat `state=present` as part of the package *name* list. Module arguments must be **space-separated key=value pairs**, only individual package names inside `name=` are comma-separated:
```
name=openjdk-21-jre state=present
```

Verify installation:
```bash
ansible workers -a "java -version"
```
Expected output shows something like `openjdk version "21.0.12"`.

---

## Step 3 — Install prerequisite tools

```bash
ansible workers -b -m apt -a "name=curl,gnupg state=present" -K
```

**Why:** `curl` and `gnupg` are needed to fetch and verify Jenkins' signing key over HTTPS. Note the correct comma usage here: multiple *package names* under one `name=` argument, followed by a separate `state=` argument.

---

## Step 4 — Create the keyrings directory

```bash
ansible workers -b -m file -a "path=/etc/apt/keyrings state=directory mode=0755" -K
```

**Why:** Modern Debian/Ubuntu apt no longer trusts keys dropped into `/etc/apt/trusted.gpg.d` by default for third-party repos. The current best practice is to store each repo's signing key in `/etc/apt/keyrings/` and reference it explicitly per-repository with `signed-by=`. This avoids that key being trusted for *all* repos on the system — better security isolation.

---

## Step 5 — Download the Jenkins GPG key

```bash
ansible workers -b -m get_url -a "url=https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key dest=/etc/apt/keyrings/jenkins-keyring.asc mode=0644" -K
```

**Why:** This key lets apt cryptographically verify that packages from the Jenkins repo actually come from Jenkins and haven't been tampered with. `get_url` also downloads *idempotently* — rerunning it won't re-download if the file is unchanged, and Ansible reports `checksum_src` to confirm what was fetched.

Verify:
```bash
ansible workers -a "ls -l /etc/apt/keyrings/jenkins-keyring.asc"
```

---

## Step 6 — Add the Jenkins apt repository

```bash
ansible workers -b -m apt_repository -a "repo='deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/' filename=jenkins state=present" -K
```

**Why:** This tells apt where to find Jenkins packages and which key to trust for them. `signed-by=` scopes trust to *this repo only*, using the key from Step 5. `filename=jenkins` controls the name of the resulting file: `/etc/apt/sources.list.d/jenkins.list`.

Verify:
```bash
ansible workers -a "cat /etc/apt/sources.list.d/jenkins.list"
```

---

## Step 7 — Refresh the apt cache

```bash
ansible workers -b -m apt -a "update_cache=yes" -K
```

**Why:** apt needs to re-index its package lists after adding a new repository, otherwise it won't know Jenkins packages exist yet, and installation will fail with an "unable to locate package" error.

---

## Step 8 — Install Jenkins

```bash
ansible workers -b -m apt -a "name=jenkins state=present" -K
```

**Why:** This pulls Jenkins and its dependency `net-tools`, unpacks the package, and — critically — the postinstall script automatically:
- creates the `jenkins` system service
- enables and starts it via systemd (`Created symlink .../jenkins.service`)

Verify the package installed:
```bash
ansible workers -b -m shell -a "dpkg -l | grep jenkins" -K
```

---

## Step 9 — Confirm the service is running

```bash
ansible workers -b -m command -a "systemctl status jenkins --no-pager" -K
```

**Why:** Confirms Jenkins is `active (running)`, records the main PID, and — importantly — the startup logs will point you to the initial admin password file, needed for first-time setup through the web UI on port 8080.

---

## Step 10 — Retrieve the initial admin password

```bash
ansible workers -b -m command -a "cat /var/lib/jenkins/secrets/initialAdminPassword" -K
```

**Why:** Jenkins generates a one-time password on first boot and requires it to unlock the setup wizard at `http://<worker-ip>:8080`. This file is only readable by root/jenkins, which is why `-b` (become) is required to read it.

Copy the printed value (e.g. `337a6906e64341e9ad2606b09ba105ac`) and paste it into the "Unlock Jenkins" screen in your browser.

---

## Step 11 — Open the firewall for port 8080

```bash
ansible workers -b -m ufw -a "rule=allow port=8080 proto=tcp" -K
```

**Why:** Jenkins listens on port 8080 by default, but the worker's firewall (if `ufw` is active) blocks inbound connections to it until you explicitly allow the port. Without this, `http://<worker-ip>:8080` will time out in the browser even though the service is running.

Check `ufw` is actually active and the rule took effect:
```bash
ansible workers -b -a "ufw status" -K
```
If `ufw` reports `Status: inactive`, this step isn't needed — there's no local firewall blocking the port. If you're on a cloud VM, remember the security group / network firewall at the provider level may need the same port opened separately.

---

## Step 12 — Unlock Jenkins and install plugins

This step happens in the browser, not Ansible — open `http://<worker-ip>:8080`.

**Why manual:** The setup wizard runs interactively over HTTP; there's no headless Ansible module for it. The steps are:

1. Paste the password from Step 10 into "Unlock Jenkins"
2. Choose **Install suggested plugins** (covers Git, pipelines, credentials — the common baseline) unless you know you need a custom plugin set
3. Wait for the plugin installation screen to finish

**Why suggested plugins:** They give you a working CI baseline (source control, build pipelines, credential storage) without requiring you to hand-pick dozens of plugins before you've even used Jenkins once. You can always add/remove plugins later from **Manage Jenkins → Plugins**.

---

## Step 13 — Create the first admin user

Still in the setup wizard, after plugins finish installing, Jenkins prompts you to create an admin account.

**Why:** The `initialAdminPassword` from Step 10 is a one-time bootstrap credential, not meant for ongoing use. Creating a named admin user with its own password means:
- you're not sharing a single generic secret between admins
- the temporary password file can safely be ignored/rotated afterward
- future logins and audit logs show a real username instead of "admin"

Fill in username, password, full name, and email, then confirm the Jenkins URL on the final screen (defaults to `http://<worker-ip>:8080/` — fine to accept for internal/lab use).

At this point Jenkins is fully installed, reachable, and ready to configure jobs.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `[Errno 2] No such file or directory: b'java'` | Java isn't installed yet | Run Step 2 before anything else — Jenkins won't run without a JVM |
| `"msg": "Missing sudo password"` | Ran a `-b` (become) task without `-K` | Add `-K` so Ansible prompts for the become password |
| `UNREACHABLE ... Permission denied (publickey,password)` | Ran `sudo ansible ...` — this escalates the **local** Ansible process, not the **remote** connection, and can break which SSH identity/agent is used | Don't prefix `ansible` with `sudo`. Use `-b -K` instead so escalation happens on the target host via the normal SSH login |
| `"msg": "No package matching 'state' is available"` | Module args written as `name=pkg,state=present` — the comma merges `state=present` into the package name list | Space-separate distinct arguments: `name=pkg state=present`. Commas are only for multiple values *within* one argument, e.g. `name=curl,gnupg` |
| `FAILED! => {"msg": "Incorrect sudo password"}` | Mistyped the become password at the `-K` prompt | Just re-run the same command and re-enter the password correctly |
| `cat: .../secrets/<password>: No such file or directory` | Tried to `cat` the *password value* as if it were a *filename* (copy-paste/typo mixing up the command and its own output) | The password is a **value**, not a path. Read it with:<br>`cat /var/lib/jenkins/secrets/initialAdminPassword` — don't substitute the printed password string into a new path |
| Jenkins install completes but `dpkg -l | grep jenkins` shows nothing | Repo/key/cache steps were skipped or ran in the wrong order | Re-check Steps 4–7 ran successfully in order: keyring dir → download key → add repo → update cache → install |
| Can't reach `http://<worker-ip>:8080` in browser | Firewall blocking port 8080, or checking the wrong IP | Confirm the worker's IP (`ansible workers -a "hostname -I"`) and that port 8080 is open (`ansible workers -b -a "ss -tlnp | grep 8080" -K`) |

---

## Quick reference: full command sequence

```bash
ansible workers -m ping
ansible workers -b -m apt -a "name=openjdk-21-jre state=present update_cache=yes" -K
ansible workers -a "java -version"
ansible workers -b -m apt -a "name=curl,gnupg state=present" -K
ansible workers -b -m file -a "path=/etc/apt/keyrings state=directory mode=0755" -K
ansible workers -b -m get_url -a "url=https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key dest=/etc/apt/keyrings/jenkins-keyring.asc mode=0644" -K
ansible workers -b -m apt_repository -a "repo='deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/' filename=jenkins state=present" -K
ansible workers -b -m apt -a "update_cache=yes" -K
ansible workers -b -m apt -a "name=jenkins state=present" -K
ansible workers -b -m command -a "systemctl status jenkins --no-pager" -K
ansible workers -b -m command -a "cat /var/lib/jenkins/secrets/initialAdminPassword" -K
ansible workers -b -m ufw -a "rule=allow port=8080 proto=tcp" -K
# Then finish in the browser: unlock Jenkins → install suggested plugins → create admin user
```
