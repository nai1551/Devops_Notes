# Single-VM Kubernetes with kubeadm + Calico CNI + Calico eBPF kube-proxy Replacement

### 🌱 Beginner-Friendly Edition

> This is the same runbook as before, with **extra explanation added to every step**. Every step now tells you **what you are doing, why you are doing it, what a good result looks like, and what to do if it goes wrong**.
>
> If you have never touched Kubernetes before, read the next two sections ("How to use this guide" and "Glossary") first. They take about 10 minutes and will make everything else much easier.

---

## How to Use This Guide

### The golden rules

1. **Go in order.** Each step depends on the one before it. Skipping ahead is the number one cause of broken clusters.
2. **Do not move on until the "✅ What you should see" box matches your screen.** If it does not match, stop and use the "⚠️ If it doesn't" hint or the troubleshooting sections near the end.
3. **Read the command before you run it.** Every command is explained. Copy-pasting without understanding is how small typos become big problems.
4. **Take notes.** Write down your VM's IP address, hostname, and any join command that is printed. You will need them later.

### What the symbols mean

| Symbol | Meaning |
|---|---|
| 🧠 | **What this step does**: a plain-English explanation |
| 🎯 | **Why it matters**: the reason this step exists |
| 💡 | **Tip / analogy**: a way to remember the idea |
| ✅ | **What you should see**: how to know it worked |
| ⚠️ | **If it doesn't work**: common problems and fixes |
| 🛑 | **Stop and check**: do not continue until this is true |

### How to read the commands

- Lines in a gray box are commands you type into the **terminal** (the text window connected to your VM, usually through SSH).
- `sudo` means "run this as the administrator". You may be asked for your password.
- Anything in angle brackets like `<NODE_IP>` is a **placeholder**. Replace it, including the `<` and `>` characters, with your real value. For example, `<NODE_IP>` becomes `192.168.30.100`.
- A backslash `\` at the end of a line means "the command continues on the next line". You can paste a multi-line command as-is.
- A line starting with `#` inside a command block is a **comment**. It is a note for humans, and the computer ignores it.
- `|` (the "pipe") sends the output of one command into another. For example, `lsmod | grep overlay` means "list all loaded modules, then show me only the lines containing the word overlay".

### Assumptions

