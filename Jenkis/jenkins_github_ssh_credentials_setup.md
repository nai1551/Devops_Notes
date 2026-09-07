# Jenkins + GitHub SSH Credentials Setup Guide

**Level:** Beginner-friendly
**Goal:** Connect a Jenkins server/agent to a GitHub repository using SSH credentials, so Jenkins can clone and pull your code securely without a username/password.

---

## Table of Contents

1. [Prerequisites & Glossary](#1-prerequisites--glossary)
2. [Security Warning](#2-security-warning)
3. [What We're Building (Concept Overview)](#3-what-were-building-concept-overview)
4. [Understand the Linux Users Involved](#4-understand-the-linux-users-involved)
5. [Step 1 — Prepare the Jenkins SSH Directory](#5-step-1--prepare-the-jenkins-ssh-directory)
6. [Step 2 — Generate an SSH Key Pair](#6-step-2--generate-an-ssh-key-pair)
7. [Step 3 — Set Correct Ownership & Permissions](#7-step-3--set-correct-ownership--permissions)
8. [Step 4 — Add the Public Key to GitHub](#8-step-4--add-the-public-key-to-github)
9. [Step 5 — Trust GitHub's Host Key (`known_hosts`)](#9-step-5--trust-githubs-host-key-known_hosts)
10. [Step 6 — Test SSH as the Jenkins User](#10-step-6--test-ssh-as-the-jenkins-user)
11. [Understanding the Two Common SSH Errors](#11-understanding-the-two-common-ssh-errors)
12. [Step 7 — Add the SSH Credential in Jenkins](#12-step-7--add-the-ssh-credential-in-jenkins)
13. [Step 8 — Configure the Jenkins Pipeline to Use SSH](#13-step-8--configure-the-jenkins-pipeline-to-use-ssh)
14. [Optional: Explicit SSH Config File](#14-optional-explicit-ssh-config-file)
15. [Troubleshooting Reference](#15-troubleshooting-reference)
16. [Final Verification Sequence](#16-final-verification-sequence)
17. [Complete Command Reference](#17-complete-command-reference)
18. [Final Checklist](#18-final-checklist)
19. [Key Lessons & Conclusion](#19-key-lessons--conclusion)

---

## 1. Prerequisites & Glossary

**Before you start, you should have:**
- A Jenkins server already installed and running.
- Root or `sudo` access to the machine Jenkins runs on.
- A GitHub account with access to the target repository.

**Key terms explained:**

| Term | What it means |
|---|---|
| **SSH key pair** | Two mathematically linked files: a **private key** (kept secret) and a **public key** (safe to share). Together they let you authenticate without a password. |
| **`ssh-keygen`** | The command-line tool used to generate a new SSH key pair. |
| **`known_hosts`** | A file that stores the "fingerprint" of servers you've already connected to and trust — this is *host verification*, separate from your key pair. |
| **Jenkins credential** | A securely stored secret (like an SSH private key) that Jenkins uses to authenticate to external services such as GitHub. |
| **`jenkins` user** | The Linux system account that the Jenkins service runs as. Its home directory is typically `/var/lib/jenkins`. |
| **`sudo -u jenkins <command>`** | Runs a command *as* the `jenkins` user, which is essential for testing SSH exactly the way Jenkins will use it. |
| **SSH remote URL** | A Git repository address in the form `git@github.com:USERNAME/REPO.git`, used for SSH-based (rather than HTTPS-based) access. |

---

## 2. Security Warning

> ⚠️ **Never share your SSH private key** — not in screenshots, GitHub repos, chat messages, documentation, public websites, or Jenkins console logs.

A private key looks like this:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

Only the **`.pub`** file (the public key) is safe to share — that's the one that goes on GitHub.

If a private key is ever exposed, **generate a new key pair immediately** and replace the old public key on GitHub.

---

## 3. What We're Building (Concept Overview)

```text
                    SSH
 Jenkins  ─────────────────────────────▶  GitHub
    │                                        │
    │ Private Key                            │ Public Key
    │                                        │
    └──────────── Jenkins Credential ────────┘
```

Jenkins needs **two separate things** to talk to GitHub over SSH:

| Concern | Question it answers | Where it lives |
|---|---|---|
| **Authentication** | "Am I really Jenkins, and am I allowed in?" | Private key on Jenkins ↔ matching public key on GitHub |
| **Host verification** | "Am I really talking to GitHub, and not an impostor?" | GitHub's server fingerprint stored in Jenkins' `known_hosts` file |

These are independent checks — fixing one does not automatically fix the other, and both must pass for Jenkins to successfully clone a repository.

---

## 4. Understand the Linux Users Involved

SSH configuration is **user-specific** — a key that works for one Linux user does not automatically work for another. A typical server might have several users:

```text
root
worker
jenkins
jenkins-agent
```

Each has its own separate SSH directory:

| User | SSH directory |
|---|---|
| `root` | `/root/.ssh/` |
| `worker` | `/home/worker/.ssh/` |
| `jenkins` (service account) | `/var/lib/jenkins/.ssh/` |

> **Beginner note:** If Jenkins performs Git operations as the `jenkins` user, its SSH files must exist under `/var/lib/jenkins/.ssh/`. Don't assume that because SSH works when you're logged in as `root`, it will also work for Jenkins — they have completely separate environments. This is the single most common source of confusion when setting this up for the first time.

---

## 5. Step 1 — Prepare the Jenkins SSH Directory

Become root:

```bash
sudo -i
```

Confirm the Jenkins home directory:

```bash
cd /var/lib/jenkins
pwd
```

Expected output:

```text
/var/lib/jenkins
```

Create the `.ssh` directory if it doesn't already exist:

```bash
mkdir -p /var/lib/jenkins/.ssh
chown jenkins:jenkins /var/lib/jenkins/.ssh
chmod 700 /var/lib/jenkins/.ssh
```

Confirm it looks like this:

```text
drwx------ jenkins jenkins .ssh
```

---

## 6. Step 2 — Generate an SSH Key Pair

Generate a modern ED25519 key pair directly into the Jenkins SSH directory:

```bash
ssh-keygen -t ed25519 -f /var/lib/jenkins/.ssh/id_ed25519
```

Using `-f` explicitly tells `ssh-keygen` where to save the key, avoiding the interactive prompt.

This produces two files:

| File | Meaning |
|---|---|
| `id_ed25519` | **Private key** — must stay secret, never leaves this server |
| `id_ed25519.pub` | **Public key** — this is what you add to GitHub |

> **Beginner note — passphrase:** For automated CI/CD, most setups use a key **without a passphrase**, since Jenkins needs to authenticate non-interactively (no one is around to type it in). If you do set a passphrase, Jenkins must be configured to supply it securely.

### Common mistakes to avoid

- **Don't** run `touch /var/lib/jenkins/.ssh/id_ed25519` — this creates an empty, useless file, not a real key. If you did this by accident, delete it (`rm /var/lib/jenkins/.ssh/id_ed25519`) and re-run `ssh-keygen`.
- **Don't** save the key directly in `/var/lib/jenkins/id_ed25519` — it must go inside the `.ssh/` subdirectory:

```text
/var/lib/jenkins/
└── .ssh/
    ├── id_ed25519
    └── id_ed25519.pub
```

### Verify the files exist

```bash
ls -lah /var/lib/jenkins/.ssh/
cat /var/lib/jenkins/.ssh/id_ed25519.pub
```

The public key should look like:

```text
ssh-ed25519 AAAA... comment
```

Do **not** run `cat` on the private key and paste the output anywhere — only inspect it locally if truly necessary.

---

## 7. Step 3 — Set Correct Ownership & Permissions

```bash
chown -R jenkins:jenkins /var/lib/jenkins/.ssh
chmod 700 /var/lib/jenkins/.ssh
chmod 600 /var/lib/jenkins/.ssh/id_ed25519
chmod 644 /var/lib/jenkins/.ssh/id_ed25519.pub
```

**The rule to remember:**

| Item | Permission | Reason |
|---|---|---|
| `.ssh` directory | `700` | Only the owner can enter it |
| Private key | `600` | Only the owner can read/write it |
| Public key | `644` | Safe to be world-readable |

> Note: `chmod 400` on the public key is unnecessary — `644` is the normal, correct permission for a `.pub` file.

---

## 8. Step 4 — Add the Public Key to GitHub

Display and copy the public key (the entire single line):

```bash
cat /var/lib/jenkins/.ssh/id_ed25519.pub
```

In GitHub: **Settings → SSH and GPG keys → New SSH key**

Give it a descriptive title, e.g. `Jenkins Worker Server`, and paste the key.

> ⚠️ Make sure you paste `id_ed25519.pub` (public), **never** `id_ed25519` (private).

**Repository access:** the GitHub account that owns this key must have access to the target repository. The SSH remote URL follows this format:

```text
git@github.com:USERNAME/REPOSITORY.git
```

Example:

```text
git@github.com:na1551/jenkins-pipeline-demo.git
```

---

## 9. Step 5 — Trust GitHub's Host Key (`known_hosts`)

`known_hosts` is a **separate concept** from your key pair — it records the fingerprints of servers you've already verified, so SSH can detect if you're ever connecting to an impostor server.

The easiest way to populate it correctly is to just attempt a real connection as the Jenkins user:

```bash
sudo -u jenkins ssh -T git@github.com
```

On the first connection, you'll see something like:

```text
The authenticity of host 'github.com' can't be established.
ED25519 key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

After confirming the fingerprint matches GitHub's official one, type `yes`. This adds GitHub's key to:

```text
/var/lib/jenkins/.ssh/known_hosts
```

Confirm it now exists:

```bash
ls -lah /var/lib/jenkins/.ssh/
```

You should now see all three files:

```text
id_ed25519
id_ed25519.pub
known_hosts
```

> 🚫 Do **not** disable SSH host-key checking just to make an error disappear — it exists specifically to protect against connecting to a malicious impostor server.

---

## 10. Step 6 — Test SSH as the Jenkins User

This is the most important command in this whole guide:

```bash
sudo -u jenkins ssh -T git@github.com
```

This runs SSH **as the `jenkins` user** — exactly how Jenkins itself will connect — rather than as `root`, whose SSH environment is entirely separate.

A successful response looks like:

```text
Hi USERNAME! You've successfully authenticated,
but GitHub does not provide shell access.
```

This message is expected and correct — GitHub allows SSH authentication for Git operations, but doesn't give you an interactive shell.

**Once that works, test the actual repository:**

```bash
sudo -u jenkins git ls-remote git@github.com:na1551/jenkins-pipeline-demo.git
```

A successful result looks like:

```text
<commit-hash>    HEAD
<commit-hash>    refs/heads/main
```

This single command conveniently verifies SSH connectivity, GitHub authentication, *and* repository access all at once.

---

## 11. Understanding the Two Common SSH Errors

| Error | What it means | Fix |
|---|---|---|
| `No ED25519 host key is known for github.com` / `Host key verification failed` | Jenkins doesn't yet trust GitHub's server fingerprint — a **host verification** problem, not an authentication problem. Jenkins hasn't even reached the authentication step yet. | Run `sudo -u jenkins ssh -T git@github.com` and accept GitHub's fingerprint (see [Step 5](#9-step-5--trust-githubs-host-key-known_hosts)). |
| `git@github.com: Permission denied (publickey)` | GitHub was reached successfully, but rejected the key offered — an **authentication** problem. | Check: the public key was added to GitHub; it's the *matching* key pair; it belongs to the correct GitHub account; Jenkins can read the private key; permissions are correct (see [Troubleshooting](#15-troubleshooting-reference)). |

**Progression through a successful fix looks like this:**

```text
Jenkins ──▶ github.com
              │
        ✗ Host key unknown        →  Fix: accept fingerprint, populate known_hosts
              │
        ✓ Host verified
        ✗ Public-key auth failed  →  Fix: add matching public key to GitHub
              │
        ✓ Host verified
        ✓ SSH authentication
              │
              ▼
       GitHub repository access
```

---

## 12. Step 7 — Add the SSH Credential in Jenkins

Navigate to:

**Manage Jenkins → Credentials → System → Global credentials → Add Credentials**

Set:

| Field | Value |
|---|---|
| **Kind** | `SSH Username with private key` |
| **Username** | `git` |
| **Private Key** | Choose "Enter directly", then paste the **private key** matching the public key added to GitHub |
| **Passphrase** | Leave empty if the key has none; otherwise enter it |
| **ID** | A descriptive ID, e.g. `github-ssh-jenkins` |
| **Description** | e.g. `SSH key for Jenkins GitHub access` |

The private key you paste should look like:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

> ⚠️ Paste the **private** key here — never the `.pub` file.

### Public key vs. private key — the concept to internalize

| Location | Which key goes here |
|---|---|
| Jenkins credential | **Private** key (`id_ed25519`) |
| GitHub SSH keys settings | **Public** key (`id_ed25519.pub`) |
| Jenkins `known_hosts` | GitHub's *server* host key (not your key pair at all) |

They are mathematically linked — never reverse them.

---

## 13. Step 8 — Configure the Jenkins Pipeline to Use SSH

In your Pipeline job configuration:

**Pipeline → Definition → Pipeline script from SCM**

| Field | Value |
|---|---|
| **SCM** | `Git` |
| **Repository URL** | `git@github.com:na1551/jenkins-pipeline-demo.git` |
| **Credentials** | Select the credential ID you created (e.g. `github-ssh-jenkins`) |
| **Branch** | `*/main` |
| **Script Path** | `Jenkinsfile` |

**Why an SSH URL and not HTTPS?** This guide is specifically about SSH-based authentication, which pairs your private key (on Jenkins) with your public key (on GitHub). An HTTPS URL (`https://github.com/...`) would instead use a different authentication method (token or username/password), which this setup doesn't use.

### Useful commands for verifying the Jenkins user's environment

```bash
sudo -u jenkins whoami                        # expect: jenkins
sudo -u jenkins sh -c 'echo $HOME'             # expect: /var/lib/jenkins
sudo -u jenkins ls -lah /var/lib/jenkins/.ssh/
sudo -u jenkins git --version
sudo -u jenkins ssh -V
```

---

## 14. Optional: Explicit SSH Config File

If multiple SSH keys exist on the server, you can pin exactly which key to use for GitHub by creating a config file:

```bash
cat > /var/lib/jenkins/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile /var/lib/jenkins/.ssh/id_ed25519
    IdentitiesOnly yes
EOF

chown jenkins:jenkins /var/lib/jenkins/.ssh/config
chmod 600 /var/lib/jenkins/.ssh/config
```

For a simple, single-key setup this usually isn't necessary, but it removes any ambiguity about which key SSH selects.

---

## 15. Troubleshooting Reference

| Symptom | Likely Cause | Fix |
|---|---|---|
| `No ED25519 host key is known for github.com` | GitHub's fingerprint isn't in `known_hosts` yet | Run `sudo -u jenkins ssh -T git@github.com` and accept the fingerprint |
| `Permission denied (publickey)` | Wrong or missing public key on GitHub | Verify `cat /var/lib/jenkins/.ssh/id_ed25519.pub` matches exactly what's registered on the correct GitHub account |
| Jenkins can't read the private key | Wrong ownership/permissions | `chown jenkins:jenkins id_ed25519` and `chmod 600 id_ed25519` |
| Wrong owner on `.ssh` directory | Files created as `root` instead of `jenkins` | `chown -R jenkins:jenkins /var/lib/jenkins/.ssh` |
| SSH works as `root` but fails for Jenkins | Testing under the wrong user — `root` and `jenkins` have separate SSH environments | Always test with `sudo -u jenkins ssh -T git@github.com` |
| `chmod: command not found` / garbled command | Terminal control characters got pasted in (e.g. `^[[200~`) | Retype the command manually instead of pasting |
| `chown ... /var/lib/jenkins/.ssh~: No such file or directory` | Stray `~` accidentally typed after the path | Remove the trailing `~` — it isn't part of the directory name |
| Offering the wrong key / unclear which key SSH is using | Multiple keys present, none pinned | Run `sudo -u jenkins ssh -vT git@github.com` and look for the `Offering public key:` line, or add an explicit [SSH config](#14-optional-explicit-ssh-config-file) |

### Deeper debugging

For verbose SSH diagnostics (shows which config is loaded, which keys are tried, and whether `known_hosts` is being read):

```bash
sudo -u jenkins ssh -vT git@github.com     # verbose
sudo -u jenkins ssh -vvvT git@github.com   # maximum verbosity
```

> Never paste private-key contents from debug output into documentation, tickets, or chat.

### Quick decision tree

```text
Jenkins cannot clone repository
            │
            ▼
Does `sudo -u jenkins ssh -T git@github.com` succeed?
            │
     ┌──────┴──────┐
     NO            YES
     │              │
     ▼              ▼
Check SSH key   Run: sudo -u jenkins git ls-remote <repo>
+ known_hosts        │
                ┌─────┴─────┐
                NO          YES
                │             │
                ▼             ▼
          Check repo      SSH/Git access is
          permissions      working — check the
          on GitHub        Jenkins credential config
```

---

## 16. Final Verification Sequence

Run through these in order when troubleshooting from scratch:

1. **Check files exist:**
   ```bash
   ls -lah /var/lib/jenkins/.ssh/
   ```
   Expect: `id_ed25519`, `id_ed25519.pub`, `known_hosts`

2. **Check ownership** — should be `jenkins jenkins` on all files.

3. **Check private-key permission:**
   ```bash
   chmod 600 /var/lib/jenkins/.ssh/id_ed25519
   ```

4. **Check directory permission:**
   ```bash
   chmod 700 /var/lib/jenkins/.ssh
   ```

5. **Test SSH as Jenkins:**
   ```bash
   sudo -u jenkins ssh -T git@github.com
   ```
   Expect the "successfully authenticated" message.

6. **Test the repository:**
   ```bash
   sudo -u jenkins git ls-remote git@github.com:na1551/jenkins-pipeline-demo.git
   ```

7. **Test in Jenkins** using Repository URL `git@github.com:na1551/jenkins-pipeline-demo.git`, credential type `SSH Username with private key`, username `git`, then run the job.

---

## 17. Complete Command Reference

A compact copy-pasteable summary of the whole setup:

```bash
sudo -i

mkdir -p /var/lib/jenkins/.ssh
chown jenkins:jenkins /var/lib/jenkins/.ssh
chmod 700 /var/lib/jenkins/.ssh

ssh-keygen -t ed25519 -f /var/lib/jenkins/.ssh/id_ed25519

chown -R jenkins:jenkins /var/lib/jenkins/.ssh
chmod 600 /var/lib/jenkins/.ssh/id_ed25519
chmod 644 /var/lib/jenkins/.ssh/id_ed25519.pub

cat /var/lib/jenkins/.ssh/id_ed25519.pub
# → Add this to GitHub: Settings → SSH and GPG keys → New SSH key

sudo -u jenkins ssh -T git@github.com
# → type "yes" on first connection to trust GitHub's host key

sudo -u jenkins git ls-remote git@github.com:na1551/jenkins-pipeline-demo.git
```

---

## 18. Final Checklist

Before running the Jenkins pipeline, confirm:

- [ ] `/var/lib/jenkins/.ssh/` exists and is owned by `jenkins`
- [ ] `id_ed25519` (private key) and `id_ed25519.pub` (public key) both exist
- [ ] Private key permission is `600`; directory permission is `700`
- [ ] Public key has been added to the correct GitHub account
- [ ] `known_hosts` contains GitHub's host key
- [ ] `sudo -u jenkins ssh -T git@github.com` succeeds
- [ ] `sudo -u jenkins git ls-remote <repo>` succeeds
- [ ] Jenkins credential type is `SSH Username with private key`
- [ ] Jenkins credential username is `git`
- [ ] Jenkins credential's private key matches the public key on GitHub
- [ ] Pipeline's Repository URL uses the SSH format (`git@github.com:...`)
- [ ] Pipeline is configured to use the correct credential and points to the correct `Jenkinsfile`

---

## 19. Key Lessons & Conclusion

**The original problem** was an SSH **host-key verification** failure:

```text
No ED25519 host key is known for github.com
```

Once GitHub's host key was added to the Jenkins user's `known_hosts` (by accepting the fingerprint during a manual test), authentication could proceed. The successful test:

```bash
sudo -u jenkins ssh -T git@github.com
```

returning:

```text
Hi USERNAME! You've successfully authenticated,
but GitHub does not provide shell access.
```

confirms the Jenkins Linux user can authenticate to GitHub over SSH. The final piece is making sure the **same private key** is stored in the Jenkins credential, with the corresponding **public key** registered on GitHub — then using that credential with the SSH repository URL in the Jenkins Pipeline configuration.

**Takeaways worth remembering:**

1. **Test as the `jenkins` user, not `root`.** They have completely separate SSH environments (`/var/lib/jenkins/.ssh/` vs `/root/.ssh/`) — success under one proves nothing about the other.
2. **`known_hosts` ≠ your key pair.** One verifies *the server* (GitHub); the other authenticates *you* (Jenkins).
3. **The `.pub` file goes to GitHub; the private key goes into the Jenkins credential.** Never reverse them.
4. **Never disable host-key checking** just to silence an error — it exists to catch impostor servers.
5. **Debug in layers**, in this order: host verification → SSH authentication → Git repository access → Jenkins credential → Jenkins pipeline. Isolating which layer fails makes troubleshooting far faster.
