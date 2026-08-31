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

## 5. Cloud-Init and Duplicate IP Addresses

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
