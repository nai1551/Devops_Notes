# Ansible Master–Worker Lab Guide

A beginner-friendly guide covering what we learned today:
installation, Master/Worker setup, networking, SSH, inventory, commands, modules, playbooks, and troubleshooting.

---

## 1. What is Ansible?

Ansible is an automation and configuration-management tool.

It allows one machine to control and configure other machines over SSH.

### Basic architecture

```text
             ANSIBLE CONTROL NODE
                    MASTER
              192.168.56.103
                     |
                     | SSH
                     v
              MANAGED NODE
                   WORKER
              192.168.56.102
```

### Important terms

| Term | Meaning |
|---|---|
| Control Node | Machine where Ansible is installed and commands are executed |
| Managed Node | Machine controlled by Ansible |
| Inventory | File containing managed hosts |
| Module | Small unit of work performed by Ansible |
| Playbook | YAML file containing automation tasks |
| SSH | Main connection method for Linux managed nodes |

**Important:** Ansible normally needs to be installed only on the Control Node. A Linux Worker generally needs SSH access and Python.

---

## 2. Our Lab Network

We use two network interfaces on each VM.

| Machine | Host-Only IP | NAT IP | Purpose |
|---|---:|---:|---|
| Master | `192.168.56.103` | `10.0.2.6` | Control Node |
| Worker | `192.168.56.102` | `10.0.2.5` | Managed Node |

### Why two networks?

- `192.168.56.x` = Host-Only network, useful for stable VM-to-VM communication.
- `10.0.2.x` = NAT network, useful for Internet/outbound access.

For Ansible communication, use the stable Host-Only IPs:

```text
Master  -> 192.168.56.103
Worker  -> 192.168.56.102
```

---

## 3. Check the Linux Network

Run:

```bash
hostname -I
```

Show interfaces:

```bash
ip addr
```

Show routing table:

```bash
ip route
```

Test the Worker from Master:

```bash
ping -c 4 192.168.56.102
```

Test Internet:

```bash
ping -c 4 8.8.8.8
```

Test DNS:

```bash
ping -c 4 google.com
```

---

## 4. Netplan Static Configuration

Ubuntu uses Netplan to configure networking.

Example Master configuration:

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    enp0s3:
      dhcp4: no
      addresses:
        - 192.168.56.103/24

    enp0s8:
      dhcp4: no
      addresses:
        - 10.0.2.6/24
      routes:
        - to: default
          via: 10.0.2.2
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

Worker uses:

```yaml
enp0s3:
  addresses:
    - 192.168.56.102/24

enp0s8:
  addresses:
    - 10.0.2.5/24
```

Apply:

```bash
sudo netplan generate
sudo netplan apply
```

Check:

```bash
ip addr
ip route
hostname -I
```

### Netplan permission warning

If you see:

```text
Permissions for /etc/netplan/01-static.yaml are too open.
```

Fix it:

```bash
sudo chmod 600 /etc/netplan/01-static.yaml
```

Verify:

```bash
ls -l /etc/netplan/01-static.yaml
```

Expected permission:

```text
-rw------- 1 root root ...
```

---

## 5. Troubleshoot (Cloud-Init and Duplicate IP Addresses)

If both a static Netplan file and `50-cloud-init.yaml` configure the same interface, you may get multiple IP addresses and multiple default routes.

For example:

```text
192.168.56.102 192.168.56.101
10.0.2.5 10.0.2.4
```

This usually means the old DHCP configuration is still active.

Check:

```bash
sudo cat /etc/netplan/50-cloud-init.yaml
```

Disable cloud-init network configuration:

```bash
sudo nano /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
```

Add:

```yaml
network:
  config: disabled
```

Backup the old Netplan file:

```bash
sudo mv /etc/netplan/50-cloud-init.yaml \
/etc/netplan/50-cloud-init.yaml.bak
```

Then:

```bash
sudo netplan generate
sudo netplan apply
```

Verify:

```bash
hostname -I
ip route
```

---

## 6. Install Ansible on the Master

Update packages:

```bash
sudo apt update
```

Upgrade packages:

```bash
sudo apt upgrade -y
```

