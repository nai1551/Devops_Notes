# Ansible Galaxy Role Practice: Installing Nginx with Variables and Templates

A hands-on lab for building a reusable **Ansible Galaxy role** that installs Nginx, deploys a custom HTML page from a Jinja2 template, and demonstrates how variables flow through a role.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Step 1 — Create the Role](#step-1--create-the-role)
5. [Step 2 — Inventory File](#step-2--inventory-file)
6. [Step 3 — Main Playbook](#step-3--main-playbook)
7. [Step 4 — Tasks](#step-4--tasks)
8. [Step 5 — Default Variable](#step-5--default-variable)
9. [Step 6 — Jinja2 Template](#step-6--jinja2-template)
10. [Step 7 — Syntax Check](#step-7--syntax-check)
11. [Step 8 — Run the Playbook](#step-8--run-the-playbook)
12. [Step 9 — Verify the Installation](#step-9--verify-the-installation)
13. [Troubleshooting](#troubleshooting)
14. [How Variable Flow Works](#how-variable-flow-works)
15. [Key Concepts (Interview Notes)](#key-concepts-interview-notes)
16. [What We Learned](#what-we-learned)
17. [Practice Exercises](#practice-exercises)
18. [Command Reference](#command-reference)
19. [Final Result](#final-result)

---

## Overview

An **Ansible Galaxy role** is a standardized, reusable folder structure for organizing automation (tasks, variables, templates, handlers, etc.) so it can be shared, versioned, and reused across playbooks and projects. This lab uses that structure to:

- Install and start Nginx on a remote host (`worker1`)
- Render a custom `index.html` page from a Jinja2 template
- Pass a variable (`user_name`) from the role's defaults into that template

By the end, visiting the worker's web page will display a personalized greeting like `Hi Naim`.

---

## Prerequisites

Before starting, make sure you have:

- A **control node** with Ansible installed (`ansible --version` to confirm)
- At least one **managed host** (`worker1`) reachable over SSH, with a sudo-capable user
- SSH key or password access from the control node to the worker
- Basic familiarity with YAML syntax

---

## Project Structure

```text
ansible/
├── inventory
├── install-nginx.yml
└── roles/
    └── nginx/
        ├── defaults/
        │   └── main.yml
        ├── files/
        ├── handlers/
        │   └── main.yml
        ├── meta/
        │   └── main.yml
        ├── tasks/
        │   └── main.yml
        ├── templates/
        │   └── index.html.j2
        ├── tests/
        │   ├── inventory
        │   └── test.yml
        ├── vars/
        │   └── main.yml
        └── README.md
```

**What each folder is for:**

| Folder/File          | Purpose                                            |
|-----------------------|-----------------------------------------------------|
| `defaults/main.yml`   | Default variable values (lowest priority, easy to override) |
| `files/`              | Static files copied as-is to the remote host        |
| `handlers/main.yml`   | Tasks triggered by `notify` (e.g., restart a service) |
| `meta/main.yml`       | Role metadata (author, dependencies, supported platforms) |
| `tasks/main.yml`      | The actual list of actions the role performs         |
| `templates/`          | Jinja2 (`.j2`) files rendered with variables          |
| `tests/`              | Sample inventory/playbook for testing the role in isolation |
| `vars/main.yml`       | Variables with higher priority than `defaults/`       |
| `README.md`           | Documentation for the role                           |

---

## Step 1 — Create the Role

```bash
mkdir -p ~/ansible/roles
cd ~/ansible
ansible-galaxy init roles/nginx
```

This scaffolds the entire directory structure shown above automatically.

---

## Step 2 — Inventory File

Create an `inventory` file listing the hosts Ansible will manage:

```ini
[workers]
worker1 ansible_host=192.168.56.11 ansible_user=worker
```

Test connectivity:

```bash
ansible workers -m ping
```

Expected output:

```json
{
  "ping": "pong"
}
```

> If this fails, double-check SSH access and that `ansible_user` has the correct permissions.

---

## Step 3 — Main Playbook (`vi install-nginx.yml`)

Create `install-nginx.yml`:

```yaml
---
- name: Install and configure Nginx
  hosts: workers
  become: yes

  roles:
    - nginx
```

**Explanation:**

| Key         | Meaning                                  |
|-------------|-------------------------------------------|
| `hosts`     | The inventory group this play targets     |
| `become`    | Escalates privileges (sudo) for tasks      |
| `roles`     | The list of roles to execute, in order     |

---

## Step 4 — Tasks (`vi roles/nginx/tasks/main.yml`)

Edit `roles/nginx/tasks/main.yml`:

```yaml
---
- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install Nginx
  apt:
    name: nginx
    state: present

- name: Start and enable Nginx
  service:
    name: nginx
    state: started
    enabled: yes

- name: Deploy custom HTML page
  template:
    src: index.html.j2
    dest: /var/www/html/index.html
    owner: root
    group: root
    mode: "0644"
```

**Modules used:**

| Module     | Purpose                                      |
|------------|-----------------------------------------------|
| `apt`      | Installs packages on Debian/Ubuntu systems     |
| `service`  | Starts, stops, and enables system services     |
| `template` | Renders a Jinja2 file and copies it to the host |

---

## Step 5 — Default Variable (`vi roles/nginx/defaults/main.yml`)

Edit `roles/nginx/defaults/main.yml`:

```yaml
---
user_name: "Naim"
```

**Why use `defaults/`?**

- Stores the role's default variable values
- Easy to override from a playbook, inventory, or `vars/` (which takes higher priority)

**Why not call the variable `name`?**

`name` is a reserved keyword in Ansible (used internally, e.g., in module parameters and task names), so `user_name` is used instead to avoid conflicts.

---

## Step 6 — Jinja2 Template (`vi roles/nginx/templates/index.html.j2`)

Edit `roles/nginx/templates/index.html.j2`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Ansible Galaxy Demo</title>
</head>
<body>

<h1>Hi {{ user_name }}</h1>

<p>This page was deployed using Ansible Galaxy Role and Jinja2 Template.</p>

</body>
</html>
```

**Jinja2 syntax used here:**

| Syntax             | Meaning                          |
|---------------------|-----------------------------------|
| `{{ user_name }}`   | Prints the value of `user_name`   |

Rendered output:

```html
<h1>Hi Naim</h1>
```

---

## Step 7 — Syntax Check

Before running anything against real hosts, validate the YAML:

```bash
ansible-playbook install-nginx.yml --syntax-check
```

This only checks syntax — it does not connect to hosts or make changes.

---

## Step 8 — Run the Playbook

```bash
ansible-playbook install-nginx.yml -K
```

`-K` (`--ask-become-pass`) prompts for the sudo password, required because the playbook uses `become: yes`.

---

## Step 9 — Verify the Installation

**Check Nginx status:**

```bash
systemctl status nginx
```

**Check the deployed HTML:**

```bash
cat /var/www/html/index.html
```

**Test with curl — on the worker itself:**

```bash
curl http://localhost
```

**Test with curl — from the control node:**

```bash
curl http://worker1
```

Expected page content:

```html
<h1>Hi Naim</h1>
```

---

## Troubleshooting

| Problem                     | Symptom / Error                                      | Fix                                                              |
|------------------------------|--------------------------------------------------------|--------------------------------------------------------------------|
| Missing sudo password        | `Missing sudo password`                                 | Re-run with `-K`: `ansible-playbook install-nginx.yml -K`          |
| Reserved variable name       | `Found variable using reserved name: name`               | Rename `name: "Naim"` → `user_name: "Naim"`                        |
| Undefined variable           | `AnsibleUndefinedVariable: 'Naim' is undefined`           | In the template, reference the variable itself: `{{ user_name }}`, not its value `{{ Naim }}` |

---

## How Variable Flow Works

```text
defaults/main.yml
        │
        │ user_name = "Naim"
        ▼
templates/index.html.j2
        │
        │ {{ user_name }}
        ▼
/var/www/html/index.html
        │
        ▼
Browser Output → Hi Naim
```

The variable is defined once in `defaults/main.yml`, referenced in the template, and rendered into the final HTML file served by Nginx.

---

## Key Concepts (Interview Notes)

| Concept    | Explanation                                              |
|------------|-------------------------------------------------------------|
| Role       | Reusable, self-contained automation component                |
| Playbook   | YAML file describing what automation to run and where        |
| Inventory  | List of managed hosts and groups                              |
| Task       | A single action executed by Ansible                           |
| Module     | Built-in functionality, e.g. `apt`, `service`, `template`      |
| Variable   | Dynamic value stored in YAML and used elsewhere                |
| Template   | Jinja2 file rendered with variable substitution                |
| Become     | Privilege escalation (sudo/root) for running tasks              |

---

## What We Learned

- Creating a role with `ansible-galaxy init`
- The purpose of each folder in the Galaxy role structure
- Writing a playbook that calls a role
- Installing packages with the `apt` module
- Managing services with the `service` module
- Storing reusable variables in `defaults/main.yml`
- Rendering Jinja2 templates with the `template` module
- Using `become: yes` and `-K` for sudo authentication
- Validating playbooks with `--syntax-check`

---

## Practice Exercises

**Practice 1 — Change the Variable**

```yaml
user_name: "Rahim"
```

Re-run the playbook and confirm the webpage updates accordingly.

**Practice 2 — Add Another Variable**

```yaml
user_name: "Naim"
course: "DevOps"
```

Update the template to use it:

```html
<h1>Hi {{ user_name }}</h1>
<p>Welcome to {{ course }}.</p>
```

**Practice 3 — Add a Handler**

Create `handlers/main.yml`:

```yaml
---
- name: Restart Nginx
  service:
    name: nginx
    state: restarted
```

Trigger it from the template task:

```yaml
notify: Restart Nginx
```

Handlers only run once, at the end of the play, and only if notified — useful for restarting a service after a config change.

**Practice 4 — Use the `copy` Module**

Place a static file inside `roles/nginx/files/` and copy it to the worker using the `copy` module (as opposed to `template`, which is for files needing variable substitution).

**Practice 5 — Create Another Role**

```bash
ansible-galaxy init roles/apache
```

Create a second role and call both roles from the same playbook to practice multi-role playbooks.

---

## Command Reference

```bash
ansible-galaxy init roles/nginx
ansible workers -m ping
ansible-playbook install-nginx.yml --syntax-check
ansible-playbook install-nginx.yml -K
systemctl status nginx
curl http://localhost
curl http://worker1
tree ~/ansible
```

---

## Final Result

After a successful run:

```text
PLAY RECAP

worker1 : ok=5 changed=1 failed=0
```

The worker automatically installs Nginx, starts the service, and serves a webpage displaying:

```html
Hi Naim
```

This is the foundation for building reusable Ansible Galaxy roles for DevOps automation.
