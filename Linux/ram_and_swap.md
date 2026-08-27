# Linux Essentials: RAM & Swap

A practical reference guide to RAM (physical memory) and Swap (virtual memory) in Linux — how they work, how to check them, and how to manage swap.

---

## Table of Contents
1. [RAM vs Swap — The Basics](#1-ram-vs-swap--the-basics)
2. [Checking Memory Usage](#2-checking-memory-usage)
3. [Understanding `free -h` Output](#3-understanding-free--h-output)
4. [What is Swappiness?](#4-what-is-swappiness)
5. [Creating & Managing a Swap File](#5-creating--managing-a-swap-file)
6. [Creating & Managing a Swap Partition](#6-creating--managing-a-swap-partition)
7. [Enabling Swap Permanently (fstab)](#7-enabling-swap-permanently-fstab)
8. [Monitoring & Troubleshooting](#8-monitoring--troubleshooting)

---

## 1. RAM vs Swap — The Basics

| | RAM (Physical Memory) | Swap (Virtual Memory) |
|---|---|---|
| Location | Physical memory chips (fast) | Disk/SSD space (much slower) |
| Speed | Very fast (nanoseconds) | Slow (milliseconds — thousands of times slower) |
| Purpose | Active working memory for running processes | Overflow space when RAM is full; also stores inactive memory pages |
| Volatile? | Yes (lost on reboot) | Persisted on disk, but treated as temporary |
| Typical size | Fixed (physically installed) | Configurable (swap file or partition) |

**Why does swap exist?**
- Acts as a safety net when RAM fills up, preventing the system from immediately crashing or killing processes (`Out Of Memory` errors).
- Lets the kernel move **inactive** memory pages (data not used recently) out of RAM to make room for more frequently used data — even if RAM isn't technically full yet.
- Enables **hibernation** (saving full RAM state to disk) on some systems.

**Important myth-buster:** Swap being used ≠ system is in trouble. Linux proactively swaps out cold/idle memory pages to free up RAM for caching and active processes. It only becomes a real problem when swap usage is **high** and the system feels **sluggish** (heavy, constant swapping is called "thrashing").

---

## 2. Checking Memory Usage

| Command | Purpose |
|---|---|
| `free -h` | Show RAM & swap usage (human-readable) |
| `free -m` | Show in megabytes |
| `free -g` | Show in gigabytes |
| `free -s 5` | Auto-refresh every 5 seconds |
| `top` | Live view including per-process memory |
| `htop` | Nicer interactive version of `top` |
| `cat /proc/meminfo` | Very detailed raw memory stats |
| `vmstat` | Virtual memory statistics summary |
| `swapon --show` | List active swap devices/files |
| `cat /proc/swaps` | Similar swap info, raw format |

**Examples:**
```bash
free -h
vmstat 1 5        # sample every 1 second, 5 times
swapon --show
cat /proc/meminfo | head -20
```

---

## 3. Understanding `free -h` Output

Example output:
```
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       2.3Gi       230Mi        45Mi       1.3Gi       1.6Gi
Swap:          3.6Gi       432Mi       3.2Gi
```

| Column | Meaning |
|---|---|
| `total` | Total physical RAM (or total swap) installed/configured |
| `used` | Memory currently in use by processes |
| `free` | Completely unused memory (misleadingly low — see below) |
| `shared` | Memory used by `tmpfs` and shared between processes |
| `buff/cache` | Memory used for disk buffers/page cache — reclaimable on demand |
| `available` | **The real number to watch** — estimated RAM available for new applications without swapping |

**Key insight:** Don't panic over a low `free` value. Linux deliberately uses spare RAM for `buff/cache` to speed up disk access, and instantly releases it when apps need more memory. Always check `available`, not `free`, to judge real memory pressure.

---

## 4. What is Swappiness?

`swappiness` is a kernel parameter (0–100) controlling **how aggressively** the kernel swaps memory pages to disk vs. dropping page cache.

| Value | Behavior |
|---|---|
| `0` | Avoid swapping as much as possible (only swap to prevent OOM) |
| `60` | Default on most distros — balanced |
| `100` | Swap aggressively, even with RAM still available |

**Check current swappiness:**
```bash
cat /proc/sys/vm/swappiness
```

**Change temporarily (until reboot):**
```bash
sudo sysctl vm.swappiness=10
```

**Change permanently:**
```bash
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

Lower swappiness (e.g. `10`) is often recommended on desktops/laptops with SSDs to reduce swap wear and keep the system snappier; higher values may suit servers that prioritize caching.

---

## 5. Creating & Managing a Swap File

A swap file is the easiest way to add/resize swap space without repartitioning disks.

**Step 1: Create a swap file (example: 2GB)**
```bash
sudo fallocate -l 2G /swapfile
# If fallocate isn't supported by your filesystem:
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
```

**Step 2: Secure the file (only root can read/write)**
```bash
sudo chmod 600 /swapfile
```

**Step 3: Set it up as swap space**
```bash
sudo mkswap /swapfile
```

**Step 4: Enable it**
```bash
sudo swapon /swapfile
```

**Step 5: Verify**
```bash
sudo swapon --show
free -h
```

**Disable a swap file:**
```bash
sudo swapoff /swapfile
```

**Remove a swap file entirely:**
```bash
sudo swapoff /swapfile
sudo rm /swapfile
```

---

## 6. Creating & Managing a Swap Partition

If you have a dedicated partition (e.g., `/dev/sdb1`) for swap:

```bash
sudo mkswap /dev/sdb1     # format the partition as swap
sudo swapon /dev/sdb1     # activate it
```

Check it's active:
```bash
sudo swapon --show
```

Deactivate:
```bash
sudo swapoff /dev/sdb1
```

---

## 7. Enabling Swap Permanently (fstab)

Swap enabled with `swapon` only lasts until reboot unless added to `/etc/fstab`.

**Add a swap file to fstab:**
```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Add a swap partition to fstab (using UUID is safer):**
```bash
sudo blkid /dev/sdb1        # find the UUID
```
Then add a line like:
```
UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx none swap sw 0 0
```

**Test the fstab entry without rebooting:**
```bash
sudo swapon -a
```

---

## 8. Monitoring & Troubleshooting

**See per-process memory usage:**
```bash
ps aux --sort=-%mem | head -10
```

**See what's using swap the most (per process):**
```bash
for pid in /proc/[0-9]*; do
  swap=$(grep VmSwap "$pid/status" 2>/dev/null | awk '{print $2}')
  [ -n "$swap" ] && [ "$swap" -gt 0 ] && echo "$swap KB - $pid $(cat $pid/comm 2>/dev/null)"
done | sort -n
```

**Watch memory & swap in real time:**
```bash
watch -n 1 free -h
```

**Signs of real memory pressure ("thrashing"):**
- `available` memory in `free -h` is very low
- Swap `used` keeps climbing steadily
- System feels sluggish, disk activity light stays constantly busy
- `vmstat 1` shows high numbers in the `si`/`so` (swap in/out) columns

**Clear cached memory (rarely needed, for testing only):**
```bash
sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
```

**Common fixes for high swap usage:**
- Add more physical RAM
- Increase swap size
- Lower `swappiness`
- Identify and close/restart memory-leaking processes (`ps aux --sort=-%mem`)

---

## Quick Reference Cheat Sheet

```bash
# check memory/swap
free -h                          # RAM & swap summary
vmstat 1 5                       # live memory stats
swapon --show                    # list active swap
cat /proc/meminfo                # detailed raw stats

# swappiness
cat /proc/sys/vm/swappiness      # check current value
sudo sysctl vm.swappiness=10     # change temporarily

# swap file setup
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# swap partition setup
sudo mkswap /dev/sdb1
sudo swapon /dev/sdb1

# disable/remove swap
sudo swapoff /swapfile
sudo rm /swapfile

# make permanent (fstab)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo swapon -a                   # apply without reboot

# monitor
ps aux --sort=-%mem | head -10   # top RAM consumers
watch -n 1 free -h                # live watch
```