- You have a fresh **Ubuntu 22.04 (or newer)** virtual machine.
- You can log in with a normal user that has `sudo` rights. You do **not** need to be root.
- The VM has internet access.
- **This guide was tested end-to-end** on: Ubuntu 24.04 (kernel 6.8), VirtualBox, containerd 2.2.1, Kubernetes **v1.36.5**, Calico **v3.33.0** (Tigera Operator), eBPF dataplane, no kube-proxy. Kubernetes v1.37 was also released (Aug 26, 2026), but it was not tested here. Kubernetes and Calico release often, so **check the official links in Section 71** (especially Calico's Kubernetes requirements page) before choosing other versions.

---

## Glossary: Words You Will See Everywhere

| Term | Plain-English meaning |
|---|---|
| **Kubernetes (K8s)** | Software that runs and manages containers across one or more machines. Think of it as an "operating system for a cluster". |
| **Container** | A lightweight, packaged program that includes everything it needs to run (like a shipping container for software). |
| **Cluster** | A group of machines (here: just one VM) managed together by Kubernetes. |
| **Node** | One machine in the cluster. We only have one node. |
| **Control plane** | The "brain" of Kubernetes. It decides what runs where and keeps track of everything. |
| **Worker** | The part of a node that actually runs your applications. |
| **Pod** | The smallest unit Kubernetes runs. It wraps one or more containers. Every Pod gets its own IP address. |
| **Service** | A stable address (and name) that sits in front of one or more Pods. Pods come and go, but the Service address stays the same. |
| **ClusterIP** | The default Service type: an address that only works *inside* the cluster. |
| **NodePort** | A Service type that also opens a port on the node itself, so you can reach the app from outside the cluster. |
| **kubeadm** | The official tool that sets up (bootstraps) a Kubernetes cluster for you. |
| **kubelet** | A small agent that runs on every node. It takes orders from the control plane and starts/stops containers. |
| **kubectl** | The command-line "remote control" you use to talk to Kubernetes. |
| **containerd** | The container runtime. It is the program that actually pulls images and runs containers. |
| **CRI** | Container Runtime Interface: the "plug" that lets kubelet talk to containerd. |
| **etcd** | Kubernetes' database. It stores all cluster information. |
| **API server** | The front door of Kubernetes. Every command and every component talks to it (port 6443). |
| **CNI** | Container Network Interface. A plugin that gives Pods IP addresses and lets them talk to each other. |
| **Calico** | The CNI we are installing. It also enforces network security rules (NetworkPolicy). |
| **Tigera Operator** | A helper program that installs and manages Calico for you based on a simple YAML file. |
| **kube-proxy** | The standard Kubernetes component that makes Services work (using iptables rules). We are **replacing** it. |
| **eBPF** | A Linux kernel feature that lets small, safe programs run inside the kernel. Calico uses it to route traffic faster and more efficiently than iptables. |
| **iptables** | The traditional Linux firewall/packet-rules system. |
| **CIDR** | A way to write a range of IP addresses, such as `10.96.0.0/12`. |
| **Pod CIDR** | The range of IP addresses handed out to Pods. |
| **Service CIDR** | The range of IP addresses handed out to Services. |
| **VXLAN** | A technique that wraps network traffic in another packet so it can cross networks. Used between nodes. |
| **Taint** | A "keep out" sign on a node. Normal workloads will not run on a tainted node. |
| **YAML** | A text format used to describe Kubernetes resources. Indentation (spaces) matters. Never use tabs. |
| **CRD** | Custom Resource Definition: teaches Kubernetes about a new type of object (for example, Calico's `Installation`). |
| **DaemonSet** | A Kubernetes object that runs one copy of a Pod on every node. |

---

# 0. Target Architecture

## 🧠 What this section describes

Before building anything, it helps to see the **finished picture**. This guide builds a complete Kubernetes cluster **on a single virtual machine**. That one VM plays every role: it is the "brain" (control plane) *and* the place where applications run (worker).

```text
                         Single VM
                +-------------------------+
                | Ubuntu 22.04+           |
                |                         |
                | containerd              |
                | kubelet                 |
                | kubeadm                  |
                | kubectl                 |
                |                         |
                | Kubernetes              |
                |  Control Plane          |
                |  + Worker               |
                |                         |
                | Calico CNI               |
                | Calico eBPF dataplane    |
                | kube-proxy: DISABLED    |
                +-------------------------+
```

### How to read the diagram

| Box | What it is |
|---|---|
| **Ubuntu 22.04+** | The operating system everything sits on. |
| **containerd** | Runs the containers. |
| **kubelet** | The agent that tells containerd what to start. |
| **kubeadm / kubectl** | Tools: one sets the cluster up, the other lets you control it. |
| **Control Plane + Worker** | Both jobs happen on the same machine. |
| **Calico CNI** | Gives every Pod a network address and connects them. |
| **Calico eBPF dataplane** | The modern, fast way Calico moves network packets inside the Linux kernel. |
| **kube-proxy: DISABLED** | We deliberately do **not** run the normal Service-routing component, because Calico eBPF does that job instead. |

### Design decisions

| Component | Choice | What this means for you |
|---|---|---|
| Deployment | Self-hosted | You run everything yourself. No cloud-managed Kubernetes (EKS, GKE, AKS). |
| Infrastructure | One VM | Simple and cheap, but there is no backup machine. |
| Kubernetes bootstrap | kubeadm | The official, standard way to build a cluster by hand. |
| Container runtime | containerd | Lightweight and the Kubernetes default. |
| CNI | Calico | Handles Pod networking and security policy. |
| Service dataplane | Calico eBPF | Calico (not kube-proxy) makes Services work. |
| kube-proxy | Disabled | Calico replaces it. |
| Control plane | Same VM | The brain lives on the same machine as your apps. |
| Worker | Same VM | Your apps run on the same machine as the brain. |
| etcd | kubeadm stacked/local etcd | The cluster database runs on this same VM. |
| Calico datastore | Kubernetes API | Calico stores its settings inside Kubernetes itself. No extra database to manage. |
| Calico installation | Tigera Operator | An automatic installer/manager for Calico. |
| Calico overlay | VXLAN where applicable | The method used to carry Pod traffic between nodes (only matters once you add more nodes). |
| HA (high availability) | No | If the VM dies, everything stops. |
| Purpose | Lab / development / self-hosted practice | Great for learning, **not** for production. |

> **Important:** Calico eBPF replaces kube-proxy for Kubernetes Service networking. Do not install a second CNI such as Cilium, and do not leave kube-proxy actively managing Services.

## 🎯 Why this warning matters

💡 **Analogy:** Imagine two traffic controllers standing at the same intersection, each giving different hand signals. Cars (network packets) would get confused and crash. Kubernetes networking works the same way. If both kube-proxy **and** Calico eBPF try to handle Service traffic, or if two CNIs fight over Pod networking, you get random, confusing failures. **One CNI, and one Service-routing mechanism, only.**

---

# 1. Before Installing Anything

## 🧠 What this section does

You are **inspecting** your VM, not changing it yet. Think of it like checking that your car has fuel, tyres and a valid licence *before* a long trip. Every command here only **reads** information.

## 1.1 Confirm VM resources

### 🧠 What this step does

Kubernetes needs a certain amount of CPU, memory (RAM) and disk. Here we check that your VM has enough.

### 🎯 Why it matters

If the VM is too small, Kubernetes components will crash or become painfully slow. Problems like this are very confusing to debug later, so it is better to know now.

Minimum Kubernetes requirements should be treated as a starting point, not a recommended production sizing.

```bash
nproc
free -h
df -h
uname -a
```

### What each command does

| Command | What it tells you |
|---|---|
| `nproc` | The number of CPU cores (vCPUs) available. |
| `free -h` | How much RAM you have and how much is free. The `-h` means "human-readable" (shows GB/MB instead of raw bytes). |
| `df -h` | How much disk space is used and available on each disk/partition. |
| `uname -a` | Basic system info: kernel version, hostname, architecture. |

Recommended for this single-node lab:

```text
CPU:     4+ vCPU
RAM:     8+ GB
Disk:    40+ GB
```

Check:

```bash
nproc
free -h
lsblk
df -h /
```

| Command | What it tells you |
|---|---|
| `lsblk` | Lists your disks and partitions in a tree view. |
| `df -h /` | Free space on the main (root `/`) disk only. |

### ✅ What you should see

- `nproc` prints `4` or more.
- `free -h` shows a `Mem:` line with a total of about `8Gi` or more.
- `df -h /` shows at least `40G` total and plenty under `Avail`.

### ⚠️ If it doesn't match

A VM with 2 CPUs and 4 GB RAM *can* sometimes run a tiny cluster, but it will be slow and unreliable. If you can, increase the VM size in your hypervisor (VirtualBox, VMware, Proxmox, cloud console, etc.) and reboot.

## 1.2 Confirm operating system

### 🧠 What this step does

Shows which Linux distribution and which **kernel** (the core of the operating system) your VM runs.

### 🎯 Why it matters

eBPF is a **kernel** feature. If your kernel is too old, Calico's eBPF mode simply will not work. Checking now saves hours of confusion later.

```bash
cat /etc/os-release
uname -r
```

| Command | What it tells you |
|---|---|
| `cat /etc/os-release` | Prints the OS name and version (e.g., Ubuntu 22.04). |
| `uname -r` | Prints the **kernel version** (e.g., `5.15.0-91-generic`). |

Calico eBPF requires a supported Linux kernel. Current Calico documentation supports Ubuntu 22.04+ and other supported systems with sufficiently recent kernels.

Verify the actual kernel before continuing:

```bash
uname -r
```

### ✅ What you should see

`NAME="Ubuntu"` and `VERSION_ID="22.04"` (or newer), and a kernel version that is `5.x` or `6.x`.

### 🛑 Stop and check

Do not continue until the kernel/OS combination is confirmed compatible with the Calico version you intend to install. Open the Calico eBPF documentation (link in Section 71) and compare its stated kernel requirement with your `uname -r` output.

## 1.3 Confirm architecture

### 🧠 What this step does

Shows the type of CPU your VM uses.

### 🎯 Why it matters

Software is built for specific CPU families. The download links in this guide work for the two most common ones.

```bash
uname -m
```

Expected for a normal x86 VM:

```text
x86_64
```

Calico also supports arm64 (`aarch64`), which is what you would see on an ARM-based VM such as an Apple Silicon host or an AWS Graviton instance.

## 1.4 Confirm hostname

### 🧠 What this step does

Every machine has a **hostname**: its name on the network. Kubernetes uses the hostname as the **node name**. This step checks it and, if needed, gives the VM a clean, permanent name.

### 🎯 Why it matters

Kubernetes expects the node name to stay stable. If you change the hostname *after* creating the cluster, things break. Choose now, and choose once.

💡 **Tip:** Hostnames should be lowercase, with no spaces or underscores. Letters, numbers and hyphens are fine.

```bash
hostnamectl
hostname
```

| Command | What it does |
|---|---|
| `hostnamectl` | Shows detailed hostname and OS information. |
| `hostname` | Prints just the hostname. |

Set a stable hostname if required:

```bash
sudo hostnamectl set-hostname k8s-single
```

This command renames the VM to `k8s-single`. You may choose any valid name, but the rest of this guide uses `k8s-single` in examples.

Reconnect SSH if necessary. (Close your terminal window and log in again so your prompt shows the new name.)

Verify:

```bash
hostnamectl
hostname
```

### ✅ What you should see

`k8s-single` (or whatever name you chose) printed back.

## 1.5 Confirm the VM has a stable IP

### 🧠 What this step does

Finds your VM's **IP address**, which is its "house number" on the network.

### 🎯 Why it matters

Kubernetes bakes the node's IP address into certificates and configuration. If your VM's IP changes later (because your router hands out a new one), the cluster will break in confusing ways.

💡 **Tip:** A **static IP** is an address that never changes. If you are on a home or office network, either configure a static IP in the VM, or set a **DHCP reservation** for the VM's MAC address in your router.

```bash
ip -br addr
ip route
```

| Command | What it shows |
|---|---|
| `ip -br addr` | A short ("brief") list of network interfaces and their IP addresses. |
| `ip route` | The routing table: which network traffic goes out through which interface/gateway. |

Find the node's intended Kubernetes IP:

```bash
ip -4 addr
```

`-4` limits the output to IPv4 addresses (the familiar `192.168.x.x` style).

Example:

```text
192.168.30.100
```

Look for the address on your main network interface (often named `eth0`, `ens33`, `ens18`, or `enp0s3`). **Ignore** `127.0.0.1` (that is "localhost", meaning the machine itself).

For a single-node cluster, use a stable/static node IP whenever possible.

📝 **Write this IP down.** In this guide it appears as `<NODE_IP>`.

### 1.5b Real-world fix: disk shows only about half the size you gave the VM

Ubuntu's installer often creates the LVM volume at about half of the disk (for example, 24 GB on a 50 GB disk). Check:

```bash
lsblk
sudo vgs
df -h /
```

If `VFree` in `vgs` shows free space, extend the volume and its filesystem in one command:

```bash
sudo lvextend -r -l +100%FREE /dev/mapper/ubuntu--vg-ubuntu--lv
df -h /
```

`-r` also resizes the filesystem. `df -h /` should now show nearly the full disk size. If `VFree` is `0` but the disk is larger, grow the partition first: `sudo apt install -y cloud-guest-utils`, then `sudo growpart /dev/sda 3` and `sudo pvresize /dev/sda3` (check your partition number with `lsblk`), then run `lvextend` again.

### 1.5c Real-world fix: make the IP address permanent (static IP)

If `ip route` shows `proto dhcp`, the address comes from DHCP and could change. Kubernetes bakes the node IP into its certificates, so a changed IP breaks the cluster. Either reserve the IP in your router (DHCP reservation) or set a static IP in netplan inside the VM.

Use your own values from `ip -br addr`, `ip route` and `resolvectl status`. Example (replace the interface name, IP, gateway and DNS with yours):

```bash
echo 'network: {config: disabled}' | sudo tee /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
sudo cp /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml.bak
sudo nano /etc/netplan/50-cloud-init.yaml
```

```yaml
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: false
      addresses:
        - 10.11.204.124/22
      routes:
        - to: default
          via: 10.11.204.1
      nameservers:
        addresses:
          - 96.45.45.45
          - 96.45.46.46
```

Apply it safely:

```bash
sudo netplan try
```

`netplan try` rolls the change back automatically after 120 seconds unless you press Enter, which protects you from locking yourself out over SSH. Afterwards `ip route` should show `proto static`.

---

# 2. Verify Network Connectivity

## 🧠 What this section does

Kubernetes has to **download** a lot of software (container images, packages, manifests). This section confirms your VM can reach the internet and that DNS (name lookup) works.

## 🎯 Why it matters

A huge share of "Kubernetes won't start" problems are really "the VM can't reach the internet" problems. Checking now takes one minute.

## 2.1 Check default route

### 🧠 What this step does

The **default route** is the exit door from your VM to the rest of the world. Without it, the VM cannot reach the internet.

```bash
ip route
```

Expected to contain a default route:

```text
default via <gateway> dev <interface>
```

### ✅ What you should see

A line beginning with `default via`, for example `default via 192.168.30.1 dev ens33`. The `192.168.30.1` is your **gateway** (usually your router).

### ⚠️ If it doesn't

If there is no `default` line, the VM has no path to the internet. Check your VM's network adapter settings in your hypervisor (try "Bridged" or "NAT" mode).

## 2.2 Check DNS

### 🧠 What this step does

**DNS** converts names like `google.com` into IP addresses. This step checks that conversion works.

```bash
resolvectl status
getent hosts google.com
```

| Command | What it does |
|---|---|
| `resolvectl status` | Shows which DNS servers the VM uses. |
| `getent hosts google.com` | Looks up `google.com` the same way most programs do. |

If `getent` returns an address, DNS is working.

### ✅ What you should see

A line such as `2607:f8b0:4004:c1b::65 google.com` or an IPv4 address followed by `google.com`.

### ⚠️ If it doesn't

If nothing is printed, DNS is not working. Check the DNS servers shown by `resolvectl status`. A quick test is to try a public DNS such as `8.8.8.8`; if `ping -c 3 8.8.8.8` works but names do not, DNS is the issue.

## 2.3 Check Internet connectivity

### 🧠 What this step does

Tries to actually fetch web pages from the two sites we will rely on.

```bash
curl -I https://kubernetes.io
curl -I https://docs.tigera.io
```

| Part | Meaning |
|---|---|
| `curl` | A tool for fetching web pages from the command line. |
| `-I` | Ask only for the HTTP **headers** (a quick "are you there?"), not the whole page. |

### ✅ What you should see

A first line like `HTTP/2 200` (or `301`/`302`, which are redirects and are also fine).

### ⚠️ If it doesn't

Messages like `Could not resolve host` mean DNS trouble. `Connection timed out` usually means a firewall or proxy is blocking you. If you are on a corporate network, you may need proxy settings.

## 2.4 Check the node can reach itself

### 🧠 What this step does

Confirms the VM can "talk to itself" using its own IP address.

Replace the IP:

```bash
ping -c 3 <NODE_IP>
```

| Part | Meaning |
|---|---|
| `ping` | Sends small test packets and waits for replies. |
| `-c 3` | Send exactly 3 packets, then stop. |
| `<NODE_IP>` | Your VM's IP from step 1.5, for example `192.168.30.100`. |

### ✅ What you should see

`3 packets transmitted, 3 received, 0% packet loss`.

## 2.5 Check required Kubernetes API port

### 🧠 What this step does

Explains which port the Kubernetes API server uses, and how to confirm it is listening **after** the cluster has been created.

The Kubernetes API server will normally listen on:

```text
6443/tcp
```

💡 **Analogy:** An IP address is like a building's street address; a **port** is like an apartment number. `6443` is the "apartment" where the Kubernetes front door lives.

Check after kubeadm initialization (Section 17), not now:

```bash
sudo ss -lntp | grep 6443
```

| Part | Meaning |
|---|---|
| `ss` | Lists network sockets (open connections and listening ports). |
| `-l` | Only show **listening** sockets. |
| `-n` | Show numbers instead of names. |
| `-t` | TCP only. |
| `-p` | Show which program owns each socket. |
| `grep 6443` | Filter to lines containing 6443. |

### ✅ What you should see (after init)

A line containing `*:6443` or `:::6443` and `kube-apiserver`.

---

# 3. Verify VM Identity

## 🧠 What this step does

Records three things that identify your VM: **hostname**, **MAC address** and **product UUID**.

## 🎯 Why it matters

Kubernetes requires every node in a cluster to have a **unique** hostname, MAC address and product UUID. With one node this is automatically true, **but** if you cloned this VM from another one, or plan to add more nodes later by cloning, duplicates will cause nasty problems. Checking now builds the habit and gives you a record.

For this one-node cluster, verify them now:

```bash
hostnamectl
ip link
cat /sys/class/dmi/id/product_uuid
```

MAC addresses:

```bash
ip link show
```

💡 A **MAC address** is a hardware address for a network card. It appears after `link/ether` (for example `link/ether 52:54:00:ab:cd:ef`).

Product UUID:

```bash
cat /sys/class/dmi/id/product_uuid
```

This prints a long identifier such as `4C4C4544-0042-3010-8057-B2C04F4B4C32`. If you get "Permission denied", run it with `sudo`.

### ✅ What you should see

A hostname, one or more MAC addresses, and a UUID. No action is needed. Just note them.

### ⚠️ If you cloned this VM

If you made this VM by copying another VM that is part of a cluster, regenerate the MAC address and UUID in your hypervisor so they are different.

---

# 4. Update the Operating System

## 🧠 What this step does

Downloads the latest security fixes and bug fixes for Ubuntu, then installs a handful of helper tools that Kubernetes and this guide rely on.

## 🎯 Why it matters

An out-of-date system can be missing fixes that Kubernetes and the kernel need. Installing helper tools now prevents "command not found" errors later.

```bash
sudo apt update
sudo apt upgrade -y
```

| Command | What it does |
|---|---|
| `sudo apt update` | Refreshes the **list** of available packages (does not install anything). |
| `sudo apt upgrade -y` | Installs newer versions of everything already on the system. `-y` automatically answers "yes" to the confirmation question. |

This can take several minutes. If a purple/blue screen appears asking which services to restart, accept the defaults by pressing **Enter**.

Install basic utilities:

```bash
sudo apt install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gpg \
  vim \
  git \
  jq \
  socat \
  conntrack \
  ebtables \
  ethtool \
  iproute2 \
  iptables
```

### What each tool is for

| Package | Why we need it |
|---|---|
| `apt-transport-https` | Lets `apt` download from `https://` repositories. |
| `ca-certificates` | Trusted certificates, so HTTPS connections are verified. |
| `curl` | Downloads files and web pages. |
| `gpg` | Verifies the signature on Kubernetes packages (proves they are genuine). |
| `vim` | A text editor. (You may use `nano` instead if you prefer; it is easier for beginners.) |
| `git` | Version control; handy for downloading examples. |
| `jq` | Reads and filters JSON output. |
| `socat` | Network relay tool used by `kubectl port-forward`. |
| `conntrack` | Lets you inspect the kernel's connection-tracking table; used by Kubernetes networking. |
| `ebtables`, `ethtool` | Low-level network tools that kubeadm checks for during preflight. |
| `iproute2` | Provides the `ip` command. |
| `iptables` | The classic Linux firewall tool (needed by Kubernetes components even in eBPF mode). |

Reboot if the kernel or core system packages were upgraded:

```bash
sudo reboot
```

💡 If you are not sure whether a reboot is needed, reboot anyway. It is harmless here and ensures you are running the newest kernel.

After reconnecting (wait about 30–60 seconds, then SSH in again):

```bash
uname -r
uptime
```

| Command | What it shows |
|---|---|
| `uname -r` | The kernel you are now running (it may have changed after the reboot). |
| `uptime` | How long the machine has been running. It should be very short now. |

### ✅ What you should see

`uptime` shows only a minute or two. This confirms the reboot happened.

---

# 5. Disable Swap

## 🧠 What this step does

**Swap** is disk space the operating system uses as "emergency memory" when RAM is full. This step turns swap **off**, both right now and permanently.

## 🎯 Why it matters

By default, the kubelet **refuses to start** if swap is on. Kubernetes wants to manage memory precisely: when a Pod asks for 1 GB of RAM, Kubernetes wants that to be real RAM, not slow disk pretending to be RAM.

Kubernetes kubelet requires swap to be disabled unless a deliberate supported swap configuration is being used.

Check:

```bash
swapon --show
free -h
```

| Command | What it shows |
|---|---|
| `swapon --show` | Lists active swap areas. No output means no swap. |
| `free -h` | The `Swap:` row shows total swap; `0B` means none. |

Disable immediately:

```bash
sudo swapoff -a
```

`swapoff -a` turns off **all** swap right now. But this only lasts until the next reboot.

Disable swap permanently:

```bash
sudo sed -i.bak '/\sswap\s/s/^/#/' /etc/fstab
```

### Explaining that scary-looking command

| Part | Meaning |
|---|---|
| `/etc/fstab` | The file that lists disks/partitions mounted at boot, including swap. |
| `sed` | A tool that edits text automatically. |
| `-i.bak` | Edit the file **in place**, and keep a backup copy named `fstab.bak`. |
| `'/\sswap\s/s/^/#/'` | "Find lines containing the word `swap`, and put a `#` at the start." A `#` turns the line into a comment so Linux ignores it. |

So you are not deleting anything, only "commenting out" the swap line, and a backup exists.

Verify:

```bash
swapon --show
```

Expected:

```text
<no output>
```

Also verify:

```bash
free -h
```

### ✅ What you should see

`swapon --show` prints nothing. `free -h` shows `Swap: 0B 0B 0B`.

### ⚠️ If it doesn't

On Ubuntu cloud images swap may be a file like `/swap.img`. Run `grep swap /etc/fstab` to confirm the line now begins with `#`. If swap returns after a reboot, this line was not commented out.

---

# 6. Configure Kernel Modules

## 🧠 What this step does

**Kernel modules** are plug-in features for the Linux kernel. We need two:

| Module | What it provides |
|---|---|
| `overlay` | A filesystem type that containers use to layer files efficiently. |
| `br_netfilter` | Lets the firewall system see traffic that crosses a network "bridge" (Pods are connected through bridges). |

## 🎯 Why it matters

Without these, containers cannot start properly and Pod network traffic can bypass rules.

Create:

```bash
sudo tee /etc/modules-load.d/k8s.conf > /dev/null <<'EOF'
overlay
br_netfilter
EOF
```

### What this command does

| Part | Meaning |
|---|---|
| `sudo tee /etc/modules-load.d/k8s.conf` | Writes text into a file as the administrator. (`tee` is used because a plain `>` cannot combine with `sudo` easily.) |
| `> /dev/null` | Hides `tee`'s on-screen echo of the text. |
| `<<'EOF' ... EOF` | A "here-document": everything between the two `EOF` markers becomes the file's contents. |

This file tells Linux to load both modules **every time the VM boots**.

Load them:

```bash
sudo modprobe overlay
sudo modprobe br_netfilter
```

`modprobe` loads a module **right now**, without needing a reboot.

Verify:

```bash
lsmod | grep overlay
lsmod | grep br_netfilter
```

### ✅ What you should see

Each command prints at least one line starting with the module name (e.g., `overlay   151552  0`). If a command prints nothing, that module is not loaded.

For Calico eBPF, also verify that the kernel exposes the BPF-related functionality expected by the selected Calico version.

Useful checks:

```bash
mount | grep /sys/fs/bpf
bpftool version 2>/dev/null || true
```

| Part | Meaning |
|---|---|
| `mount \| grep /sys/fs/bpf` | Checks whether the special BPF filesystem is mounted. Calico stores eBPF data there. |
| `bpftool version 2>/dev/null \|\| true` | Prints the `bpftool` version if installed; otherwise stays quiet instead of showing an error. |

If `bpftool` is not installed:

```bash
sudo apt install -y linux-tools-common linux-tools-$(uname -r)
```

`bpftool` is a diagnostic tool for inspecting eBPF programs. `$(uname -r)` is replaced automatically by your kernel version, so the matching tools package is installed.

Then:

```bash
bpftool version
```

### ✅ What you should see

A line such as `bpftool v7.x.x`. It is fine if `/sys/fs/bpf` is not mounted yet. Modern systems and Calico usually mount it automatically. If `linux-tools-$(uname -r)` is not found for your kernel, installing `linux-tools-generic` instead is a common workaround.

---

# 7. Configure Kernel Networking

## 🧠 What this step does

Sets three **kernel settings** (called *sysctl* parameters) that Kubernetes networking depends on.

| Setting | What it does |
|---|---|
| `net.ipv4.ip_forward = 1` | Allows the VM to **forward** network packets between interfaces, acting like a router. Pods rely on this to reach each other and the internet. |
| `net.bridge.bridge-nf-call-iptables = 1` | Makes bridged IPv4 traffic pass through the firewall rules. |
| `net.bridge.bridge-nf-call-ip6tables = 1` | The same for IPv6. |

## 🎯 Why it matters

If `ip_forward` is `0`, Pods cannot route traffic out of the machine. `kubeadm init` will refuse to continue.

Create:

```bash
sudo tee /etc/sysctl.d/99-kubernetes-calico.conf > /dev/null <<'EOF'
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF
```

This saves the settings in a file so they survive reboots. (The `99-` prefix means "load this one last", so nothing overrides it.)

Apply:

```bash
sudo sysctl --system
```

This reads all sysctl configuration files and applies them **right now**. You will see a lot of output. That is normal.

Verify:

```bash
sysctl net.ipv4.ip_forward
sysctl net.bridge.bridge-nf-call-iptables
sysctl net.bridge.bridge-nf-call-ip6tables
```

Expected:

```text
net.ipv4.ip_forward = 1
```

### ✅ What you should see

All three commands print `= 1`.

### ⚠️ If it doesn't

If you get `cannot stat /proc/sys/net/bridge/...: No such file or directory`, the `br_netfilter` module from Section 6 is not loaded. Run `sudo modprobe br_netfilter` and try again.

---

# 8. Verify iptables

## 🧠 What this step does

**Records** (does not change) how your VM's firewall tooling is set up.

## 🎯 Why it matters

Modern Linux has two iptables "backends" (called *legacy* and *nft*). Mixing them can cause confusing behaviour. Knowing which one you have makes troubleshooting much easier.

Check:

```bash
iptables --version
```

Look at the version text. `(nf_tables)` or `(legacy)` tells you which backend is active.

Also:

```bash
sudo iptables -L -n
```

Lists all current firewall rules. `-L` = list, `-n` = show numbers instead of trying to resolve names (faster). A fresh VM usually has empty or very short rules.

Check nftables backend if relevant:

```bash
iptables -V
```

(`-V` is the same as `--version`.)

Do not blindly change firewall/iptables backends. Record the current environment before proceeding.

### ✅ What you should see

A version like `iptables v1.8.7 (nf_tables)`. No action is needed. Just write it down.

---

# 9. Configure Firewall

## 🧠 What this step does

A **firewall** blocks or allows network connections. This step makes you check that the firewall will not block Kubernetes.

## 🎯 Why it matters

If a firewall blocks port `6443`, you (and the cluster's own components) cannot reach the API server.

For a single VM, the exact firewall depends on the VM network.

At minimum, ensure Kubernetes API access is possible:

```text
6443/tcp
```

If using UFW (Ubuntu's simple firewall tool):

```bash
sudo ufw status
```

### ✅ What you should see

- `Status: inactive`: no firewall is running. Nothing to configure for a lab.
- `Status: active`: UFW is on. You must allow the ports you need, for example:

```bash
sudo ufw allow 22/tcp      # SSH, so you do not lock yourself out
sudo ufw allow 6443/tcp    # Kubernetes API server
```

⚠️ **Be careful:** If you enable UFW without first allowing SSH (22/tcp), you will lock yourself out of the VM.

If SSH is required:

```text
22/tcp
```

For a self-hosted environment, document whether the VM is:

```text
[ ] Behind NAT
[ ] Directly reachable
[ ] Private network only
[ ] Publicly reachable
```

(Tick whichever applies. This helps you decide how careful to be. A publicly reachable VM needs much stricter rules.)

Do not expose Kubernetes API port 6443 publicly unless there is a deliberate security design.

---

# 10. Install containerd

## 🧠 What this step does

Installs **containerd**, the program that actually pulls container images from the internet and runs them.

💡 **Analogy:** Kubernetes is the restaurant manager who decides which dishes to make. The kubelet is the waiter taking orders. **containerd is the cook** who actually prepares each dish (runs each container).

## 🎯 Why it matters

Kubernetes cannot run a single container without a container runtime. No runtime means no Pods.

## 10.1 Install containerd

```bash
sudo apt update
sudo apt install -y containerd
```

Verify:

```bash
containerd --version
```

Check service:

```bash
sudo systemctl status containerd --no-pager
```

| Part | Meaning |
|---|---|
| `systemctl` | The tool that starts, stops and inspects background services on Ubuntu. |
| `status containerd` | Shows whether the containerd service is running. |
| `--no-pager` | Prints everything at once instead of opening a scrolling viewer. (If you ever get stuck in a viewer, press `q` to quit.) |

### ✅ What you should see

A version line such as `containerd github.com/containerd/containerd 1.7.x`, and in the status output a green `active (running)`.

---

# 11. Configure containerd

## 🧠 What this step does

Creates containerd's configuration file and changes **one setting**: `SystemdCgroup = true`.

## 🎯 Why it matters (the most common beginner failure)

**cgroups** are how Linux limits and tracks the CPU and memory used by each process. Two programs are involved here: **systemd** (Ubuntu's service manager) and **containerd**. Kubernetes expects both to use the **same** cgroup manager, namely systemd. If containerd uses a different one, the node can become unstable, and Pods may restart randomly or the control plane may keep crashing.

💡 **Analogy:** If two managers both try to control the same worker's schedule using different calendars, the worker gets double-booked. We make both use the same calendar (systemd).

Create a default configuration:

```bash
sudo mkdir -p /etc/containerd

containerd config default | \
  sudo tee /etc/containerd/config.toml > /dev/null
```

| Part | Meaning |
|---|---|
| `mkdir -p /etc/containerd` | Creates the folder if it doesn't already exist. `-p` means "no error if it exists". |
| `containerd config default` | Prints containerd's built-in default configuration. |
| `\| sudo tee /etc/containerd/config.toml` | Saves that output into the real config file. |

Edit:

```bash
sudo vim /etc/containerd/config.toml
```

> **Not comfortable with vim?** Use `sudo nano /etc/containerd/config.toml` instead. Or skip the editor entirely and use this one-line replacement, which does the same thing:
>
> ```bash
> sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
> ```

Find:

```toml
SystemdCgroup = false
```

Change to:

```toml
SystemdCgroup = true
```

💡 **vim quick help:** press `/` then type `SystemdCgroup` and Enter to search; press `i` to start typing; change `false` to `true`; press `Esc`; type `:wq` and Enter to save and quit.

Verify:

```bash
grep -n "SystemdCgroup" /etc/containerd/config.toml
```

`grep -n` searches a file for text and shows the **line number** where it was found.

Expected:

```text
SystemdCgroup = true
```

Restart:

```bash
sudo systemctl restart containerd
sudo systemctl enable containerd
```

| Command | Meaning |
|---|---|
| `restart` | Stops and starts containerd so it reads the new config. |
| `enable` | Makes containerd start automatically every time the VM boots. |

Verify:

```bash
sudo systemctl is-active containerd
sudo systemctl is-enabled containerd
```

### ✅ What you should see

```text
active
enabled
```

### ⚠️ If it doesn't

If containerd shows `failed`, you probably introduced a typo in the config file. Run `sudo journalctl -u containerd -n 50 --no-pager` to see the error, or regenerate the default file and try again.

---

# 12. Verify CRI

## 🧠 What this step does

Checks that containerd is offering the **CRI** (Container Runtime Interface). CRI is the standard "plug socket" kubelet uses to talk to the runtime.

## 🎯 Why it matters

On some systems, a packaged containerd ships with CRI **disabled**. If CRI is off, kubeadm cannot start the cluster. Confirm it now rather than discovering it halfway through.

Check that containerd exposes the CRI plugin:

```bash
sudo ctr plugins ls | grep cri
```

`ctr` is containerd's own command-line client. `plugins ls` lists its plugins and `grep cri` keeps only the CRI line.

Expected status should be:

```text
ok
```

Also check:

```bash
sudo crictl info
```

If `crictl` is available. (`crictl` is a tool for talking to any CRI runtime. It is installed along with the Kubernetes packages in Section 13, so it may not exist yet. **If you get "command not found", skip this and re-check after Section 13.**)

Verify runtime endpoint if configured:

```bash
sudo crictl info | jq '.config.containerdEndpoint // .config.containerd.endpoint // empty'
```

This uses `jq` to dig out the runtime's socket address from the JSON. It is optional.

### ✅ What you should see

A line containing `io.containerd.grpc.v1  cri  ...  ok`.

### ⚠️ If it doesn't

If CRI is missing or shows an error, check that `/etc/containerd/config.toml` does not contain the line `disabled_plugins = ["cri"]`. If it does, remove `"cri"` from that list and restart containerd.

---

# 13. Install Kubernetes Packages

## 🧠 What this step does

Adds the official Kubernetes software repository to Ubuntu, then installs three tools:

| Tool | Role |
|---|---|
| `kubeadm` | Builds the cluster. |
| `kubelet` | The node agent that runs Pods. |
| `kubectl` | The command-line remote control. |

## 🎯 Why it matters

Ubuntu's own repositories do not contain current Kubernetes releases. We have to add the official source (and its signing key, so we know the downloads are genuine).

Choose the Kubernetes minor version deliberately.

> 💡 A **minor version** is the middle number: in `v1.37.2`, the minor version is `37`. Each minor release gets its own repository. Check https://kubernetes.io/releases/ for the currently supported versions before choosing.

The example below uses the Kubernetes **v1.36** repository, which is the version this guide was tested with. Kubernetes v1.37 also exists, but check Calico's requirements page before using it. If you choose another supported minor release, change the repository version consistently (both places where `v1.36` appears below).

```bash
sudo mkdir -p -m 755 /etc/apt/keyrings

curl -fsSL \
  https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key \
  | sudo gpg --dearmor \
  -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```

### Explaining this command

| Part | Meaning |
|---|---|
| `mkdir -p -m 755 /etc/apt/keyrings` | Creates a folder for security keys, readable by everyone. |
| `curl -fsSL <url>` | Downloads the key quietly (`-s`), shows errors (`-S`), fails on HTTP errors (`-f`), follows redirects (`-L`). |
| `gpg --dearmor` | Converts the key from text to the binary format `apt` expects. |
| `-o <file>` | Saves the result in that file. |

Add repository:

```bash
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' \
  | sudo tee /etc/apt/sources.list.d/kubernetes.list
```

This writes one line into a file telling `apt`: "You may also download packages from pkgs.k8s.io, and verify them using this key."

Update:

```bash
sudo apt update
```

### ✅ What you should see

Lines mentioning `pkgs.k8s.io` and no `NO_PUBKEY` or `404` errors. A `404` normally means the version number in the URL doesn't exist; double-check it.

Install:

```bash
sudo apt install -y kubelet kubeadm kubectl
```

Hold:

```bash
sudo apt-mark hold kubelet kubeadm kubectl
```

### 🎯 What "hold" does and why

It tells Ubuntu: "Do **not** automatically upgrade these three packages." A surprise Kubernetes upgrade during a routine `apt upgrade` can break a running cluster. Upgrades should be planned and done deliberately.

Verify:

```bash
kubeadm version
kubectl version --client
kubelet --version
```

### ✅ What you should see

All three report the same version, such as `v1.36.x`. (`kubectl version --client` may also mention a "Kustomize Version". That's normal.)

---

# 14. Enable kubelet

## 🧠 What this step does

Tells Ubuntu to start the **kubelet** service automatically at boot.

```bash
sudo systemctl enable kubelet
```

It is normal for kubelet to restart/fail before kubeadm has initialized the cluster.

### 💡 Why does it "fail" now?

kubelet is the waiter, but there is no restaurant yet. It keeps starting up and restarting, waiting for instructions that `kubeadm init` will provide in a later step. This is expected, **not** a mistake you made.

Check:

```bash
sudo systemctl status kubelet --no-pager
```

### ✅ What you should see

Something like `activating (auto-restart)` or `exited`. Do not try to fix this.

Do not treat pre-`kubeadm init` kubelet errors as the final cluster state.

---

# 15. Final Pre-kubeadm Verification

## 🧠 What this step does

A **pre-flight checklist**, as pilots do. You run a bundle of checks to confirm every earlier step is truly done before the big step (`kubeadm init`).

## 🎯 Why it matters

`kubeadm init` is the hardest step to cleanly undo. Ten minutes of checking here can save an hour of cleanup.

Run all of these before initialization:

```bash
hostname
hostname -I
uname -r
cat /etc/os-release
free -h
swapon --show
nproc
df -h /
ip route
```

| Command | What it confirms |
|---|---|
| `hostname` | Name is correct. |
| `hostname -I` | Prints all IP addresses of the VM. Your `<NODE_IP>` should appear. |
| `uname -r` / `cat /etc/os-release` | Kernel/OS compatible. |
| `free -h` / `nproc` / `df -h /` | Enough RAM, CPU, disk. |
| `swapon --show` | Prints nothing (swap off). |
| `ip route` | Default route present. |

Runtime:

```bash
containerd --version
sudo systemctl is-active containerd
```

Kubernetes:

```bash
kubeadm version
kubectl version --client
kubelet --version
```

Kernel:

```bash
lsmod | grep br_netfilter
lsmod | grep overlay
sysctl net.ipv4.ip_forward
```

Expected:

```text
swap: disabled
containerd: active
ip_forward: 1
overlay: loaded
br_netfilter: loaded
```

### 🛑 Stop and check

If **any** line above is wrong, go back to the relevant section and fix it first. Do not run `kubeadm init` until everything matches.

---

# 16. Decide the Kubernetes Pod and Service CIDRs

## 🧠 What this step does

You choose two ranges of IP addresses that Kubernetes will use *internally*:

| Range | Used for |
|---|---|
| **Pod CIDR** | Addresses given to Pods. |
| **Service CIDR** | Addresses given to Services (virtual, stable addresses in front of Pods). |

💡 **What is a CIDR?** It's shorthand for "a block of addresses". `192.168.0.0/16` means "every address from 192.168.0.0 to 192.168.255.255" (about 65,000 addresses). The `/16` says how many of the first bits are fixed; a smaller number after the slash means a bigger block.

Example:

```text
Pod CIDR:     192.168.0.0/16
Service CIDR: 10.96.0.0/12
```

## 🎯 Why it matters

These ranges must **not overlap** with any real network your VM or you can reach. If they do, traffic meant for a Pod might get sent to your home router instead, or vice versa. This produces strange "it works from some places but not others" problems.

For a single-node lab, keep the CIDRs simple and make sure they do not overlap with:

- VM LAN
- VPN
- Docker networks
- corporate network
- host network
- other routed networks

Check current routes:

```bash
ip route
```

Example:

```text
192.168.30.0/24
```

Do not choose a Pod CIDR that overlaps with that network.

> ### ⚠️ Important beginner warning: check the example against *your* network
>
> The example IP in Section 1.5 (`192.168.30.100`) sits **inside** the example Pod CIDR `192.168.0.0/16`. That is a real overlap!
>
> - If your VM's network is **`192.168.x.x`**, choose a different Pod CIDR such as **`10.244.0.0/16`** (check that your network isn't `10.x.x.x` first).
> - If your VM's network is **`10.x.x.x` or `172.16.x.x`**, the default `192.168.0.0/16` is fine.
>
> **Whatever you choose, use the *same* Pod CIDR in two places:** (1) `kubeadm init --pod-network-cidr=...` in Section 17, and (2) the `cidr:` line of the Calico Installation file in Section 22. This guide's examples keep `192.168.0.0/16`; change them both together if needed.

### ✅ What you should do

Write down your final choice:

```text
Pod CIDR:     ____________________
Service CIDR: ____________________   (10.96.0.0/12 is the Kubernetes default and rarely needs changing)
```

---

# 17. Initialize Kubernetes Without kube-proxy

## 🧠 What this step does

This is **the** big step. `kubeadm init` turns your VM into a Kubernetes control plane. Behind the scenes it:

1. Runs preflight checks.
2. Generates certificates (so components can trust each other).
3. Starts the API server, scheduler, controller-manager and etcd as containers.
4. Writes `admin.conf`, the file that lets you log in as cluster administrator.
5. Installs CoreDNS (cluster DNS).
6. Normally installs **kube-proxy**, but we are telling it **not to**.

This is the critical step.

## 🎯 Why we skip kube-proxy

Calico eBPF can provide Kubernetes Service networking without kube-proxy.

For a new kubeadm cluster, skip kube-proxy during initialization:

```bash
sudo kubeadm init \
  --apiserver-advertise-address=<NODE_IP> \
  --pod-network-cidr=192.168.0.0/16 \
  --service-cidr=10.96.0.0/12 \
  --skip-phases=addon/kube-proxy
```

Replace `<NODE_IP>` with your VM's static IP from Section 1.5 (for example `10.11.204.124`). Do not paste the `<` and `>` characters.

### Explaining each option

| Option | Meaning |
|---|---|
| `--apiserver-advertise-address=<NODE_IP>` | Pins the API server to your VM's static IP. Calico eBPF needs this real address later (Section 21.1). |
| `--pod-network-cidr=192.168.0.0/16` | The range for Pod IPs (from Section 16). |
| `--service-cidr=10.96.0.0/12` | The range for Service IPs. |
| `--skip-phases=addon/kube-proxy` | Skip the step that installs kube-proxy. **Do not forget this!** It is much easier to skip it now than to remove it later. |

This command takes **2–5 minutes** and downloads several container images. Do not press Ctrl+C. Wait for it to finish.

### ✅ What you should see

At the very end:

```text
Your Kubernetes control-plane has initialized successfully!
```

followed by instructions and a `kubeadm join ...` command.

Record the complete output.

Especially save the worker join command if you later expand this cluster.

💡 **Tip:** Copy the entire output into a text file. The `kubeadm join` line contains a token that expires after 24 hours, but you can create a new one later with `kubeadm token create --print-join-command`.

### ⚠️ If it fails

- `[ERROR Swap]`: swap is still on (Section 5).
- `[ERROR CRI]`: containerd is not running or CRI is disabled (Sections 10–12).
- `[ERROR FileContent--proc-sys-net-ipv4-ip_forward]`: forwarding is off (Section 7).
- `connection refused` while pulling images: internet/DNS problem (Section 2).

After fixing the problem, clean up with `sudo kubeadm reset -f` (see Section 64) and run `kubeadm init` again.

---

# 18. Configure kubectl

## 🧠 What this step does

`kubectl` needs to know **where** the cluster is and **who you are**. Both are in a file called `admin.conf`. This step copies that file into your own home folder so that you can run `kubectl` as a normal user, without `sudo`.

After successful initialization:

```bash
mkdir -p $HOME/.kube

sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config

sudo chown "$(id -u):$(id -g)" $HOME/.kube/config
```

| Command | Meaning |
|---|---|
| `mkdir -p $HOME/.kube` | Creates a hidden `.kube` folder in your home directory. |
| `sudo cp -i ... $HOME/.kube/config` | Copies the admin file. (`-i` asks before overwriting an existing file; answer `y` if asked.) |
| `sudo chown "$(id -u):$(id -g)" ...` | Makes **you** the owner of the file, since `sudo cp` made root the owner. `id -u` and `id -g` print your user and group numbers. |

> 🔒 **Security note:** `admin.conf` is the master key to your cluster. Treat `~/.kube/config` like a password. Never share it or commit it to Git.

Verify:

```bash
kubectl cluster-info
```

### ✅ What you should see

Lines such as `Kubernetes control plane is running at https://<NODE_IP>:6443` and `CoreDNS is running at ...`.

Then:

```bash
kubectl get nodes
```

At this point the node may be:

```text
NotReady
```

That is expected before a CNI is installed.

💡 **Why NotReady?** A node is "Ready" only when it has working Pod networking. We haven't installed Calico yet, so Kubernetes (correctly) says "I can't give Pods network addresses yet". It becomes `Ready` in Section 25.

### ⚠️ If it doesn't

`The connection to the server localhost:8080 was refused` means kubectl cannot find its config file. Re-run the three commands above.

---

# 19. Verify kube-proxy Was Not Installed

## 🧠 What this step does

Double-checks that the `--skip-phases` option really worked.

## 🎯 Why it matters

If kube-proxy is present, it would compete with Calico eBPF (remember the two traffic controllers!). It's much easier to find out now.

Run:

```bash
kubectl -n kube-system get daemonset
```

| Part | Meaning |
|---|---|
| `-n kube-system` | Look in the `kube-system` namespace (a "folder" inside Kubernetes where system components live). |
| `get daemonset` | List DaemonSets. kube-proxy normally runs as one. |

Check specifically:

```bash
kubectl -n kube-system get daemonset kube-proxy
```

Expected:

```text
Error from server (NotFound)
```

✅ **Yes, an error is the *good* result here.** `NotFound` means kube-proxy does not exist.

Also:

```bash
kubectl -n kube-system get pods
```

There should not be a kube-proxy Pod.

You will likely see `coredns` Pods in `Pending` state and control-plane Pods (`etcd`, `kube-apiserver`, ...) `Running`. CoreDNS stays `Pending` until Calico is installed. This is normal.

This is an important checkpoint.

### 🛑 Stop and check

If kube-proxy **does** exist, jump to Section 56 before continuing.

---

# 20. Allow the Control Plane to Run Workloads

## 🧠 What this step does

By default, Kubernetes puts a **taint** (a "keep out" sign) on control-plane nodes so that normal applications don't run on them. That's the right design for big clusters but wrong for ours, because our one node must run **everything**. We remove the taint.

## 🎯 Why it matters

Without this step, any Pod you create (including Calico's own helper Pods and CoreDNS) would stay `Pending` forever with "node(s) had untolerated taint".

Because this is a one-machine cluster, the control-plane node must also function as a worker.

Check taints:

```bash
kubectl describe node "$(hostname)" | grep -i taint
```

| Part | Meaning |
|---|---|
| `kubectl describe node <name>` | Prints detailed information about the node. |
| `"$(hostname)"` | Automatically fills in this VM's hostname as the node name. |
| `grep -i taint` | Shows only lines mentioning "taint" (`-i` = ignore upper/lower case). |

### ✅ What you should see (before)

```text
Taints:             node-role.kubernetes.io/control-plane:NoSchedule
```

Remove the default control-plane taint:

```bash
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

⚠️ **The trailing `-` (minus sign) is not a typo.** In `kubectl taint`, a minus at the end means "**remove** this taint".

Verify:

```bash
kubectl describe node "$(hostname)" | grep -i taint
```

### ✅ What you should see (after)

```text
Taints:             <none>
```

---

# 21. Install Calico

## 🧠 What this step does

Installs Calico in two parts:

1. **CRDs** (Custom Resource Definitions): these teach Kubernetes new vocabulary, like "Installation" and "NetworkPolicy (Calico flavour)".
2. **The Tigera Operator**: a program that reads the settings you give it and **builds and maintains Calico for you**.

💡 **Analogy:** The CRDs are like adding new words to Kubernetes' dictionary. The operator is a **contractor** you hire: you hand over a plan (Section 22) and it does the building.

## 🎯 Why we use the operator

Current Calico documentation recommends the operator for new installations. It handles upgrades and configuration cleanly.

Install the appropriate Calico CRDs for the Kubernetes version.

For Kubernetes 1.36+:

```bash
kubectl create -f \
  https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/v3_projectcalico_org.yaml
```

| Part | Meaning |
|---|---|
| `kubectl create -f <url>` | Create everything described in the file at that URL. |
| `v3.33.0` | The Calico version. Check the official docs (Section 71) in case a newer matching version is recommended for your Kubernetes version. |

Install the Tigera Operator:

```bash
kubectl create -f \
  https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/tigera-operator.yaml
```

### ✅ What you should see

A long list of lines ending in `created`, for example `customresourcedefinition.apiextensions.k8s.io/... created`. No `Error` lines.

> ## 🛑 Important: the operator will crash until you do Step 21.1
>
> The operator normally finds the API server through the Service address `10.96.0.1`, and **only kube-proxy makes that address work**. We skipped kube-proxy on purpose, so the operator starts, times out, and crashes (you will see `Running → Error → CrashLoopBackOff`). This is expected. Fix it right now with Step 21.1.

## 21.1 Tell Calico the API server's real address (REQUIRED without kube-proxy)

### 🧠 What this step does

Creates a small ConfigMap named `kubernetes-services-endpoint` that tells the Tigera Operator, and later `calico-node`, to connect **directly** to your node's IP and port 6443 instead of the Service address `10.96.0.1`.

### 🎯 Why it matters

This breaks the chicken-and-egg problem: Calico replaces kube-proxy, but Calico itself must reach the API server before it can do that.

Replace `10.11.204.124` with **your** node IP:

```bash
kubectl apply -f - <<'EOF'
kind: ConfigMap
apiVersion: v1
metadata:
  name: kubernetes-services-endpoint
  namespace: tigera-operator
data:
  KUBERNETES_SERVICE_HOST: "10.11.204.124"
  KUBERNETES_SERVICE_PORT: "6443"
EOF
```

Restart the operator so it reads the new settings:

```bash
kubectl delete pod -n tigera-operator -l k8s-app=tigera-operator
kubectl get pods -n tigera-operator -w
```

Press **Ctrl+C** when it shows `1/1 Running`.

### ✅ What you should see

After about 2 minutes: `1/1 Running`, `RESTARTS 0`, and in the logs `Waiting for an Installation`:

```bash
kubectl get pods -n tigera-operator
kubectl logs -n tigera-operator deployment/tigera-operator --tail=15
```

### ⚠️ If it doesn't

If the logs still show `dial tcp 10.96.0.1:443: i/o timeout`, the Pod did not pick up the ConfigMap. Check the name is exactly `kubernetes-services-endpoint` in the `tigera-operator` namespace, then delete the operator Pod again.

Check:

```bash
kubectl get pods -n tigera-operator
```

Wait until the operator is running:

```bash
kubectl get pods -n tigera-operator -w
```

`-w` ("watch") keeps the command running and prints a new line whenever something changes. Press **Ctrl+C** to stop watching.

### ✅ What you should see

```text
NAME                               READY   STATUS    RESTARTS   AGE
tigera-operator-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
```

### ⚠️ If it doesn't

- `CrashLoopBackOff` with `10.96.0.1:443 i/o timeout` in the logs means you skipped Step 21.1.
- `AlreadyExists` errors mean you ran the command twice; that's harmless.
- `ImagePullBackOff` means the VM can't download the image (check internet/DNS).
- A very large CRD may fail with `metadata.annotations: Too long`. In that case, use `kubectl create` as shown (not `apply`), or `kubectl apply --server-side -f ...`.

---

# 22. Configure Calico eBPF

## 🧠 What this step does

You write a short **YAML** file (the "plan" for the contractor) that says: "Install Calico, use the eBPF dataplane, and I have no kube-proxy. (The API server address comes from the ConfigMap in Step 21.1.)" Then you hand it to Kubernetes.

## 🎯 Why it matters

This single file is what switches on eBPF mode and makes Calico responsible for Services.

For this cluster, use Calico's eBPF dataplane.

Create a Calico Installation resource.

Example:

```yaml
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  variant: Calico

  calicoNetwork:
    linuxDataplane: BPF
    bpfNetworkBootstrap: Disabled
    kubeProxyManagement: Disabled
    ipPools:
      - cidr: 192.168.0.0/16
        encapsulation: VXLAN
```

### Line-by-line explanation

| Line | Meaning |
|---|---|
| `apiVersion: operator.tigera.io/v1` | Which "dictionary" this object belongs to (the Tigera operator's). |
| `kind: Installation` | The type of object: a Calico installation request. |
| `name: default` | The operator expects this exact name. Don't change it. |
| `variant: Calico` | Install open-source Calico (the alternative is Tigera's commercial "Calico Enterprise"). |
| `linuxDataplane: BPF` | Use eBPF instead of iptables. **The key setting.** |
| `bpfNetworkBootstrap: Disabled` | Do **not** use Calico's automatic bootstrap. We gave the API server address ourselves in Step 21.1 (explained in Section 23). |
| `kubeProxyManagement: Disabled` | Do **not** make the operator look for a kube-proxy DaemonSet (we have none; explained in Section 23). |
| `ipPools / cidr` | The Pod address range. **Must match** the `--pod-network-cidr` you used in Section 17. |
| `encapsulation: VXLAN` | How Pod traffic is wrapped when it travels between nodes. eBPF mode works with VXLAN (not IP-in-IP). With one node it's not used, but it's correct to set for later growth. |

> ⚠️ **YAML is strict about spaces.** Use **spaces**, never tabs, and keep the indentation exactly as shown (2 spaces per level). A single misplaced space makes the file invalid.
>
> ⚠️ If you chose a different Pod CIDR in Section 16, change the `cidr:` line to match.

Save as:

```text
calico-installation.yaml
```

One easy way to create the file is to paste this into your terminal:

```bash
cat > calico-installation.yaml <<'EOF'
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  variant: Calico

  calicoNetwork:
    linuxDataplane: BPF
    bpfNetworkBootstrap: Disabled
    kubeProxyManagement: Disabled
    ipPools:
      - cidr: 192.168.0.0/16
        encapsulation: VXLAN
EOF
```

Apply:

```bash
kubectl apply -f calico-installation.yaml
```

`kubectl apply -f <file>` means "make the cluster match what this file describes".

### ✅ What you should see

```text
installation.operator.tigera.io/default created
```

Check:

```bash
kubectl get installation.operator.tigera.io default -o yaml
```

`-o yaml` prints the full stored object. Look for `linuxDataplane: BPF` in the output.

### ⚠️ If it doesn't

- `no matches for kind "Installation"`: the Tigera Operator CRDs are not installed yet. Redo Section 21 and wait for the operator Pod to be `Running`.
- `error converting YAML`: indentation problem. Compare with the example.
- After applying, `kubectl get tigerastatus` shows `DEGRADED True` with `bpfNetworkBootstrap is Enabled but the requirements are not met` or `failed to retrieve kube-proxy DaemonSet ... not found`: you left those two settings as `Enabled`. Change both to `Disabled`, run `kubectl apply -f calico-installation.yaml` again, and wait a few minutes (Section 55).

---

# 23. Understand the Three Important Calico eBPF Settings

## 🧠 What this section does

Explains in plain English the three lines that matter most, and **why two of them are `Disabled` on a cluster without kube-proxy**.

The important configuration is:

```yaml
calicoNetwork:
  linuxDataplane: BPF
  bpfNetworkBootstrap: Disabled
  kubeProxyManagement: Disabled
```

### `linuxDataplane: BPF`

Tells Calico to use the eBPF dataplane instead of the normal iptables dataplane.

💡 **In simple terms:** The *dataplane* is the machinery that actually moves each network packet. The old way is a long list of iptables rules the kernel checks one by one. eBPF instead runs small programs directly in the kernel, which is usually **faster and scales better**, and it can handle Services itself.

### `bpfNetworkBootstrap: Disabled`

Calico has an automatic "bootstrap" feature that can discover the API server address. But on this cluster we **already give Calico the address ourselves** through the `kubernetes-services-endpoint` ConfigMap (Step 21.1). If both are used, Calico reports `bpfNetworkBootstrap is Enabled but the requirements are not met: kubernetes service endpoint is defined by the ... ConfigMap` and goes `DEGRADED`. So we pick **one** method: the ConfigMap.

💡 **The chicken-and-egg problem:** Normally, a program inside the cluster reaches the API server through a Service address (`10.96.0.1`), and **kube-proxy** is what makes that address work. But Calico is what replaces kube-proxy! If Calico needs kube-proxy to reach the API server, and kube-proxy doesn't exist, Calico can never start. The ConfigMap breaks the loop by giving Calico (and the Tigera Operator) the API server's **real** address.

### `kubeProxyManagement: Disabled`

When `Enabled`, the Calico operator looks for a kube-proxy DaemonSet to manage (for example, to switch it off when eBPF turns on). Because this cluster was initialized with:

```bash
--skip-phases=addon/kube-proxy
```

there is no kube-proxy DaemonSet at all. With `Enabled`, the operator reports `kubeproxy-monitor DEGRADED: failed to retrieve kube-proxy DaemonSet ... not found`. So we set it to `Disabled`.

💡 **Rule of thumb:** If you **removed** kube-proxy yourself and gave Calico the endpoint ConfigMap, set both to `Disabled`. If you start from a cluster that **has** kube-proxy and want Calico to migrate it automatically, follow Calico's official migration guide instead (Section 71).

---

# 24. Monitor Calico Installation

## 🧠 What this step does

Watches Calico being built. The operator is now downloading images and starting Pods. This takes roughly **2–10 minutes**.

```bash
kubectl get tigerastatus
```

`tigerastatus` is a summary of how each Calico component is doing.

Watch:

```bash
watch kubectl get tigerastatus
```

`watch` re-runs the command every 2 seconds. Press **Ctrl+C** to stop.

### ✅ What you should see (eventually)

```text
NAME     AVAILABLE   PROGRESSING   DEGRADED   SINCE
calico   True        False         False      2m
```

| Column | Healthy value |
|---|---|
| `AVAILABLE` | `True` |
| `PROGRESSING` | `False` (when done) |
| `DEGRADED` | `False` |

It's normal to see `AVAILABLE False` and `PROGRESSING True` for the first few minutes. Be patient.

Also:

```bash
kubectl get pods -A -o wide
```

`-A` means "all namespaces". `-o wide` adds extra columns such as IP address and node.

Check Calico namespaces:

```bash
kubectl get pods -n calico-system
```

Check operator:

```bash
kubectl get pods -n tigera-operator
```

### ✅ What you should see

In `calico-system`: `calico-node-...` and `calico-kube-controllers-...` and `calico-typha-...` (typha may be absent on tiny clusters), all `Running`.

### ⚠️ If it doesn't

If it's still not healthy after 10–15 minutes, jump to Sections 54–55 and 60.

---

# 25. Verify Node Becomes Ready

## 🧠 What this step does

Checks the **node status**, the first big proof that networking works.

```bash
kubectl get nodes -o wide
```

Expected:

```text
NAME        STATUS   ROLES           AGE   VERSION
k8s-single  Ready    control-plane   ...   v1.xx.x
```

### 🎉 Milestone

`Ready` means Kubernetes now sees working Pod networking. CoreDNS Pods should also change from `Pending` to `Running` shortly (check with `kubectl get pods -n kube-system`).

If still `NotReady`, do not continue to application testing.

Investigate Calico first.

### ⚠️ If it doesn't

Go to Section 54 ("Node NotReady").

---

# 26. Verify Calico eBPF Mode

## 🧠 What this step does

Confirms Calico is **really** running in eBPF mode and not quietly in iptables mode.

## 🎯 Why it matters

If the setting didn't take effect, everything may still "work" but you would not be using eBPF at all, which defeats the purpose of this lab.

Inspect the Calico installation:

```bash
kubectl get installation default -o yaml
```

Look for:

```yaml
linuxDataplane: BPF
```

Check Calico node resources:

```bash
kubectl get pods -n calico-system -o wide
```

Inspect Felix:

```bash
kubectl logs -n calico-system \
  -l k8s-app=calico-node \
  --tail=100
```

| Part | Meaning |
|---|---|
| **Felix** | The Calico agent (inside `calico-node`) that programs the dataplane on each node. |
| `kubectl logs` | Prints the log messages of a Pod. |
| `-l k8s-app=calico-node` | Select Pods by **label**: pick Pods labelled `k8s-app=calico-node`. |
| `--tail=100` | Only the last 100 lines. |

Look for BPF/eBPF-related initialization.

### ✅ What you should see

Log lines mentioning `BPF`, for example `BPFEnabled` or `BPF dataplane`. You do not need to understand every line, just confirm BPF is mentioned and that there are no repeated `ERROR` messages.

---

# 27. Verify kube-proxy Is Absent

## 🧠 What this step does

A second, independent confirmation that nothing is running kube-proxy, now that Calico is up.

Run:

```bash
kubectl get pods -n kube-system
```

Then:

```bash
kubectl get daemonsets -A
```

There must be no active:

```text
kube-proxy
```

Also check the node:

```bash
ps aux | grep '[k]ube-proxy'
```

| Part | Meaning |
|---|---|
| `ps aux` | Lists every running process on the machine. |
| `grep '[k]ube-proxy'` | Searches for "kube-proxy". The `[k]` trick stops `grep` from matching its own command line. |

Expected:

```text
no kube-proxy process
```

### ✅ What you should see

The `grep` command prints **nothing** and the DaemonSet list shows only `calico-node` (and maybe `csi-node-driver`), not `kube-proxy`.

---

# 28. Verify Calico Is Providing Service Networking

## 🧠 What this step does

Starts a real web server (nginx) in the cluster and puts a **Service** in front of it. In the next step you will call that Service from another Pod.

💡 **Analogy:** A Pod is a employee who may be replaced at any time and gets a new phone number whenever that happens. A Service is the **company's main phone number**: it never changes, and calls get forwarded to whichever employee is currently available. In this cluster, Calico eBPF does the call forwarding.

Create a test Deployment:

```bash
kubectl create deployment nginx --image=nginx
```

| Part | Meaning |
|---|---|
| `create deployment nginx` | Create a Deployment named `nginx`. A Deployment keeps the desired number of Pods running. |
| `--image=nginx` | Use the public `nginx` web-server image. |

Check:

```bash
kubectl get pods -o wide
```

### ✅ What you should see

A Pod named `nginx-xxxxx-xxxxx` with status `Running` and an IP in your Pod CIDR (for example `192.168.x.x`). The first pull of the image may take about a minute; `ContainerCreating` is normal for a short while.

Expose it:

```bash
kubectl expose deployment nginx \
  --port=80 \
  --target-port=80 \
  --type=ClusterIP
```

| Option | Meaning |
|---|---|
| `--port=80` | The port the **Service** listens on. |
| `--target-port=80` | The port the **container** listens on. |
| `--type=ClusterIP` | Reachable only from inside the cluster. |

Check Service:

```bash
kubectl get svc nginx
```

Example:

```text
NAME    TYPE        CLUSTER-IP      PORT(S)
nginx   ClusterIP   10.96.x.x      80/TCP
```

### ✅ What you should see

A `CLUSTER-IP` from your Service CIDR (`10.96.x.x`).

---

# 29. Test Service Networking From a Pod

## 🧠 What this step does

Starts a throwaway Pod and uses it to call the Service. This is the **real** proof that Calico eBPF is routing Service traffic **without kube-proxy**.

Create a temporary test Pod:

```bash
kubectl run network-test \
  --image=curlimages/curl \
  --rm -it \
  --restart=Never \
  -- sh
```

| Option | Meaning |
|---|---|
| `kubectl run network-test` | Create a Pod called `network-test`. |
| `--image=curlimages/curl` | A tiny image that contains the `curl` tool. |
| `--rm` | Delete the Pod when you exit. |
| `-it` | Interactive terminal, so you can type into the Pod. |
| `--restart=Never` | Run it once as a plain Pod (not restart it when finished). |
| `-- sh` | Everything after `--` is the command to run inside the Pod: a shell. |

After a few seconds your prompt changes (to something like `~ $`). **You are now inside the Pod.**

Inside:

```sh
curl http://nginx
```

Or:

```sh
curl http://nginx.default.svc.cluster.local
```

💡 **Name explained:** `nginx` = Service name, `default` = namespace, `svc` = it's a Service, `cluster.local` = the cluster's domain. The short name `nginx` works because Pods in the same namespace can skip the suffix.

Expected:

```text
HTML response from nginx
```

### ✅ What you should see

```text
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
```

This verifies Kubernetes Service routing without kube-proxy.

Exit:

```sh
exit
```

### ⚠️ If it doesn't

- `Could not resolve host: nginx` → DNS problem (Sections 31, 58).
- Hangs, then `Connection timed out` → Service routing problem (Section 57).
- `Unable to use a TTY` or the Pod prompt doesn't appear → just wait; if it never does, run `kubectl get pods` to see what state the Pod is in.

---

# 30. Verify Service IP and Endpoints

## 🧠 What this step does

Looks "under the hood". A Service needs **endpoints**: the actual Pod IPs it forwards to. A Service without endpoints is a phone number connected to nobody.

```bash
kubectl get svc nginx
kubectl get endpoints nginx
kubectl get endpointslices
```

| Command | Shows |
|---|---|
| `kubectl get svc nginx` | The Service and its virtual IP. |
| `kubectl get endpoints nginx` | The real Pod IP:port behind it. |
| `kubectl get endpointslices` | The newer, scalable form of the same information. |

> Newer Kubernetes versions may print a warning that `Endpoints` is deprecated in favour of `EndpointSlices`. That's just a notice, not a failure.

Check:

```bash
kubectl describe svc nginx
```

Look for a line like `Endpoints: 192.168.x.x:80`.

The Service must have a backend endpoint.

### ✅ What you should see

The `ENDPOINTS` column shows an address such as `192.168.1.5:80`, which is the nginx Pod's IP.

### ⚠️ If it doesn't

If `ENDPOINTS` is `<none>`, the Service's **selector** doesn't match any Pod labels, or the Pod isn't Ready yet. Check `kubectl get pods --show-labels`.

---

# 31. Verify Kubernetes DNS

## 🧠 What this step does

Tests **CoreDNS**, the cluster's internal phone book. It lets Pods use names like `nginx` instead of memorising IP addresses.

Check CoreDNS:

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

(CoreDNS Pods are labelled `kube-dns` for historical reasons.)

Run:

```bash
kubectl run dns-test \
  --image=busybox:1.36 \
  --rm -it \
  --restart=Never \
  -- nslookup kubernetes.default.svc.cluster.local
```

`nslookup` asks DNS "what is the IP of this name?". `kubernetes.default.svc.cluster.local` is the built-in Service that points to the API server, so it always exists.

⚠️ **Use the full name.** With the `busybox:1.36` image, `nslookup kubernetes.default` (short name) often returns `NXDOMAIN` even though cluster DNS is healthy, because busybox's `nslookup` doesn't apply the cluster search domains. This is a quirk of the test tool, not a cluster fault. If `curl http://nginx` works from a Pod, DNS is fine.

Expected result should resolve the Kubernetes Service.

### ✅ What you should see

```text
Name:      kubernetes.default.svc.cluster.local
Address 1: 10.96.0.1 kubernetes.default.svc.cluster.local
```

(The `10.96.0.1` address is the first address in the Service CIDR; this is normal.)

Then:

```bash
kubectl run dns-test \
  --image=busybox:1.36 \
  --rm -it \
  --restart=Never \
  -- nslookup nginx.default.svc.cluster.local
```

### ✅ What you should see

The `nginx` Service's `10.96.x.x` address.

💡 If you see the message `pod "dns-test" deleted` after the output, that's `--rm` cleaning up. Perfect.

---

# 32. Verify Pod-to-Pod Networking

## 🧠 What this step does

Proves that two Pods can talk to each other **directly by Pod IP**, without going through any Service.

Create two test Pods:

```bash
kubectl run pod-a --image=nginx
kubectl run pod-b --image=nginx
```

Get addresses:

```bash
kubectl get pods -o wide
```

Get Pod IP:

```bash
kubectl get pod pod-b -o wide
```

Find the `IP` column for `pod-b` (e.g. `192.168.1.12`). That is your `<POD_B_IP>`.

Test from pod-a:

```bash
kubectl exec -it pod-a -- \
  curl http://<POD_B_IP>
```

| Part | Meaning |
|---|---|
| `kubectl exec` | Run a command **inside** an existing Pod. |
| `-it pod-a` | Do it interactively in `pod-a`. |
| `-- curl http://<POD_B_IP>` | The command to run inside: fetch pod-b's web page. |

### ✅ What you should see

The nginx "Welcome to nginx!" HTML page.

Delete tests afterward:

```bash
kubectl delete pod pod-a pod-b
```

---

# 33. Verify eBPF on the Host

## 🧠 What this step does

Looks **at the VM itself** to see the eBPF programs and data tables that Calico loaded into the kernel. This is the physical evidence that eBPF is active.

Check BPF filesystem:

```bash
mount | grep bpf
```

Check BPF programs:

```bash
sudo bpftool prog show
```

Check BPF maps:

```bash
sudo bpftool map show
```

| Term | Meaning |
|---|---|
| **BPF program** | A small piece of code running inside the kernel (e.g. "route this packet"). |
| **BPF map** | A data table those programs use (e.g. "Service IP → Pod IP"). |

### ✅ What you should see

- `mount` shows a line like `bpf on /sys/fs/bpf type bpf`.
- `bpftool prog show` lists many programs (many with names containing `cali` or `calico`).
- `bpftool map show` lists maps such as `cali_v4_...`.

The exact number and names of programs/maps depend on the Calico version and active features.

Do not rely on one hard-coded program name as the only validation.

💡 **Tip:** If `bpftool prog show` prints a long list, you can count the lines with `sudo bpftool prog show | wc -l`. If the number is large and there are `cali`-related entries, eBPF is active.

---

# 34. Verify Calico Node Status

## 🧠 What this step does

A health check on Calico itself.

```bash
kubectl get nodes
kubectl get pods -n calico-system -o wide
```

Check:

```bash
kubectl get tigerastatus
```

Inspect:

```bash
kubectl describe tigerastatus calico
```

The Calico status should eventually report healthy/available.

### ✅ What you should see

`AVAILABLE True`, `DEGRADED False`. In the `describe` output, look at the **Conditions** and **Message** fields. They explain any problem in plain words.

---

# 35. Verify NetworkPolicy

## 🧠 What this step does

**NetworkPolicy** is Kubernetes' firewall for Pods: rules like "only the web Pods may talk to the database Pods". In this and the next section you will prove Calico enforces such rules. First we create a working setup with **no** rules (everything allowed), so we know the baseline works.

💡 **Default behaviour:** Kubernetes allows all Pods to talk to all Pods until you add a policy.

Create a test namespace:

```bash
kubectl create namespace network-test
```

A **namespace** is a separate "folder" inside the cluster. A separate one keeps our test tidy and easy to delete.

Create an nginx Pod:

```bash
kubectl run nginx \
  -n network-test \
  --image=nginx
```

Expose:

```bash
kubectl expose pod nginx \
  -n network-test \
  --port=80
```

Run a client:

```bash
kubectl run client \
  -n network-test \
  --image=curlimages/curl \
  --rm -it \
  --restart=Never \
  -- sh
```

Test:

```sh
curl http://nginx
```

Then exit:

```sh
exit
```

This confirms basic connectivity before introducing policy.

### ✅ What you should see

The nginx welcome page.

---

# 36. Test a Calico NetworkPolicy

## 🧠 What this step does

Adds a rule that blocks **all incoming** traffic to the nginx Pod, then repeats the test. This time, the request should **fail**.

## 🎯 Two small corrections for beginners

The original example had two details that commonly trip people up, so this version handles them explicitly:

1. **Labels.** `kubectl run nginx` automatically labels the Pod `run=nginx` (not `app=nginx`). A policy only affects Pods whose labels it matches, so the selector must say `run`.
2. **Which kind of policy.** To keep things simple, the version below is a standard **Kubernetes** NetworkPolicy, which Calico enforces just the same. (Calico-specific `projectcalico.org/v3` policies also exist. On recent Calico versions installed with the native CRDs from Section 21 they can usually be applied with `kubectl` too, but that is not needed for this lab.)

Create a deny policy deliberately:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-nginx
  namespace: network-test
spec:
  podSelector:
    matchLabels:
      run: nginx
  policyTypes:
    - Ingress
```

### Line-by-line explanation

| Line | Meaning |
|---|---|
| `kind: NetworkPolicy` | A firewall rule for Pods. |
| `namespace: network-test` | It only applies in this namespace. |
| `podSelector: matchLabels: run: nginx` | The rule applies to Pods labelled `run=nginx`. |
| `policyTypes: - Ingress` | We are controlling **incoming** traffic. |
| (no `ingress:` section) | An empty allow-list means **nothing** is allowed in, so all incoming traffic is denied. |

Save it as `deny-nginx.yaml` (for example with `nano deny-nginx.yaml`, or `cat > deny-nginx.yaml <<'EOF' ... EOF` as in Section 22).

Apply:

```bash
kubectl apply -f deny-nginx.yaml
```

Test again from the client:

```bash
kubectl run client \
  -n network-test \
  --image=curlimages/curl \
  --rm -it \
  --restart=Never \
  -- curl -sS --max-time 5 http://nginx
```

`--max-time 5` makes curl give up after 5 seconds instead of waiting forever. `-sS` hides the progress bar but **still shows errors**, so you can see the timeout message (with plain `-s` a blocked request prints nothing, which is confusing).

The expected result is that ingress to the selected nginx workload is blocked unless an appropriate allow policy exists.

### ✅ What you should see

```text
curl: (28) Connection timed out after 5001 milliseconds
```

A timeout means the policy **blocked** the traffic. 🎉 That's success.

### ⚠️ If it still returns the nginx page

The policy isn't matching. Check labels with `kubectl get pod nginx -n network-test --show-labels` and make sure the `matchLabels` agree.

> 💡 **Note:** The harmless line `Copying stdin failed ... write on closed stream 0` can appear when using `kubectl run -i`. Ignore it.

---

# 37. Remove the Test Policy

## 🧠 What this step does

Cleans up the policy and the whole test namespace.

```bash
kubectl delete networkpolicy deny-nginx \
  -n network-test
```

Clean test namespace:

```bash
kubectl delete namespace network-test
```

Deleting a namespace deletes **everything inside it**: Pods, Services, policies. It may take a few seconds.

### ✅ What you should see

```text
networkpolicy.networking.k8s.io "deny-nginx" deleted
namespace "network-test" deleted
```

---

# 38. Test NodePort With Calico eBPF

## 🧠 What this step does

A **NodePort** Service opens a port (30000–32767) on the VM itself. Anything that can reach the VM's IP can then reach your app on that port. This tests Calico eBPF's handling of traffic coming **from outside** the cluster.

Create:

```bash
kubectl expose deployment nginx \
  --name=nginx-nodeport \
  --port=80 \
  --target-port=80 \
  --type=NodePort
```

(The `--name` option gives this second Service a different name from the first.)

Get port:

```bash
kubectl get svc nginx-nodeport
```

Example:

```text
80:30xxx/TCP
```

The number after the colon (like `30421`) is your `<NODEPORT>`.

Get node IP:

```bash
kubectl get node -o wide
```

The `INTERNAL-IP` column is your `<NODE_IP>`.

Test from the VM:

```bash
curl http://<NODE_IP>:<NODEPORT>
```

For example: `curl http://192.168.30.100:30421`

⚠️ **Use your own numbers.** Do not paste `<NODE_IP>` or `<NODEPORT>` literally (the shell treats `<` and `>` as redirects and prints `syntax error near unexpected token`), and do not copy the example port. Use the real number from `kubectl get svc nginx-nodeport` (the number after the colon in `80:3xxxx/TCP`). If curl prints nothing, you probably used the wrong port.

Calico eBPF supports Kubernetes service handling without kube-proxy.

### ✅ What you should see

The nginx welcome page.

---

# 39. Verify NodePort From Another Machine

## 🧠 What this step does

Repeats the test from a **different computer** (for example, your laptop), proving external clients can reach your app.

If the VM is reachable from your LAN:

```bash
curl http://<VM_IP>:<NODEPORT>
```

You can also open `http://<VM_IP>:<NODEPORT>` in a web browser.

If this fails, check:

```bash
ip route
sudo ss -lntup
kubectl get svc nginx-nodeport
kubectl get endpoints nginx-nodeport
```

| Check | Why |
|---|---|
| `ip route` | Is the network layout sane? |
| `sudo ss -lntup` | `-u` adds UDP. Note that in eBPF mode a NodePort may **not** appear as a listening socket, because the kernel handles it directly. Do not panic if you don't see it. |
| `get svc` / `get endpoints` | Is there a backend Pod? |

Also verify VM firewall/security-group rules.

If you are on a cloud provider, the NodePort range (`30000–32767`) usually needs to be opened in the cloud "security group" or "firewall rules". Local `ufw` rules also matter.

---

# 40. Clean NodePort Test

```bash
kubectl delete svc nginx-nodeport
```

Removes the extra Service. (The nginx Deployment and the first Service remain until Section 65.)

---

# 41. Check Core Kubernetes Components

## 🧠 What this step does

Lists every system Pod and confirms each expected part is present.

```bash
kubectl get pods -n kube-system -o wide
```

Expected major components include:

```text
coredns
etcd
kube-apiserver
kube-controller-manager
kube-scheduler
```

| Component | Job |
|---|---|
| `coredns` | Internal DNS. |
| `etcd` | The cluster database. |
| `kube-apiserver` | The front door. |
| `kube-controller-manager` | Makes reality match what you asked for (e.g. restarts missing Pods). |
| `kube-scheduler` | Decides which node a new Pod goes on. |

There should be:

```text
NO kube-proxy
```

### ✅ What you should see

All of the above `Running` and `1/1` ready (CoreDNS may show two replicas).

---

# 42. Check All Cluster Resources

## 🧠 What this step does

A big-picture view of everything in the cluster.

```bash
kubectl get all -A
```

Nodes:

```bash
kubectl get nodes -o wide
```

Namespaces:

```bash
kubectl get namespaces
```

CRDs:

```bash
kubectl get crd | grep -i calico
```

Calico:

```bash
kubectl get tigerastatus
```

### ✅ What you should see

Namespaces such as `default`, `kube-system`, `kube-public`, `kube-node-lease`, `tigera-operator`, `calico-system` (and possibly `calico-apiserver`). Scan the `STATUS` columns for anything that is not `Running` or `Completed`.

---

# 43. Check Calico Operator

## 🧠 What this step does

Looks at the Tigera Operator (the "contractor"): is it running, and is it complaining about anything?

```bash
kubectl get deployment -n tigera-operator
```

```bash
kubectl logs \
  -n tigera-operator \
  deployment/tigera-operator \
  --tail=100
```

### ✅ What you should see

`READY 1/1`. Logs are mostly informational. Look for lines containing `error` or `degraded` for clues if something is wrong.

---

# 44. Check Calico Node Logs

## 🧠 What this step does

Reads the logs of the main Calico agent. This is your best window into what Calico is doing.

```bash
kubectl logs \
  -n calico-system \
  -l k8s-app=calico-node \
  --tail=200
```

If multiple containers exist:

```bash
kubectl get pods -n calico-system
```

Then:

```bash
kubectl describe pod -n calico-system <CALICO_NODE_POD>
```

Replace `<CALICO_NODE_POD>` with the exact Pod name from the list (for example `calico-node-abcde`). `describe` also shows **Events** at the bottom: a timeline of what Kubernetes did (and any errors).

---

# 45. Check Felix Configuration

## 🧠 What this step does

Shows Felix's settings. *Felix* is the part of Calico that programs your dataplane.

```bash
kubectl get felixconfiguration default -o yaml
```

For eBPF mode, inspect:

```bash
kubectl get felixconfiguration default -o yaml | grep -i bpf
```

### ✅ What you should see

Lines such as `bpfEnabled: true`. Exact fields vary by version.

> If `felixconfiguration` isn't recognised by `kubectl`, the Calico CRDs from Section 21 were not installed correctly.

---

# 46. Check Calico Installation Configuration

## 🧠 What this step does

Re-reads the "plan" you gave the operator, to confirm it's the one you meant.

```bash
kubectl get installation default -o yaml
```

Confirm the intended dataplane:

```yaml
linuxDataplane: BPF
```

Also confirm:

```yaml
bpfNetworkBootstrap: Disabled
kubeProxyManagement: Disabled
```

---

# 47. Verify the Kubernetes API Server

## 🧠 What this step does

Asks the API server if it's healthy.

```bash
kubectl cluster-info
```

```bash
kubectl get --raw='/readyz?verbose'
```

`--raw` calls an API URL directly. `/readyz` is the "am I ready?" health endpoint, and `?verbose` lists every individual check.

Expected:

```text
ok
```

### ✅ What you should see

A list of lines such as `[+]ping ok`, `[+]etcd ok` and finally `readyz check passed`. A `[+]` means passing, and a `[-]` means failing.

Check API port:

```bash
sudo ss -lntp | grep 6443
```

---

# 48. Verify etcd

## 🧠 What this step does

etcd is the cluster's **database**. If etcd is unhealthy, nothing in the cluster works reliably.

Check:

```bash
kubectl -n kube-system get pods -l component=etcd
```

Describe:

```bash
kubectl -n kube-system describe pod \
  -l component=etcd
```

### ✅ What you should see

`1/1 Running`, and in `describe` a `Ready: True` condition.

Do not expose etcd publicly.

🔒 etcd holds **all** cluster data, including secrets. Never open its ports (`2379`, `2380`) to the internet.

---

# 49. Verify kubelet

## 🧠 What this step does

Checks the node agent: is it running, and what does it log?

```bash
sudo systemctl status kubelet --no-pager
```

Logs:

```bash
sudo journalctl -u kubelet -n 200 --no-pager
```

| Part | Meaning |
|---|---|
| `journalctl` | Reads system logs. |
| `-u kubelet` | Only logs from the kubelet service. |
| `-n 200` | The last 200 lines. |

Follow:

```bash
sudo journalctl -u kubelet -f
```

`-f` ("follow") shows new lines live. Press **Ctrl+C** to stop.

### ✅ What you should see

`active (running)` in the status. Occasional warnings are fine. Repeated errors about `CNI`, `cgroup`, or `certificate` need attention.

---

# 50. Verify containerd

## 🧠 What this step does

The same health check for the container runtime.

```bash
sudo systemctl status containerd --no-pager
```

Logs:

```bash
sudo journalctl -u containerd -n 200 --no-pager
```

### ✅ What you should see

`active (running)` and no repeating error lines.

---

# 51. Optional: Metrics Server

## 🧠 What this step does

**Metrics Server** collects CPU/memory usage so that `kubectl top` works. It is **optional**. Skip it unless you want those numbers.

Only install after the core cluster and networking are healthy.

Verify whether already installed:

```bash
kubectl get deployment -n kube-system metrics-server
```

Then test:

```bash
kubectl top nodes
```

If Metrics Server is installed:

```bash
kubectl top pods -A
```

Do not use Metrics Server as proof that Calico networking works.

💡 On a kubeadm lab, Metrics Server often needs the extra flag `--kubelet-insecure-tls` because the kubelet uses a self-signed certificate. Follow the Metrics Server project's instructions when you install it.

---

# 52. Optional: Helm

## 🧠 What this step does

**Helm** is a "package manager for Kubernetes". It installs complete applications with one command. Optional now, and useful later.

Install Helm only if later components require it.

Verify:

```bash
helm version
```

`command not found` just means Helm isn't installed. That's fine for now.

---

# 53. Optional: Ingress

## 🧠 What this step does

An **Ingress controller** lets you expose many web applications through a single entry point using hostnames and URL paths (like a receptionist routing visitors to the right office).

After the base cluster works:

```text
Kubernetes
    |
    +-- Calico CNI
    +-- Calico eBPF
    +-- kube-proxy disabled
    |
    +-- Ingress Controller
```

Install an ingress controller separately.

Do not troubleshoot ingress until:

```text
Node Ready
Calico healthy
Pod-to-Pod works
Service ClusterIP works
DNS works
NodePort works
```

🎯 **Why this order?** Ingress sits on top of everything else. If a lower layer is broken, ingress will also appear broken, and you will waste time debugging the wrong thing.

---

# 54. Troubleshooting: Node NotReady

## 🧠 When to use this

`kubectl get nodes` shows `NotReady` for more than about 10 minutes after Calico was installed.

## 💡 Troubleshooting mindset for beginners

Work **from the bottom up**: machine → runtime → kubelet → network plugin (Calico) → applications. A problem at a lower layer causes symptoms in every layer above it. Always read the **error message**; it usually names the cause.

Start with:

```bash
kubectl get nodes -o wide
kubectl describe node <NODE>
```

Replace `<NODE>` with your node name (e.g. `k8s-single`).

Check conditions:

```bash
kubectl describe node <NODE> | sed -n '/Conditions:/,/Addresses:/p'
```

This prints only the **Conditions** section. Look at the `Ready` row's `Message`. A message like `container runtime network not ready: NetworkReady=false ... cni plugin not initialized` means Calico hasn't finished starting.

Check Calico:

```bash
kubectl get pods -n calico-system -o wide
```

Check:

```bash
kubectl get tigerastatus
```

Check kubelet:

```bash
sudo journalctl -u kubelet -n 200 --no-pager
```

### Common causes

| Symptom | Likely cause |
|---|---|
| `cni plugin not initialized` | Calico is still starting, or failed. Check Calico Pods. |
| Calico Pods `ImagePullBackOff` | Internet/DNS problem on the VM. |
| Calico Pods `CrashLoopBackOff` | Kernel/eBPF problem or API-server connectivity (Sections 60 and 62). |
| `PLEG is not healthy` or runtime errors in kubelet logs | containerd problem (Section 59). |

---

# 55. Troubleshooting: Calico Pods Not Running

## 🧠 When to use this

Pods in `calico-system` show `Pending`, `CrashLoopBackOff`, `Error` or `ImagePullBackOff`.

```bash
kubectl get pods -n calico-system
```

Then:

```bash
kubectl describe pod \
  -n calico-system \
  <POD_NAME>
```

Scroll to the **Events** section at the bottom. It's a timeline that usually says exactly what went wrong.

Logs:

```bash
kubectl logs \
  -n calico-system \
  <POD_NAME> \
  --all-containers \
  --tail=200
```

`--all-containers` includes every container in the Pod (some Pods have several).

If a Pod keeps restarting, add `--previous` to see the logs from just before it crashed.

Check operator:

```bash
kubectl logs \
  -n tigera-operator \
  deployment/tigera-operator \
  --tail=200
```

### Status guide

| Status | Meaning | First thing to check |
|---|---|---|
| `Pending` | Not scheduled onto a node. | Did you remove the control-plane taint (Section 20)? Are resources sufficient? |
| `ContainerCreating` | Starting; image downloading. | Wait a minute or two; then check internet. |
| `ImagePullBackOff` | Can't download the image. | DNS/internet/proxy. |
| `CrashLoopBackOff` | Starts, crashes, repeats. | Read the logs. |

### Known messages from `kubectl get tigerastatus` / `describe tigerastatus`

| Message | Cause | Fix |
|---|---|---|
| `bpfNetworkBootstrap is Enabled but the requirements are not met: kubernetes service endpoint is defined by the ... ConfigMap` | Automatic bootstrap and the manual ConfigMap are both set. | Set `bpfNetworkBootstrap: Disabled`, re-apply the Installation. |
| `kubeproxy-monitor ... failed to retrieve kube-proxy DaemonSet: DaemonSet.apps "kube-proxy" not found` | The operator is told to manage a kube-proxy that was never installed. | Set `kubeProxyManagement: Disabled`, re-apply. |
| `calico-system` namespace is empty and `calico` is Degraded | The operator is blocked by one of the two errors above. | Fix the settings; Pods appear within a few minutes. |

---

# 56. Troubleshooting: kube-proxy Accidentally Exists

## 🧠 When to use this

In Section 19 or 27 you found a kube-proxy DaemonSet or Pod.

Check:

```bash
kubectl get daemonset -A | grep kube-proxy
```

If kube-proxy exists unexpectedly, stop and investigate why it was created.

Most often the cause is simply forgetting `--skip-phases=addon/kube-proxy` during `kubeadm init`.

For a fresh cluster, the preferred approach is:

```bash
kubeadm init --skip-phases=addon/kube-proxy ...
```

(The `...` stands for your other options from Section 17.)

Do not simply delete a kube-proxy Pod repeatedly without determining who owns/recreates it.

💡 **Why deleting the Pod doesn't work:** A DaemonSet keeps recreating its Pods. It's like a door that keeps reopening itself. You'd have to remove the DaemonSet (the "owner") instead. In a brand-new lab cluster, the simplest and cleanest fix is to rebuild with the correct flag (Section 64 explains the reset). Removing kube-proxy from an existing cluster has additional steps; follow Calico's official eBPF migration documentation in Section 71.

---

# 57. Troubleshooting: Service Does Not Work

## 🧠 When to use this

Calling a Service by name or IP times out or fails.

## 💡 The Service checklist

A Service can fail for four reasons: (1) there's no Pod behind it, (2) the Pod isn't healthy, (3) the Service's selector doesn't match the Pod's labels, or (4) the dataplane (Calico eBPF) isn't working. Check them in that order.

Check Service:

```bash
kubectl get svc
```

Check endpoints:

```bash
kubectl get endpoints
kubectl get endpointslices
```

`<none>` under `ENDPOINTS` means reasons 1–3 (nothing behind the Service).

Check Pods:

```bash
kubectl get pods -o wide
```

Are they `Running` and `1/1`?

Check Calico eBPF:

```bash
kubectl get installation default -o yaml
kubectl get felixconfiguration default -o yaml
```

Check host BPF:

```bash
sudo bpftool prog show
sudo bpftool map show
```

If endpoints exist and Pods are healthy, but the Service still fails, look at the Calico logs (Section 44).

---

# 58. Troubleshooting: DNS Does Not Work

## 🧠 When to use this

Pods can reach IPs but not names (e.g. `curl http://nginx` says `Could not resolve host`).

Check CoreDNS:

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

Logs:

```bash
kubectl logs -n kube-system \
  -l k8s-app=kube-dns \
  --tail=200
```

Check DNS Service:

```bash
kubectl get svc -n kube-system kube-dns
```

It should have a `CLUSTER-IP` of `10.96.0.10` (with the default Service CIDR).

Test:

```bash
kubectl run dns-test \
  --image=busybox:1.36 \
  --rm -it \
  --restart=Never \
  -- nslookup kubernetes.default.svc.cluster.local
```

### Common causes

| Symptom | Likely cause |
|---|---|
| CoreDNS `Pending` | Node not Ready, or the control-plane taint is still present. |
| CoreDNS `Running` but lookups time out | Pod-to-Service routing issue, so see Section 57. |
| Cluster names work but `google.com` doesn't | The VM's own DNS (Section 2.2). |

---

# 59. Troubleshooting: containerd

## 🧠 When to use this

Pods are stuck in `ContainerCreating`, kubelet logs mention the runtime, or `kubeadm init` complained about CRI.

Check:

```bash
sudo systemctl status containerd
```

Check CRI:

```bash
sudo ctr plugins ls | grep cri
```

Check configuration:

```bash
grep -n "SystemdCgroup" /etc/containerd/config.toml
```

Expected:

```text
SystemdCgroup = true
```

Restart:

```bash
sudo systemctl restart containerd
sudo systemctl restart kubelet
```

Restart containerd first, then kubelet, because kubelet depends on the runtime.

---

# 60. Troubleshooting: Calico API Server Connectivity

## 🧠 When to use this

Calico Pods start but cannot reach the Kubernetes API server (logs contain `connection refused`, `i/o timeout` or mention `10.96.0.1`).

In eBPF mode Calico must have a direct, stable way to reach the Kubernetes API server.

💡 **Why:** Normally the API server is reached through the Service address `10.96.0.1`, which depends on kube-proxy. We removed kube-proxy and Calico is the replacement, so Calico needs the **real** address (node IP + port 6443) to avoid a chicken-and-egg problem (see Section 23).

For a single control-plane node, use the VM's stable node IP rather than an address that can change.

Record:

```bash
kubectl get nodes -o wide
```

The Kubernetes API server normally listens on:

```text
6443
```

Verify:

```bash
sudo ss -lntp | grep 6443
```

### What to do

- Confirm the API server is running (Section 47).
- Confirm the VM's IP hasn't changed since `kubeadm init` (compare `hostname -I` with the address in `kubectl cluster-info`).
- Confirm the `kubernetes-services-endpoint` ConfigMap exists in **both** needed places: `kubectl get configmap kubernetes-services-endpoint -n tigera-operator -o yaml` (Step 21.1). The Tigera Operator copies it for the Calico Pods. The host must be your node IP and the port `6443`.
- Confirm the Installation has `bpfNetworkBootstrap: Disabled` and `kubeProxyManagement: Disabled` (Section 46). Using the ConfigMap **and** `bpfNetworkBootstrap: Enabled` together makes Calico report `DEGRADED`.
- If the operator itself crashes with `10.96.0.1:443 i/o timeout`, Step 21.1 was skipped or the operator Pod was not restarted.

---

# 61. Troubleshooting: VXLAN

## 🧠 What this section is about

**VXLAN** wraps Pod traffic so that it can cross the real network between nodes. It matters when you have **more than one node**.

Calico eBPF can use VXLAN for relevant traffic.

If the cluster later grows beyond one node, verify the underlying network permits the required VXLAN traffic.

(VXLAN uses **UDP port 4789**. Firewalls and cloud security groups between your nodes must allow it.)

Inspect:

```bash
ip link
ip -d link show
```

`-d` shows extra "details", such as the interface type.

Look for Calico-related interfaces.

You may see interfaces named `vxlan.calico` and `cali...` (one per Pod). In eBPF mode you may also see `bpfin.cali` and `bpfout.cali`.

For a one-node cluster, cross-node VXLAN traffic is not exercised because there is only one node.

---

# 62. Troubleshooting: BPF

## 🧠 When to use this

Calico logs say BPF can't be enabled, programs fail to load, or the dataplane seems to be falling back.

Check:

```bash
mount | grep /sys/fs/bpf
```

If nothing prints, the BPF filesystem is not mounted. Calico normally mounts it itself, but you can do it manually: `sudo mount -t bpf bpf /sys/fs/bpf`.

Check kernel:

```bash
uname -r
```

Compare it with the minimum kernel in the Calico eBPF documentation.

Check BPF:

```bash
sudo bpftool feature probe
```

This asks the kernel "which BPF features do you support?" and prints a long list. Look for `eBPF program_type ... is available` lines.

Check programs:

```bash
sudo bpftool prog show
```

Check maps:

```bash
sudo bpftool map show
```

If BPF support is missing, verify the VM kernel and virtualization environment before changing Calico configuration.

💡 **Why the virtualization hint?** Some cloud images or minimal kernels are built without BPF features. Some hypervisors also run special lightweight kernels. Installing a standard Ubuntu kernel (for example `linux-generic`) and rebooting often solves it.

---

# 63. Troubleshooting: VM Network

## 🧠 When to use this

General connectivity problems: downloads fail, DNS fails, or Pods behave strangely.

Check:

```bash
ip -br addr
ip route
ip link
```

Check DNS:

```bash
resolvectl status
```

Check internet:

```bash
curl -I https://registry-1.docker.io
curl -I https://k8s.io
```

(`registry-1.docker.io` is where many container images, including nginx, are downloaded from. A `401 Unauthorized` reply from it is normal and means the server is reachable.)

Check MTU:

```bash
ip link
```

If networking behaves strangely, compare the VM interface MTU with the surrounding network.

💡 **What's MTU?** The **Maximum Transmission Unit** is the largest packet your network will carry (usually `1500` bytes). VXLAN adds about 50 bytes of wrapping, so if the underlying network has a small MTU, large packets can silently disappear. Symptom: small requests work (like `ping`), big ones (large downloads) hang.

---

# 64. Cluster Reset

## 🧠 What this step does

**Wipes the Kubernetes setup** on this VM so that you can start again from `kubeadm init`.

> ⚠️ **This destroys the cluster.** All Pods, Services, data and settings stored in the cluster are removed. Use it only when intentionally rebuilding.

Use this only when intentionally rebuilding the cluster.

```bash
sudo kubeadm reset -f
```

`reset` undoes what `kubeadm init` did; `-f` skips the confirmation question.

Remove Kubernetes configuration:

```bash
rm -rf ~/.kube
```

Deletes your local kubectl config. (`rm -rf` permanently deletes, so be careful to type the path exactly.)

If you are rebuilding Calico as well, remove the relevant Calico resources/operator according to the Calico cleanup procedure for the installed version.

When the whole cluster is being rebuilt, `kubeadm reset` already removes the control plane, so the Calico objects stored in it disappear too. However, **leftover network state on the VM** (interfaces, BPF programs, CNI config in `/etc/cni/net.d`) may remain. A reboot (below) clears most of it. You may also remove the CNI config manually: `sudo rm -rf /etc/cni/net.d`.

Restart:

```bash
sudo systemctl restart containerd
sudo systemctl restart kubelet
```

Reboot if the networking state requires a clean reset:

```bash
sudo reboot
```

### ✅ After the reset

You are back to the state just **before** Section 17. Go to Section 15 (pre-flight checks), then run `kubeadm init` again.

---

# 65. Clean Test Workloads

## 🧠 What this step does

Removes the test applications you created so the cluster is tidy.

Delete test resources:

```bash
kubectl delete deployment nginx --ignore-not-found
kubectl delete service nginx --ignore-not-found
kubectl delete service nginx-nodeport --ignore-not-found
```

`--ignore-not-found` means "don't complain if it's already gone".

Verify:

```bash
kubectl get all -A
```

### ✅ What you should see

No `nginx` entries in the `default` namespace. Only system components remain.

---

# 66. Final Validation Checklist

## 🧠 What this section is

Your **final exam**. Tick each box. If something isn't ticked, revisit the section shown in brackets.

## VM

```text
[ ] VM has sufficient CPU                (Section 1.1)
[ ] VM has sufficient RAM                (Section 1.1)
[ ] Disk has sufficient space            (Section 1.1)
[ ] Static/stable IP                     (Section 1.5)
[ ] Correct hostname                     (Section 1.4)
[ ] Correct DNS                          (Section 2.2)
[ ] Internet connectivity                (Section 2.3)
[ ] Correct kernel                       (Section 1.2)
```

## OS

```text
[ ] Swap disabled                        (Section 5)
[ ] overlay loaded                       (Section 6)
[ ] br_netfilter loaded                  (Section 6)
[ ] IPv4 forwarding enabled              (Section 7)
[ ] Firewall reviewed                    (Section 9)
[ ] Required network connectivity verified (Section 2)
```

## Runtime

```text
[ ] containerd installed                 (Section 10)
[ ] containerd enabled                   (Section 11)
[ ] containerd running                   (Section 11)
[ ] CRI available                        (Section 12)
[ ] SystemdCgroup=true                   (Section 11)
```

## Kubernetes

```text
[ ] kubeadm installed                    (Section 13)
[ ] kubelet installed                    (Section 13)
[ ] kubectl installed                    (Section 13)
[ ] Kubernetes versions verified         (Section 13)
[ ] kubeadm init completed               (Section 17)
[ ] kubectl admin config works           (Section 18)
[ ] API server healthy                   (Section 47)
[ ] etcd healthy                         (Section 48)
[ ] scheduler healthy                    (Section 41)
[ ] controller-manager healthy           (Section 41)
```

## kube-proxy

```text
[ ] kubeadm initialized with --skip-phases=addon/kube-proxy   (Section 17)
[ ] kube-proxy DaemonSet absent          (Sections 19, 27)
[ ] kube-proxy process absent            (Section 27)
```

## Calico

```text
[ ] Tigera Operator running (no crash)   (Section 21)
[ ] kubernetes-services-endpoint ConfigMap created   (Section 21.1)
[ ] Calico CRDs installed                (Section 21)
[ ] Installation resource healthy        (Section 46)
[ ] linuxDataplane=BPF                   (Section 46)
[ ] bpfNetworkBootstrap=Disabled         (Section 46)
[ ] kubeProxyManagement=Disabled         (Section 46)
[ ] Calico node running                  (Section 24)
[ ] Calico status healthy                (Section 34)
```

## Networking

```text
[ ] Node Ready                           (Section 25)
[ ] Pod-to-Pod connectivity works        (Section 32)
[ ] ClusterIP Service works              (Section 29)
[ ] Service DNS works                    (Section 31)
[ ] CoreDNS works                        (Section 31)
[ ] NodePort works                       (Sections 38–39)
[ ] Calico eBPF programs present         (Section 33)
[ ] BPF maps present                     (Section 33)
```

## Policy

```text
[ ] Calico NetworkPolicy tested          (Section 36)
[ ] Allow/Deny behavior verified         (Section 36)
```

---

# 67. Recommended Installation Order

## 🧠 What this section is

A one-page **map** of the whole journey. If you get lost, come back here.

Follow this order and do not skip validation checkpoints:

```text
01. Verify VM
       |
       v
02. Verify OS + kernel
       |
       v
03. Verify stable IP + DNS
       |
       v
04. Disable swap
       |
       v
05. Configure kernel modules
       |
       v
06. Configure sysctl
       |
       v
07. Verify firewall/network
       |
       v
08. Install containerd
       |
       v
09. Configure SystemdCgroup
       |
       v
10. Verify CRI
       |
       v
11. Install kubeadm/kubelet/kubectl
       |
       v
12. Final preflight verification
       |
       v
13. kubeadm init
       |       \
       |        --skip-phases=addon/kube-proxy
       v
14. Configure kubectl
       |
       v
15. Verify kube-proxy is absent
       |
       v
16. Remove control-plane taint
       |
       v
17. Install Tigera Operator
       +-- create kubernetes-services-endpoint ConfigMap (REQUIRED)
       |
       v
18. Configure Calico
       |
       +-- linuxDataplane=BPF
       +-- bpfNetworkBootstrap=Disabled
       +-- kubeProxyManagement=Disabled
       |
       v
19. Wait for Calico
       |
       v
20. Verify Node Ready
       |
       v
21. Verify kube-proxy absent
       |
       v
22. Test Pod-to-Pod
       |
       v
23. Test ClusterIP
       |
       v
24. Test DNS
       |
       v
25. Test NodePort
       |
       v
26. Verify BPF
       |
       v
27. Test NetworkPolicy
       |
       v
28. Final cluster validation
```

> Note: the numbers in this flowchart are **stages of the journey**, not section numbers of this document. The mapping is: stages 1–3 → Sections 1–3; stage 4 → Section 5; stages 5–6 → Sections 6–7; stage 7 → Sections 8–9; stages 8–10 → Sections 10–12; stage 11 → Sections 13–14; stage 12 → Section 15; stage 13 → Sections 16–17; stage 14 → Section 18; stage 15 → Section 19; stage 16 → Section 20; stages 17–19 → Sections 21–24; stage 20 → Section 25; stage 21 → Section 27; stages 22–25 → Sections 28–32 and 38–39; stage 26 → Section 33; stage 27 → Sections 35–37; stage 28 → Section 66.

---

# 68. Important Architecture Note

## 🧠 What this section tells you

Be clear about what you have built, and what you have **not**.

This is intentionally a **single-node learning/self-hosted cluster**.

It is not HA.

There is:

```text
1 VM
1 control plane
1 etcd
1 kubelet
1 Calico node
1 worker capacity
```

If the VM goes down, the entire Kubernetes cluster goes down.

💡 **HA** (High Availability) means "no single point of failure". Here there are many single points of failure: the VM itself, the one etcd copy, the one control plane. That is a fine trade-off for learning but not suitable for anything important.

🔒 **Practical advice:** Take a **VM snapshot** in your hypervisor once the cluster is healthy (after Section 66). If you break something while experimenting, you can roll back in seconds instead of rebuilding.

For learning Calico eBPF and kube-proxy replacement, however, this is a useful minimal environment.

---

# 69. Expansion Path

## 🧠 What this section is

A look at what changes **if** you later grow to several machines. Nothing here is required now.

If later moving to multiple VMs:

```text
                  Load Balancer
                       |
                Kubernetes API
                       |
        +--------------+--------------+
        |              |              |
   control-plane-1 control-plane-2 control-plane-3
        |
   +----+---------+----------+
   |              |          |
 worker-1       worker-2   worker-3
```

At that point, revisit:

| Item | Why it matters later |
|---|---|
| `[ ] API server endpoint` | Nodes need one stable address to reach the API, which today is just the VM's IP. |
| `[ ] kubeadm controlPlaneEndpoint` | The kubeadm setting that holds that stable address. It must be chosen at `kubeadm init` time for an HA control plane. |
| `[ ] etcd HA` | Multiple etcd copies (usually 3) so one can fail. |
| `[ ] Calico node-to-node networking` | Nodes must reach each other for Pod traffic. |
| `[ ] VXLAN` | UDP 4789 must be open between nodes. |
| `[ ] firewall` | Open the required inter-node ports. |
| `[ ] BGP if selected` | An alternative to VXLAN for advanced networks. |
| `[ ] NodePort` | Think about which nodes receive external traffic. |
| `[ ] load balancer` | Spreads traffic across nodes. |
| `[ ] DNS` | Friendly names for the API/load balancer. |
| `[ ] storage` | Shared or replicated storage for stateful apps. |
| `[ ] backup` | Back up etcd and your manifests. |

The single-node installation should not be treated as an HA design.

---

# 70. Reference Commands

## 🧠 What this section is

A **cheat sheet** of the most useful commands from this guide, to keep handy for daily use.

## Cluster

```bash
kubectl get nodes -o wide              # Is my node Ready? What are its IPs?
kubectl get pods -A -o wide            # All Pods in all namespaces
kubectl get svc -A                     # All Services
kubectl get endpoints -A               # What Pods sit behind each Service
kubectl get endpointslices -A          # Same, newer format
kubectl cluster-info                   # Where is the API server?
kubectl get --raw='/readyz?verbose'    # Detailed API server health check
```

## Calico

```bash
kubectl get tigerastatus                           # Is Calico healthy?
kubectl get installation default -o yaml           # What I told the operator to install
kubectl get felixconfiguration default -o yaml     # The Calico agent's settings
kubectl get pods -n calico-system -o wide          # Calico's Pods
kubectl get pods -n tigera-operator                # The operator's Pod
```

## kube-proxy

```bash
kubectl get daemonset -A | grep kube-proxy   # Should print nothing
kubectl get pods -A | grep kube-proxy        # Should print nothing
ps aux | grep '[k]ube-proxy'                 # Should print nothing
```

Expected: no active kube-proxy.

## Host

```bash
uname -r                                  # Kernel version
ip -br addr                               # IP addresses
ip route                                  # Routing table
free -h                                   # Memory
swapon --show                             # Should print nothing
lsmod | grep -E 'overlay|br_netfilter'    # Both modules loaded?
sysctl net.ipv4.ip_forward                # Should be 1
```

## Runtime

```bash
containerd --version                      # Version
sudo systemctl status containerd          # Is it running?
sudo ctr plugins ls | grep cri            # Is CRI "ok"?
```

## eBPF

```bash
mount | grep /sys/fs/bpf                  # Is the BPF filesystem mounted?
sudo bpftool prog show                    # Loaded BPF programs
sudo bpftool map show                     # BPF data tables
```

---

# 71. Sources / Version Notes

## 🧠 What this section is

Where the instructions come from, and where to look when versions change.

This runbook follows the current Calico documentation approach for self-managed/on-premises Kubernetes:

- Calico Open Source current documentation: v3.33
- Tigera Operator recommended for new installations
- Calico eBPF dataplane
- Calico eBPF can provide Kubernetes Service networking without kube-proxy
- kubeadm can skip installation of the kube-proxy addon using:

```bash
kubeadm init --skip-phases=addon/kube-proxy
```

- Calico eBPF requires a supported Linux kernel/OS environment.
- For a new self-managed kubeadm cluster, configure Calico eBPF from the beginning rather than first building a kube-proxy cluster and migrating it later.

⚠️ **Always check before you start:** Kubernetes and Calico release new versions frequently. Before beginning, open the pages below and confirm (1) which Kubernetes minor versions are supported, (2) which Calico version matches, and (3) the kernel requirement for eBPF.

Official references:

- Calico on-premises installation:
  https://docs.tigera.io/calico/latest/getting-started/kubernetes/self-managed-onprem/onpremises
- Calico eBPF installation:
  https://docs.tigera.io/calico/latest/operations/ebpf/install
- Calico eBPF configuration:
  https://docs.tigera.io/calico/latest/operations/ebpf/enabling-ebpf
- Calico Installation API:
  https://docs.tigera.io/calico/latest/reference/installation/api
- Kubernetes kubeadm installation:
  https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/

---

# 72. End State

## 🧠 What this section is

A picture of the **finished** cluster, and the few commands that prove it.

The final cluster should satisfy all of the following:

```text
                         Kubernetes
                              |
                    +---------+---------+
                    |                   |
              Control Plane          Worker
                    |                   |
                    +---------+---------+
                              |
                         Same VM
                              |
                    +---------+---------+
                    |                   |
                 Calico              kubelet
                    |
              eBPF dataplane
                    |
             Service networking
                    |
             kube-proxy DISABLED
```

Validation:

```bash
kubectl get nodes
kubectl get pods -A
kubectl get tigerastatus
kubectl get installation default -o yaml
kubectl get daemonset -A | grep kube-proxy
sudo bpftool prog show
```

The most important final properties are:

```text
Node                  = Ready
Calico                = Healthy
Calico dataplane      = BPF
kube-proxy            = Not running
Pod networking        = Working
ClusterIP networking  = Working
DNS                   = Working
NodePort              = Working
NetworkPolicy         = Working
```

## 🎉 Congratulations

If every line above is true, you have built a real Kubernetes cluster **from scratch**, with a modern eBPF networking dataplane and no kube-proxy. Good next steps:

1. **Snapshot the VM** so you can always return to this working state.
2. **Deploy something of your own** (a small web app with a Deployment + Service).
3. **Experiment with NetworkPolicy**: write an "allow" rule so only certain Pods can reach nginx.
4. **Install an Ingress controller** (Section 53).
5. **Read the Calico eBPF docs** (Section 71) to see what else the eBPF dataplane offers.

---

# Appendix A: What Changed From the Original Runbook

This edition keeps the original structure and section numbers. Most changes are added explanations. These **technical fixes** were made so that beginners don't hit avoidable errors. Items marked ✅ were **confirmed on a real install** (Ubuntu 24.04, VirtualBox, Kubernetes v1.36.5, Calico v3.33.0).

| Where | Change | Reason |
|---|---|---|
| Section 1.5b / 1.5c | Added disk-extension (LVM) and static-IP (netplan) steps. ✅ | The Ubuntu installer used only half the disk, and DHCP addresses can change and break the cluster. |
| Section 13 | Examples now use Kubernetes v1.36. ✅ | This is the version the guide was tested with. |
| Section 16 | Added a warning about the example VM IP overlapping `192.168.0.0/16`. | The original example IP (`192.168.30.100`) falls inside the example Pod CIDR. |
| Section 17 | Added `--apiserver-advertise-address=<NODE_IP>`. ✅ | Pins the API server to the static IP that Calico eBPF will use. |
| **Section 21.1 (new)** | Added the `kubernetes-services-endpoint` ConfigMap and an operator restart. ✅ | **Without it the Tigera Operator crashes** (`10.96.0.1:443 i/o timeout`), because the Service IP needs kube-proxy. |
| **Sections 22, 23, 46, 60, 66, 67** | `bpfNetworkBootstrap` and `kubeProxyManagement` changed from `Enabled` to `Disabled`, with new explanation. ✅ | With the ConfigMap and no kube-proxy, `Enabled` makes Calico report `DEGRADED` (and Calico Pods are never created). |
| Section 22 | Added `ipPools` (cidr + `encapsulation: VXLAN`). | Keeps the Calico Pod range in sync with `kubeadm --pod-network-cidr`. |
| Section 31 and 58 | DNS test uses the full name `kubernetes.default.svc.cluster.local`. ✅ | `busybox:1.36` returns `NXDOMAIN` for the short name even when DNS works. |
| Section 36 | Standard Kubernetes NetworkPolicy, label `run: nginx`, and `curl -sS`. ✅ | `kubectl run nginx` labels the Pod `run=nginx` (not `app=nginx`), and `-s` hides the timeout message. |
| Section 38 | Warning to use real IP/port, never `<PLACEHOLDERS>`. ✅ | Pasting placeholders causes a shell syntax error; a wrong port prints nothing. |
| Section 55 | Table of known `tigerastatus` messages. ✅ | The two degraded messages above are not obvious to beginners. |

Remember to verify Kubernetes and Calico versions against the official docs before you begin.

---

# Appendix B: Problems We Hit During a Real Install, and How They Were Fixed

| # | Problem | Symptom | Cause | Fix |
|---|---|---|---|---|
| 1 | Tigera Operator crash loop | `CrashLoopBackOff`; log shows `dial tcp 10.96.0.1:443: i/o timeout` | The Service IP needs kube-proxy, which was skipped on purpose. | Step 21.1: ConfigMap with the real API server IP, then restart the operator. |
| 2 | Calico `DEGRADED` | `bpfNetworkBootstrap is Enabled but the requirements are not met ...` | Automatic bootstrap conflicts with the manual ConfigMap. | `bpfNetworkBootstrap: Disabled`. |
| 3 | `kubeproxy-monitor` `DEGRADED` | `DaemonSet.apps "kube-proxy" not found` | Operator told to manage a kube-proxy that does not exist. | `kubeProxyManagement: Disabled`. |
| 4 | Disk smaller than expected | 50 GB disk, `/` only 24 GB | Installer LVM default | `lvextend -r -l +100%FREE` (Section 1.5b). |
| 5 | DHCP address | `ip route` shows `proto dhcp` | Address could change and break the cluster | Static IP via netplan (Section 1.5c). |
| 6 | Swap enabled | 4 GB `/swap.img` | kubelet refuses to run with swap | `swapoff -a` and comment the line in `/etc/fstab` (Section 5). |
| 7 | `NXDOMAIN` in DNS test | `nslookup kubernetes.default` fails | busybox short-name quirk | Use the full name. |
| 8 | Shell `syntax error near unexpected token '|'` | Literal `<NODEPORT>` pasted | `<` and `>` are shell redirects | Replace placeholders with real values. |
| 9 | NodePort curl printed nothing | Wrong port (copied the example) | Used an example number | Use the port from `kubectl get svc`. |
| 10 | Blocked request looked like "no output" | `curl -s` hides errors | Silent mode | Use `curl -sS` to see `Connection timed out`. |

### Key lessons

1. When kube-proxy is skipped, the operator needs the `kubernetes-services-endpoint` ConfigMap **before** it can start.
2. With that ConfigMap, keep `bpfNetworkBootstrap` and `kubeProxyManagement` set to `Disabled`.
3. Check disk size, IP stability and swap **before** you start.
4. Replace every `<PLACEHOLDER>` with a real value before running a command.