Install Ansible:

```bash
sudo apt install ansible -y
```

Check:

```bash
ansible --version
```

Example:

```text
ansible [core ...]
python version = ...
```

Check Python:

```bash
python3 --version
```

---

## 7. Worker Requirements

Ansible does not normally need to be installed on the Worker.

The Worker should have:

- SSH server
- Python 3
- A user that Ansible can use

Check Python:

```bash
python3 --version
```

Install Python if necessary:

```bash
sudo apt update
sudo apt install python3 -y
```

Check SSH server:

```bash
sudo systemctl status ssh
```

If SSH is not installed:

```bash
sudo apt install openssh-server -y
```

Start and enable SSH:

```bash
sudo systemctl enable --now ssh
```

---

## 8. Test SSH Manually First

Before troubleshooting Ansible, always test normal SSH.

From Master:

```bash
ssh worker@192.168.56.102
```

If successful:

```bash
whoami
```

Expected:

```text
worker
```

Check hostname:

```bash
hostname
```

Exit:

```bash
exit
```

### Important troubleshooting rule

If normal SSH does not work, Ansible will not work either.

Fix SSH first.

---

## 9. SSH Key Authentication

On Master:

```bash
ssh-keygen
```

Press Enter to accept the default location.

Copy the public key:

```bash
ssh-copy-id worker@192.168.56.102
```

Test:

```bash
ssh worker@192.168.56.102
```

You should be able to connect without entering the Worker password.

Exit:

```bash
exit
```

---

## 10. Create an Ansible Project

On Master:

```bash
mkdir -p ~/ansible
cd ~/ansible
```

Check:

```bash
pwd
```

Recommended structure:

```text
ansible/
├── ansible.cfg
├── inventory
└── playbook.yml
```

---

## 11. Create the Inventory

Create:

```bash
nano inventory
```

Put:

```ini
[workers]
worker1 ansible_host=192.168.56.102 ansible_user=worker
```

### Meaning

```text
[workers]
```

Group name.

```text
worker1
```

Ansible's name for the machine.

```text
ansible_host=192.168.56.102
```

Actual IP address.

```text
ansible_user=worker
```

SSH username.

### Scaling to Multiple Groups (Why Ansible Is Scalable)

The example above uses one group with one worker. In a real environment, you may have many servers of different types (web servers, database servers, etc.).

Instead of running the same command on every server one by one, Ansible lets you group servers in the inventory and target them all with a single command.

Example inventory with multiple groups:

```ini
[webservers]
web1 ansible_host=192.168.56.111 ansible_user=worker
web2 ansible_host=192.168.56.112 ansible_user=worker

[dbservers]
db1 ansible_host=192.168.56.121 ansible_user=worker
db2 ansible_host=192.168.56.122 ansible_user=worker

[all_workers:children]
webservers
dbservers
```

`all_workers:children` creates a "group of groups" that contains both `webservers` and `dbservers`.

Now a single command can act on many servers at once:

Check hostname on all servers:

```bash
ansible all_workers -a "hostname"
```

Install nginx only on web servers:

```bash
ansible webservers -b -m apt -a "name=nginx state=present"
```

Check disk space only on database servers:

```bash
ansible dbservers -a "df -h"
```

Ping every server in every group:

```bash
ansible all_workers -m ping
```

If more servers are added later, you only need to add lines to the inventory file — the commands and playbooks stay exactly the same. This is why Ansible is considered scalable: the same automation that works on one server works on thousands, without changing the commands.

---

## 12. Check the Inventory

Show the inventory graph:

```bash
ansible-inventory -i inventory --graph
```

Expected:

```text
@all:
  |--@ungrouped:
  |--@workers:
  |  |--worker1
```

Show inventory data:

```bash
ansible-inventory -i inventory --list
```

---

## 13. Test Ansible Connection

Run:

```bash
ansible -i inventory workers -m ping
```

Expected:

