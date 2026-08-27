# Linux Essentials: `top` Command

A practical reference guide to the `top` command — Linux's real-time process and resource monitor.

---

## 1. What is `top`?

`top` shows a live, continuously updating view of:
- Running processes
- CPU usage
- Memory (RAM) usage
- Swap usage
- System load and uptime

It's the go-to command when you want to quickly check "what's eating my CPU/RAM right now?"

### Basic Usage

```bash
top
```

Press `q` to quit.

### Common Options

| Option | Meaning |
|---|---|
| `top -u username` | Show only processes owned by a specific user |
| `top -p PID` | Monitor a specific process by PID |
| `top -n 1` | Run once and exit (useful in scripts) |
| `top -d 5` | Refresh every 5 seconds instead of default (3s) |

### Useful Interactive Keys (while `top` is running)

| Key | Action |
|---|---|
| `q` | Quit |
| `k` | Kill a process (prompts for PID) |
| `M` | Sort by memory usage |
| `P` | Sort by CPU usage |
| `1` | Toggle per-core CPU breakdown |
| `r` | Renice (change priority) a process |
| `h` | Help |

---

## 2. Explaining the Example Output

Here's the example output from your terminal:

```
top - 15:04:06 up  4:42,  1 user,  load average: 0.33, 0.14, 0.06
Tasks: 244 total,   1 running, 243 sleeping,   0 stopped,   0 zombie
%Cpu(s):  1.0 us,  0.4 sy,  0.0 ni, 98.5 id,  0.0 wa,  0.0 hi,  0.1 si,  0.0 st
MiB Mem :   3915.7 total,    230.2 free,   2356.8 used,   1328.7 buff/cache
MiB Swap:   3716.0 total,   3283.2 free,    432.8 used.   1645.4 avail Mem 
    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND  
   2027 naim      20   0 5130912 290032  79936 S   4.6   7.2   6:27.70 gnome-s+ 
   4913 naim      20   0  554020  43544  31788 S   1.3   1.1   0:14.18 gnome-t+ 
    544 systemd+  20   0   14836   6164   6028 S   0.3   0.2   0:17.11 systemd+ 
   5485 naim      20   0   11.8g 744872 246892 S   0.3  18.6   6:23.56 firefox  
   6915 naim      20   0 3752304 648908 131480 S   0.3  16.2   2:59.38 Isolate+ 
      1 root      20   0  166856  12184   8396 S   0.0   0.3   0:02.94 systemd  
      2 root      20   0       0      0      0 S   0.0   0.0   0:00.01 kthreadd 
```

Let's break it down section by section.

---

### 2.1 Line 1 — Uptime / Load Summary

```
top - 15:04:06 up  4:42,  1 user,  load average: 0.33, 0.14, 0.06
```

| Field | Meaning |
|---|---|
| `15:04:06` | Current system time |
| `up 4:42` | System has been running (uptime) for **4 hours 42 minutes** |
| `1 user` | Currently **1 user** logged in |
| `load average: 0.33, 0.14, 0.06` | Average system load over the last **1 min, 5 min, and 15 min** |

**About load average:**
- It roughly represents how many processes are waiting for CPU time.
- On a **single-core** system, `1.00` = fully loaded, `0.33` means the CPU is only ~33% "busy" on average over the last minute.
- Your numbers (`0.33, 0.14, 0.06`) are all low and decreasing — meaning the system was briefly a bit busier a minute ago but is now very idle. This is a healthy, lightly-loaded system.

---

### 2.2 Line 2 — Tasks (Processes) Summary

```
Tasks: 244 total,   1 running, 243 sleeping,   0 stopped,   0 zombie
```

