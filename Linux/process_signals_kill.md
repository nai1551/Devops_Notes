# Linux Essentials: Process Signals & `kill`

A practical reference guide to Linux process signals and how to send them using `kill`, `killall`, and `pkill`.

---

## 1. What is a Signal?

A **signal** is a software interrupt sent to a process to notify it of an event — like "terminate", "pause", "reload config", etc. The process can handle the signal, ignore it, or let the default action happen (depending on the signal type and whether the program has a custom handler for it).

`kill` is the command used to **send a signal** to a process — despite the name, it doesn't always "kill" anything; that's just its most common use.

---

## 2. Basic Syntax

```bash
kill [-signal] PID
kill -SIGNALNAME PID
kill -SIGNALNUMBER PID
```

All three forms below are equivalent:
```bash
kill -9 1234
kill -SIGKILL 1234
kill -KILL 1234
```

### Finding a Process's PID First

```bash
ps aux | grep firefox
pgrep firefox
```

---

## 3. List All Available Signals

```bash
kill -l
```
This prints all signal names and numbers supported on your system.

---

## 4. Common Signals Explained

| Number | Name | Default Action | Meaning |
|---|---|---|---|
| `1` | `SIGHUP` | Terminate | "Hangup" — originally meant terminal disconnected; now commonly used to tell a daemon/service to **reload its config** without restarting |
| `2` | `SIGINT` | Terminate | "Interrupt" — same as pressing `Ctrl+C` in the terminal |
| `3` | `SIGQUIT` | Terminate + core dump | Like `Ctrl+\` — quit and dump core for debugging |
| `8` | `SIGFPE` | Terminate + core dump | "Floating Point Exception" — sent when a process does an illegal arithmetic operation (e.g., division by zero) |
| `9` | `SIGKILL` | Terminate (forced) | **Force kill** — immediately terminates the process; **cannot be caught, blocked, or ignored** by the process |
| `11` | `SIGSEGV` | Terminate + core dump | "Segmentation Fault" — process tried to access memory it's not allowed to |
| `15` | `SIGTERM` | Terminate | **Default signal sent by `kill`** — politely asks the process to terminate; the process *can* catch this and clean up before exiting |
| `18` | `SIGCONT` | Continue | Resume a process that was previously stopped/paused |
| `19` | `SIGSTOP` | Stop (forced) | Pause a process; **cannot be caught or ignored** (like `SIGKILL` but for pausing) |
| `20` | `SIGTSTP` | Stop | Same as pressing `Ctrl+Z` — request to pause (can be caught, unlike `SIGSTOP`) |

> **Note:** Exact signal numbers can vary slightly between architectures, but the ones above are standard on x86/x86_64 Linux.

---

## 5. Deep Dive: Signal 8 vs Signal 9

Since you mentioned `8` and `9` specifically, here's the key difference:

### Signal 8 — `SIGFPE` (Floating Point Exception)

- **Not something you normally send manually.** It's generated automatically **by the CPU/kernel** when a running program does something like:
  - Integer division by zero
  - Integer overflow in certain operations
  - (Despite the name, it covers various arithmetic errors, not just floating point ones)
- You *can* technically send it manually to test signal handling:
  ```bash
  kill -8 1234
  ```
  But in real-world use, you'd almost never do this — it's the OS's way of telling a buggy program "you just did invalid math."
- If the process doesn't have a custom handler for `SIGFPE`, it terminates and (by default) creates a **core dump** for debugging.

### Signal 9 — `SIGKILL` (Force Kill)

- The most commonly used **manual** kill signal when a process is unresponsive.
- **Cannot be caught, blocked, or ignored** by the target process — the kernel terminates it immediately and unconditionally.
- No chance for the process to clean up (close files, save data, release locks, etc.) — this is why it's considered a "last resort."
```bash
kill -9 1234
```

**Use `SIGKILL` only when:**
- The process is frozen/hung and not responding to `SIGTERM`
- You need to force-stop it immediately regardless of consequences

---

## 6. `SIGTERM` vs `SIGKILL` — The Most Important Comparison

| | `SIGTERM` (15) | `SIGKILL` (9) |
|---|---|---|
| Can be caught/handled by the process? | Yes | No |
| Allows graceful shutdown (save data, close files)? | Yes | No |
| Recommended as first attempt? | Yes ✅ | No — last resort |
| Command | `kill PID` or `kill -15 PID` | `kill -9 PID` |

**Best practice — always try in this order:**
```bash
kill PID          # sends SIGTERM (15) — polite request, default behavior
# wait a few seconds, check if it's still running:
ps -p PID
# if it's still alive and unresponsive:
kill -9 PID        # SIGKILL — force it
```

---

## 7. `kill`, `killall`, and `pkill`

| Command | Targets by | Example |
|---|---|---|
| `kill` | Specific PID | `kill -9 4521` |
| `killall` | Process **name** (all matching) | `killall -9 firefox` |
| `pkill` | Process name/pattern (regex-capable) | `pkill -9 -f "python app.py"` |

**Examples:**
```bash
# Politely ask firefox to close
killall firefox

# Force kill all processes named "node"
killall -9 node

# Kill by matching a command-line pattern
pkill -f "backup.sh"

# Kill all processes owned by a specific user
pkill -u naim
```

---

## 8. Other Useful Signal Examples

**Reload a service's config without restarting it (common for daemons like nginx):**
```bash
kill -1 PID
# or
kill -HUP PID
```

**Pause and resume a process:**
```bash
kill -19 1234      # SIGSTOP - pause it
kill -18 1234      # SIGCONT - resume it
```

**Simulate Ctrl+C on a specific process:**
```bash
kill -2 1234        # SIGINT
```

**Check what signal killed a process (in scripts):**
```bash
./myscript.sh
echo $?
# Exit code > 128 means it was killed by a signal.
# Signal number = exit code - 128
# e.g., exit code 137 = 137 - 128 = signal 9 (SIGKILL)
```

---

## 9. Sending Signals to a Whole Process Group

```bash
kill -9 -PID
```
Using a **negative PID** sends the signal to the entire **process group** (useful for killing a parent process and all its children at once).

---

## Quick Reference Cheat Sheet

```bash
kill PID              # SIGTERM (15) - polite request to terminate
kill -9 PID           # SIGKILL - force kill (last resort)
kill -15 PID          # same as plain "kill PID"
kill -1 PID           # SIGHUP - reload config (for daemons)
kill -19 PID          # SIGSTOP - pause process
kill -18 PID          # SIGCONT - resume paused process
kill -2 PID           # SIGINT - same as Ctrl+C
kill -l               # list all available signals

killall -9 name       # force kill all processes by name
pkill -f "pattern"    # kill by command-line pattern match
pgrep name            # find PID(s) by process name

ps aux | grep name    # find a process's PID before killing it
```