```text
worker1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

### What does `ping` mean here?

Ansible's `ping` module does NOT send an ICMP ping.

It checks whether Ansible can:

1. Connect to the Worker.
2. Run the required Python code.
3. Receive a valid response.

---

## 14. Create ansible.cfg
In Ansible, a .cfg file is a configuration file. It tells Ansible how it should behave when you run commands or playbooks.

Create:

```bash
nano ansible.cfg
```

Put:

```ini
[defaults]
inventory = ./inventory
host_key_checking = False
```

Now you can run:

```bash
ansible workers -m ping
```

instead of:

```bash
ansible -i inventory workers -m ping
```

---

## 15. Basic Ansible Command Structure

General format:

```bash
ansible <host-pattern> -m <module> -a "<arguments>"
```

Example:

```bash
ansible workers -m ping
```

Example:

```bash
ansible workers -m command -a "hostname"
```

Example:

```bash
ansible workers -m shell -a "df -h"
```

---

## 16. Useful Ansible Commands

### Ping Worker

```bash
ansible workers -m ping
```

### Check hostname

```bash
ansible workers -a "hostname"
```

### Check uptime

```bash
ansible workers -a "uptime"
```

### Check IP address

```bash
ansible workers -a "hostname -I"
```

### Check disk usage

```bash
ansible workers -a "df -h"
```

### Check memory

```bash
ansible workers -a "free -h"
```

### Check running processes

```bash
ansible workers -a "ps aux"
```

### Check kernel/system information

```bash
ansible workers -a "uname -a"
```

### Check current user

```bash
ansible workers -a "whoami"
```

### Check date

```bash
ansible workers -a "date"
```

---

## 17. Important Ansible Modules

### ping

```bash
ansible workers -m ping
```

Tests Ansible connectivity.

### command

```bash
ansible workers -m command -a "hostname"
```

Runs a command remotely.

### shell

```bash
ansible workers -m shell -a "df -h | grep /"
```

Use `shell` when shell features such as pipes are needed.

### setup

```bash
ansible workers -m setup
```

Collects system facts.

### file

Create a directory:

```bash
ansible workers -m file \
  -a "path=/home/worker/testdir state=directory"
```

Create a file:

```bash
ansible workers -m file \
  -a "path=/home/worker/test.txt state=touch"
```

### copy

Create/copy a file:

```bash
ansible workers -m copy \
  -a "content='Hello Ansible' dest=/home/worker/hello.txt"
```

### service

Check a service:

```bash
ansible workers -m service \
  -a "name=ssh state=started"
```

### apt

Install a package:

```bash
ansible workers -b -m apt \
  -a "name=nginx state=present update_cache=yes"
```

`-b` means become/root privilege.

---

## 18. Become / sudo

Some operations require root privileges.

Example:

```bash
ansible workers -b -m apt -a "name=nginx state=present"
```
or 
```bash
  ansible workers -b -K -a "whoami"
  -K means:

--ask-become-pass
```
Check whether sudo works:

```bash
ansible workers -b -a "whoami"
```

Expected:

```text
root
```

Without `-b`:

```bash
ansible workers -a "whoami"
```

Expected:

```text
worker
```

---

## 19. Ad-Hoc Commands

An ad-hoc command is a quick one-time Ansible operation.

Examples:

```bash
ansible workers -m ping
```

```bash
ansible workers -a "uptime"
```

```bash
ansible workers -a "df -h"
```

```bash
ansible workers -a "free -h"
```

Ad-hoc commands are useful for:

- Testing
- Checking systems
- Quick changes
- Troubleshooting

For larger automation tasks, use a **Playbook**.

---

## 20. Your First Playbook

### Theory

A playbook is a YAML file that describes a set of automation tasks to run on one or more managed nodes. While an ad-hoc command runs a single one-time action, a playbook can group many tasks together, run them in a specific order, and repeat them reliably every time.

Why playbooks matter:

- Ad-hoc commands (`ansible workers -m ...`) are good for quick checks, but they aren't saved or reusable. A playbook is a file you can save, version-control (e.g., in Git), and run again anytime.
- A playbook can perform multiple related steps in one run — for example, installing a package and then starting its service — instead of running separate commands one by one.
- Playbooks are idempotent: running the same playbook multiple times won't cause harm. If nginx is already installed and running, Ansible simply reports "no change" instead of reinstalling it.
- This is the standard way real-world Ansible automation is written — ad-hoc commands are mainly for testing and troubleshooting, while playbooks are for actual deployment and configuration.

### Examples

Create:

```bash
nano playbook.yml
```

Put:

```yaml
---
- name: Basic Worker Configuration
  hosts: workers
  become: true

  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: true

    - name: Start nginx
      service:
        name: nginx
        state: started
        enabled: true