| Field | Meaning |
|---|---|
| `244 total` | 244 total processes exist on the system |
| `1 running` | Only 1 process is actively executing on the CPU right now |
| `243 sleeping` | 243 processes are idle, waiting for something (input, timer, event) |
| `0 stopped` | No processes are paused/stopped (e.g., via `Ctrl+Z`) |
| `0 zombie` | No zombie processes (dead processes whose exit status hasn't been collected by their parent) |

This is normal — most processes on a desktop system are "sleeping" most of the time, only waking up when needed.

---

### 2.3 Line 3 — CPU Usage Breakdown

```
%Cpu(s):  1.0 us,  0.4 sy,  0.0 ni, 98.5 id,  0.0 wa,  0.0 hi,  0.1 si,  0.0 st
```

| Field | Meaning |
|---|---|
| `us` (user) | 1.0% — CPU time spent running normal **user-space** programs |
| `sy` (system) | 0.4% — CPU time spent running **kernel/system** processes |
| `ni` (nice) | 0.0% — CPU time spent on processes with a custom **nice/priority** value |
| `id` (idle) | 98.5% — CPU is **idle**, doing nothing |
| `wa` (I/O wait) | 0.0% — CPU time spent waiting for **disk/I/O** operations to finish |
| `hi` (hardware interrupts) | 0.0% — Time spent handling **hardware interrupts** |
| `si` (software interrupts) | 0.1% — Time spent handling **software interrupts** |
| `st` (steal time) | 0.0% — Time "stolen" by a **hypervisor** for other VMs (relevant in virtualized/cloud environments) |

**In plain terms:** your CPU is 98.5% idle — the machine is barely doing any work right now. This matches a lightly-loaded desktop/VM.

---

### 2.4 Line 4 — Memory (RAM) Usage

```
MiB Mem :   3915.7 total,    230.2 free,   2356.8 used,   1328.7 buff/cache
```

| Field | Meaning |
|---|---|
| `total` | 3915.7 MiB (~3.9 GB) total physical RAM installed |
| `free` | 230.2 MiB completely unused RAM |
| `used` | 2356.8 MiB actively used by running programs |
| `buff/cache` | 1328.7 MiB used by the kernel for **disk buffers/cache** (speeds up file access; automatically freed if apps need it) |

**Important:** `free` looking low (230.2 MiB) is **not a problem**. Linux aggressively uses spare RAM for `buff/cache` to speed things up, and instantly reclaims it when applications need more memory. The number to actually worry about is `avail Mem` (see below).

---

### 2.5 Line 5 — Swap Usage

```
MiB Swap:   3716.0 total,   3283.2 free,    432.8 used.   1645.4 avail Mem 
```

| Field | Meaning |
|---|---|
| `total` | 3716.0 MiB total swap space (disk-based virtual memory) configured |
| `free` | 3283.2 MiB swap currently unused |
| `used` | 432.8 MiB swap currently in use |
| `avail Mem` | 1645.4 MiB — RAM realistically **available for new applications** without swapping (this is the important number, more meaningful than "free") |

Swap being used a little (432.8 MiB) is normal and not necessarily a red flag — Linux may move rarely-used pages to swap to keep more RAM free for active work. It would only be a concern if swap usage is very high **and** the system feels sluggish.

---

### 2.6 Column Headers & Process Rows

```
    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND  
   2027 naim      20   0 5130912 290032  79936 S   4.6   7.2   6:27.70 gnome-s+ 
```

| Column | Meaning |
|---|---|
| `PID` | Process ID — unique number identifying the process |
| `USER` | The user account that owns/runs this process |
| `PR` | Priority of the process (lower number = higher priority) |
| `NI` | "Nice" value — user-adjustable priority modifier (-20 = highest priority, 19 = lowest) |
| `VIRT` | Total virtual memory used by the process (includes shared libs, mapped files, etc.) |
| `RES` | Resident memory — actual physical RAM currently used by the process |
| `SHR` | Shared memory — RAM shared with other processes (e.g., shared libraries) |
| `S` | Process state (see table below) |
| `%CPU` | Percentage of CPU currently used by this process |
| `%MEM` | Percentage of total RAM used by this process |
| `TIME+` | Total CPU time the process has consumed since it started |
| `COMMAND` | Name of the command/program (truncated with `+` if too long) |

**Process state (`S` column) values:**

| Value | Meaning |
|---|---|
| `R` | Running |
| `S` | Sleeping (waiting, idle) |
| `D` | Uninterruptible sleep (usually waiting on I/O) |
| `T` | Stopped/traced |
| `Z` | Zombie |

### Row-by-Row Walkthrough of Your Example

**Row 1:**
```
2027 naim      20   0 5130912 290032  79936 S   4.6   7.2   6:27.70 gnome-s+ 
```
- PID `2027`, owned by user `naim`
- Priority `20`, nice value `0` (default/normal priority)
- Using ~290 MB of actual RAM (`RES`), out of ~5.1 GB virtual (`VIRT`)
- Currently `S` = sleeping
- Using `4.6%` CPU and `7.2%` of total RAM — the **highest CPU user** in this snapshot
- Has accumulated `6:27.70` (6 minutes 27.7 seconds) of CPU time since it started
- Command is `gnome-s+` — truncated name, almost certainly **`gnome-shell`** (the GNOME desktop environment's core process)

**Row 4:**
```
5485 naim      20   0   11.8g 744872 246892 S   0.3  18.6   6:23.56 firefox  
```
- This is **Firefox**
- Using **18.6% of total RAM** — the biggest memory consumer in this list (very typical for browsers with multiple tabs)
- Only using `0.3%` CPU right now — mostly idle/sleeping at this moment
- `VIRT` is `11.8g` (11.8 GB) — normal for browsers since they reserve large virtual address space

**Row 5:**
```
6915 naim      20   0 3752304 648908 131480 S   0.3  16.2   2:59.38 Isolate+ 
```
- Command `Isolate+` is almost certainly **`Isolated Web Co`** — a Firefox content/sandbox process (Firefox splits tabs/sites into isolated processes for security)
- Using `16.2%` RAM, `0.3%` CPU

**Row with `root` user, low PID:**
```
1 root      20   0  166856  12184   8396 S   0.0   0.3   0:02.94 systemd  
```
- PID `1` is always the **first process** started by the kernel at boot — here it's `systemd`, the init system that manages all other services/processes
- Owned by `root`, using very little CPU/RAM — it mostly just supervises other processes

**`kworker` / `kthreadd` rows:**
```
2 root      20   0       0      0      0 S   0.0   0.0   0:00.01 kthreadd 
4 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+ 
```
- These are **kernel threads** — internal Linux kernel workers that handle background hardware/system tasks
- `VIRT`/`RES`/`SHR` are `0` because kernel threads don't use regular userspace memory
- Nice value `-20` on `kworker` means very high priority (kernel work often needs to run promptly)
- State `I` = idle (a sub-state of sleeping, meaning it's a kernel thread waiting with nothing to do)

---

## 3. Quick Takeaways From This Example

- System has been up **4h42m**, lightly loaded (load average well under 1.0)
- CPU is **98.5% idle** — nothing is stressing the processor
- RAM: ~2.3 GB used out of ~3.9 GB total, with **1.6 GB realistically available**
- Swap is barely used (432.8 MB) — not a concern
- Biggest resource users are desktop/browser related: `gnome-shell`, `firefox`, and Firefox's `Isolated Web Co` sandbox process — completely normal for an active desktop session
- No zombie or stopped processes — system is healthy

---

## Quick Reference Cheat Sheet

```bash
top                     # launch top
top -u naim             # show only processes owned by 'naim'
top -p 5485             # monitor a specific PID
top -n 1                # run once and exit (good for scripts/logs)
top -d 5                # refresh every 5 seconds

# inside top:
q   # quit
M   # sort by memory
P   # sort by CPU
k   # kill a process
1   # toggle per-core CPU view
```