```

Check syntax:

```bash
ansible-playbook --syntax-check playbook.yml
```

Run:

```bash
ansible-playbook playbook.yml
```

---

## 21. Playbook Structure

### Theory

Every Ansible playbook follows a predictable structure so that Ansible knows what to run, where to run it, and how. Understanding this structure is what allows you to read or write any playbook, no matter how simple or complex.

Why understanding the structure matters:

- `hosts` tells Ansible which group (from the inventory) the play applies to — this connects a playbook back to the inventory system.
- `tasks` is an ordered list, and Ansible runs them top to bottom — order matters, since later tasks may depend on earlier ones succeeding.
- Each task calls exactly one module (like `apt`, `service`, `copy`) with specific options — the module is what actually does the work, the task just tells it what values to use.
- `become` controls whether the task needs root/admin privileges — without it, tasks requiring elevated access will fail.
- Knowing this structure means you can look at any playbook (even one written by someone else) and immediately understand what it targets and what it will do, before running it.

### Examples

```yaml
---
- name: Play name
  hosts: workers
  become: true

  tasks:
    - name: Task 1
      module_name:
        option: value
```

### Main concepts

| Keyword | Purpose |
|---|---|
| `name` | Human-readable name |
| `hosts` | Target machines |
| `become` | Use elevated/root privileges |
| `tasks` | List of actions |
| Module | Performs the actual operation |

---

## 22. Troubleshooting Guide

### Problem 1: `UNREACHABLE`

Example:

```text
worker1 | UNREACHABLE!
```

Check the Worker IP:

```bash
ping -c 4 192.168.56.102
```

Check SSH:

```bash
ssh worker@192.168.56.102
```

Check inventory:

```bash
cat inventory
```

Expected:

```ini
[workers]
worker1 ansible_host=192.168.56.102 ansible_user=worker
```

---

### Problem 2: `Permission denied (publickey,password)`

Test SSH:

```bash
ssh worker@192.168.56.102
```

Check key:

```bash
ls -la ~/.ssh
```

Copy key again:

```bash
ssh-copy-id worker@192.168.56.102
```

Then test:

```bash
ssh worker@192.168.56.102
```

---

### Problem 3: `Connection refused`

On Worker:

```bash
sudo systemctl status ssh
```

Start SSH:

```bash
sudo systemctl start ssh
```

Enable it permanently:

```bash
sudo systemctl enable ssh
```

---

### Problem 4: `ping: Destination Host Unreachable`

Check:

```bash
ip addr
```

Check route:

```bash
ip route
```

Test:

```bash
ping -c 4 192.168.56.102
```

Make sure both VMs use the same VirtualBox Host-Only network.

---

### Problem 5: Wrong IP / Multiple IPs

Check:

```bash
hostname -I
ip addr
```

If you see old DHCP addresses such as:

```text
192.168.56.101
10.0.2.4
```

check:

```bash
sudo cat /etc/netplan/50-cloud-init.yaml
```

Make sure old DHCP configuration is not overriding your static configuration.

---

### Problem 6: `No module named ...` / Python problem

On Worker:

```bash
python3 --version
```

Install Python:

```bash
sudo apt update
sudo apt install python3 -y
```

Then test:

```bash
ansible workers -m ping
```

---

### Problem 7: `sudo` / privilege problem

Try:

```bash
ansible workers -b -a "whoami"
```

Expected:

```text
root
```

If the Worker user cannot use sudo, check on Worker:

```bash
sudo -l
```

---

### Problem 8: Inventory not found

Check:

```bash
pwd
ls
```

You should be inside:

```text
~/ansible
```

and see:

```text
ansible.cfg
inventory
```

Test:

```bash
ansible-inventory --graph
```

---

## 23. A Simple Troubleshooting Order

When Ansible does not work, **do not immediately blame Ansible**.

Use this order:

```text
1. Check IP
      ↓
2. Ping Worker
      ↓
3. Test SSH manually
      ↓
4. Check Python on Worker
      ↓
5. Check inventory
      ↓
6. Run Ansible ping
      ↓
7. Check sudo/become
      ↓
8. Run the required module
```

### Commands

```bash
hostname -I
```

```bash
ping -c 4 192.168.56.102
```

```bash
ssh worker@192.168.56.102
```

```bash
python3 --version
```

```bash
cat inventory
```

```bash
ansible workers -m ping
```

```bash
ansible workers -b -a "whoami"
```

---

## 24. Useful System Commands for Ansible Troubleshooting

### Network

```bash
ip addr
ip route
hostname -I
ping -c 4 <IP>
```

### SSH

```bash
ssh worker@192.168.56.102
sudo systemctl status ssh
sudo systemctl restart ssh
```

### Processes

```bash
ps aux
ps -u worker -f
pgrep -a -u worker
```

### Services

```bash
systemctl status ssh
systemctl list-units --type=service
```

### Disk

```bash
df -h
lsblk
```

### Memory

```bash
free -h
```

### System load/processes

```bash
top
uptime
```

---

## 25. Useful Ansible Reference Commands

Check version:

```bash
ansible --version
```

Show help:

```bash
ansible --help
```

Show module documentation:

```bash
ansible-doc ping
```

Show file module documentation:

```bash
ansible-doc file
```

Show apt module documentation:

```bash
ansible-doc apt
```

List inventory:

```bash
ansible-inventory --graph
```

List inventory in JSON-like format:

```bash
ansible-inventory --list
```

Test connectivity:

```bash
ansible workers -m ping
```

Run a playbook:

```bash
ansible-playbook playbook.yml
```

Check playbook syntax:

```bash
ansible-playbook --syntax-check playbook.yml
```

Dry-run/check mode:

```bash
ansible-playbook --check playbook.yml
```

---

## 26. Important Ansible Options

| Option | Meaning |
|---|---|
| `-i` | Specify inventory |
| `-m` | Specify module |
| `-a` | Module arguments |
| `-b` | Become/root privilege |
| `-u` | SSH user |
| `-v` | Verbose output |
| `-vv` | More verbose |
| `-vvv` | Very detailed troubleshooting |
| `--check` | Check/dry-run mode |
| `--syntax-check` | Check playbook syntax |

Examples:

```bash
ansible -i inventory workers -m ping
```

```bash
ansible workers -m ping -vvv
```

```bash
ansible workers -b -a "systemctl status ssh"
```

---

## 27. Master and Worker Final Configuration

### Master

```text
Hostname: Master
Role: Ansible Control Node
Host-Only IP: 192.168.56.103
NAT IP: 10.0.2.6
Ansible: Installed
SSH Client: Required
```

### Worker

```text
Hostname: Worker
Role: Ansible Managed Node
Host-Only IP: 192.168.56.102
NAT IP: 10.0.2.5
Ansible: Not required
Python 3: Required
SSH Server: Required
```

### Inventory

```ini
[workers]
worker1 ansible_host=192.168.56.102 ansible_user=worker
```

---

## 28. Complete Test Checklist

Run these from Master:

```bash
# 1. Check Ansible
ansible --version

# 2. Check network
ping -c 4 192.168.56.102

# 3. Check SSH
ssh worker@192.168.56.102

# 4. Exit Worker
exit

# 5. Check inventory
ansible-inventory --graph

# 6. Test Ansible
ansible workers -m ping

# 7. Check hostname
ansible workers -a "hostname"

# 8. Check uptime
ansible workers -a "uptime"

# 9. Check disk
ansible workers -a "df -h"

# 10. Check memory
ansible workers -a "free -h"

# 11. Test root privilege
ansible workers -b -a "whoami"
```

If all of these work, your basic **Ansible Master–Worker lab is ready**.

---

## 29. Recommended Learning Path

After completing this setup, learn Ansible in this order:

```text
1. Ansible architecture
        ↓
2. Inventory
        ↓
3. Ad-hoc commands
        ↓
4. Modules
        ↓
5. Variables
        ↓
6. Facts
        ↓
7. YAML
        ↓
8. Playbooks
        ↓
9. Handlers
        ↓
10. Conditionals
        ↓
11. Loops
        ↓
12. Templates (Jinja2)
        ↓
13. Roles
        ↓
14. Ansible Vault
        ↓
15. Real DevOps automation
```

---

## 30. Quick Cheat Sheet

```bash
# Installation
sudo apt update
sudo apt install ansible -y
ansible --version

# SSH
ssh worker@192.168.56.102
ssh-keygen
ssh-copy-id worker@192.168.56.102

# Project
mkdir -p ~/ansible
cd ~/ansible

# Inventory
nano inventory

# Inventory test
ansible-inventory --graph

# Connectivity
ansible workers -m ping

# Commands
ansible workers -a "hostname"
ansible workers -a "uptime"
ansible workers -a "df -h"
ansible workers -a "free -h"
ansible workers -a "hostname -I"

# Modules
ansible workers -m setup
ansible workers -m file -a "path=/home/worker/testdir state=directory"

# Root
ansible workers -b -a "whoami"

# Documentation
ansible-doc ping
ansible-doc file
ansible-doc apt

# Playbook
ansible-playbook --syntax-check playbook.yml
ansible-playbook --check playbook.yml
ansible-playbook playbook.yml

# Troubleshooting
ansible workers -m ping -vvv
```

---

## 31. Variables

### Theory

A variable in Ansible is a named value that can be reused throughout a playbook, instead of typing the same value (like a package name, port number, file path, or username) over and over.

Why variables matter:

- They avoid hardcoding — if a value changes, you update it in one place instead of many.
- The same playbook can be reused for different servers, environments (dev/staging/production), or values just by changing the variable.
- Variables can come from several places: directly inside a playbook (`vars`), from the inventory file, from separate variable files, or passed in on the command line — Ansible merges them together, with more specific sources overriding more general ones.
- Inside tasks, a variable is referenced using double curly braces: `{{ variable_name }}`.

### Examples

### Defining variables in a playbook

```yaml
---
- name: Install a package using a variable
  hosts: workers
  become: true

  vars:
    package_name: nginx

  tasks:
    - name: Install the package
      apt:
        name: "{{ package_name }}"
        state: present
```

### Defining variables in the inventory

```ini
[webservers]
web1 ansible_host=192.168.56.111 ansible_user=worker package_name=nginx
```

### Passing variables on the command line

```bash
ansible-playbook playbook.yml --extra-vars "package_name=nginx"
```

Variables make the same playbook reusable for different packages, ports, or environments without editing the file itself.

---

## 32. Facts

### Theory

Facts are pieces of system information that Ansible automatically discovers about each managed node (worker) before running tasks — things like the operating system, IP addresses, hostname, total memory, CPU count, and disk layout.

Why facts matter:

- You don't have to manually check or hardcode a server's OS, IP, or hostname — Ansible already knows it.
- Facts can be used inside playbooks to make decisions, for example installing a package only on a certain OS, or displaying server-specific information.
- By default, Ansible gathers facts automatically at the start of every play (this can be turned off with `gather_facts: false` if not needed, to save time).
- Facts are just variables — they are also referenced with `{{ }}`, for example `{{ ansible_hostname }}` or `{{ ansible_distribution }}`.

### Examples

Collect facts manually:

```bash
ansible workers -m setup
```

Example: filter facts for just the OS:

```bash
ansible workers -m setup -a "filter=ansible_distribution*"
```

### Using facts inside a playbook

```yaml
---
- name: Show system facts
  hosts: workers

  tasks:
    - name: Print OS and memory
      debug:
        msg: "OS is {{ ansible_distribution }}, memory is {{ ansible_memtotal_mb }} MB"
```

Facts are automatically gathered before tasks run (unless disabled with `gather_facts: false`), so `{{ ansible_distribution }}`, `{{ ansible_hostname }}`, etc. are available right away.

---

## 33. Handlers

### Theory

A handler is a special kind of task that only runs when it is "notified" by another task — it does not run on every playbook execution, only when something actually changed.

Why handlers matter:

- The most common use case: restarting or reloading a service only when its configuration file was actually changed, instead of restarting it every single run (which would cause unnecessary downtime).
- A task triggers a handler using the `notify` keyword, referencing the handler by its `name`.
- Handlers are defined in a separate `handlers` section of the playbook (or role), not inside `tasks`.
- Handlers run at the end of the play, after all tasks complete — and only once, even if multiple tasks notify the same handler multiple times.

### Examples

```yaml
---
- name: Configure nginx and restart only if config changes
  hosts: workers
  become: true

  tasks:
    - name: Copy nginx config file
      copy:
        src: files/nginx.conf
        dest: /etc/nginx/nginx.conf
      notify: Restart nginx

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted
```

### How it works

```text
Task runs
    |
    v
Did the task change anything?
    |
   Yes -> notify handler -> handler runs at end of play
    |
   No  -> handler is skipped
```

The handler only runs once, even if multiple tasks notify it, and only if a change actually happened — this avoids unnecessary service restarts.

---

## 34. Conditionals

### Theory

A conditional lets a task run only if a specific condition is true, using the `when` keyword. If the condition is false, Ansible simply skips that task for that host and moves on.

Why conditionals matter:

- Different servers often need different treatment — for example, a Debian-based server uses `apt` while a RedHat-based server uses `yum`. Conditionals let one playbook handle both correctly.
- Conditions can check facts (like `ansible_os_family`), variables (like an `environment` variable), or the result of a previous task.
- `when` is written without `{{ }}` around the condition itself, since it's already treated as an expression.
- Conditionals make playbooks smarter and safer — they prevent tasks from running in situations where they shouldn't.

### Examples

```yaml
---
- name: Install package based on OS
  hosts: workers
  become: true

  tasks:
    - name: Install nginx on Debian/Ubuntu
      apt:
        name: nginx
        state: present
      when: ansible_os_family == "Debian"

    - name: Install nginx on RedHat/CentOS
      yum:
        name: nginx
        state: present
      when: ansible_os_family == "RedHat"
```

### Conditional based on a variable

```yaml
    - name: Only run in production
      debug:
        msg: "Running production setup"
      when: environment == "production"
```

Run it with:

```bash
ansible-playbook playbook.yml --extra-vars "environment=production"
```

---

## 35. Loops

### Theory

A loop lets a single task run multiple times, once for each item in a list, instead of writing a separate task for every item.

Why loops matter:

- Without a loop, installing 5 packages would need 5 separate tasks. With a loop, it's one task with a list.
- Inside a loop, the current item is accessed using the special variable `{{ item }}`.
- Loops work with any module — packages, files, directories, users, and more.
- This keeps playbooks shorter, easier to read, and easier to update (adding a new item just means adding a new line to the list, not a new task).

### Examples

```yaml
---
- name: Install multiple packages
  hosts: workers
  become: true

  tasks:
    - name: Install a list of packages
      apt:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - git
        - curl
```

### Looping to create multiple files

```yaml
    - name: Create multiple directories
      file:
        path: "/home/worker/{{ item }}"
        state: directory
      loop:
        - dir1
        - dir2
        - dir3
```

Without a loop, this would need one task per package or directory — the loop keeps the playbook short and easy to update.

---

## 36. Templates (Jinja2)

### Theory

A template is a configuration file that contains placeholders (written in Jinja2 syntax, using `{{ }}`) which Ansible fills in with real values — variables or facts — when the file is copied to a managed node.

Why templates matter:

- Instead of copying one identical static file to every server, a template lets each server get a config file customized with its own hostname, IP, variables, or facts.
- Template files use the `.j2` extension by convention and are usually placed in a `templates/` folder.
- The `template` module is used instead of `copy` whenever a file needs values filled in dynamically.
- Templates support more than just variables — they also support conditionals (`{% if %}`) and loops (`{% for %}`) inside the file itself for advanced cases.

### Examples

Template file (`templates/nginx.conf.j2`):

```text
server {
    listen 80;
    server_name {{ ansible_hostname }};
    root /var/www/{{ site_name }};
}
```

Playbook using the template:

```yaml
---
- name: Deploy nginx config from template
  hosts: webservers
  become: true

  vars:
    site_name: mysite

  tasks:
    - name: Generate nginx config
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/sites-available/mysite.conf
      notify: Restart nginx

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted
```

Every server gets its own generated config file, filled in with its own hostname and variables — instead of copying one static file to every server.

---

## 37. Roles

### Theory

A role is a standardized way of organizing tasks, handlers, variables, templates, and files into a predictable folder structure, so Ansible automatically knows where to look for each piece — instead of putting everything into one large playbook file.

Why roles matter:

- As automation projects grow (many servers, many services, many tasks), a single playbook file becomes hard to read and maintain. Roles break the project into reusable, self-contained units (e.g., a "nginx" role, a "mysql" role).
- Roles can be reused across multiple playbooks and even shared between projects or downloaded from Ansible Galaxy (a public library of community roles).
- Each folder inside a role has a specific purpose (`tasks/` for the actual steps, `handlers/` for handlers, `templates/` for Jinja2 files, `vars/` and `defaults/` for variables) — Ansible loads them automatically by convention.
- A playbook simply references a role by name in its `roles:` section, and Ansible pulls in everything from that role's folder.

### Examples

### Standard role folder structure

```text
roles/
└── nginx/
    ├── tasks/
    │   └── main.yml
    ├── handlers/
    │   └── main.yml
    ├── templates/
    │   └── nginx.conf.j2
    ├── vars/
    │   └── main.yml
    └── defaults/
        └── main.yml
```

Create a role skeleton:

```bash
ansible-galaxy init roles/nginx
```

### Using a role in a playbook

```yaml
---
- name: Set up web servers
  hosts: webservers
  become: true

  roles:
    - nginx
```

Ansible automatically looks inside `roles/nginx/tasks/main.yml` for the tasks, `roles/nginx/handlers/main.yml` for handlers, and so on — keeping large projects organized instead of one huge playbook file.

---

## 38. Ansible Vault

### Theory

Ansible Vault is a built-in feature that encrypts sensitive data — such as passwords, API keys, and secrets — so they are never stored as plain, readable text inside playbooks or variable files.

Why Vault matters:

- Playbooks and variable files are often stored in version control (like Git), where plain-text passwords would be a serious security risk. Vault encrypts the file content so it's unreadable without the vault password.
- Encrypted files can still be used normally inside playbooks — Ansible decrypts them in memory at runtime using `{{ variable_name }}`, exactly like any other variable.
- A vault password is required to create, edit, view, or run anything using an encrypted file. This password can be entered manually (`--ask-vault-pass`) or read from a password file (`--vault-password-file`).
- Vault can encrypt an entire file, or in newer Ansible versions, encrypt individual variables within an otherwise plain-text file.

### Examples

### Create an encrypted file

```bash
ansible-vault create secrets.yml
```

You will be prompted for a vault password, then can edit the file normally:

```yaml
db_password: SuperSecret123
```

### Edit an existing encrypted file

```bash
ansible-vault edit secrets.yml
```

### View an encrypted file

```bash
ansible-vault view secrets.yml
```

### Encrypt an existing plain-text file

```bash
ansible-vault encrypt vars.yml
```

### Run a playbook that uses vault-encrypted variables

```bash
ansible-playbook playbook.yml --ask-vault-pass
```

Or using a password file (avoids typing the password each run):

```bash
ansible-playbook playbook.yml --vault-password-file ~/.vault_pass.txt
```

This keeps secrets out of plain text and out of version control history, while still letting playbooks use them normally via `{{ db_password }}`.

---

## Final Concept

Remember this simple model:

```text
                ANSIBLE
                   |
            Control Node
                MASTER
          192.168.56.103
                   |
                  SSH
                   |
                   v
            Managed Node
                WORKER
          192.168.56.102
                   |
             Python + SSH
```

**Master controls. Worker executes. Inventory tells Ansible where the Worker is. Modules perform individual tasks. Playbooks combine tasks into reusable automation.**
