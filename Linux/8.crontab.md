# Linux Essentials: Crontab

A practical reference guide with detailed explanations and working examples.

---

## 4. Crontab

`crontab` schedules commands or scripts to run automatically at fixed times, dates, or intervals — Linux's built-in task scheduler.

### 4.1 Key Commands

```bash
crontab -e      # Edit current user's crontab
crontab -l      # List current user's cron jobs
crontab -r      # Remove all cron jobs for current user
crontab -u username -e   # Edit another user's crontab (needs root)
```

### 4.2 Crontab Syntax

```
* * * * * command-to-execute
│ │ │ │ │
│ │ │ │ └── Day of week (0-7) (Sunday = 0 or 7)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

Special characters:

| Symbol | Meaning |
|---|---|
| `*` | Every value (wildcard) |
| `,` | List of values (e.g., `1,15`) |
| `-` | Range of values (e.g., `1-5`) |
| `/` | Step values (e.g., `*/10`) |

### 4.3 Examples

**Run a script every day at 2:30 AM:**
```
30 2 * * * /home/user/backup.sh
```

**Run every 10 minutes:**
```
*/10 * * * * /home/user/scripts/check_status.sh
```

**Run every Monday at 9:00 AM:**
```
0 9 * * 1 /home/user/scripts/weekly_report.sh
```

**Run on the 1st day of every month at midnight:**
```
0 0 1 * * /home/user/scripts/monthly_cleanup.sh
```

**Run every 5 minutes between 9 AM–5 PM on weekdays:**
```
*/5 9-17 * * 1-5 /home/user/scripts/monitor.sh
```

**Run twice a day (6 AM and 6 PM):**
```
0 6,18 * * * /home/user/scripts/sync.sh
```

### 4.4 Redirecting Output/Logs (Best Practice)

By default cron emails output (if mail is configured) or discards it. It's best to log manually:

```
30 2 * * * /home/user/backup.sh >> /home/user/logs/backup.log 2>&1
```
- `>>` appends standard output to the log file.
- `2>&1` redirects standard error into the same log file.

### 4.5 Practical Example — Full Setup

**Step 1: Create the script**
```bash
#!/bin/bash
# /home/user/scripts/disk_check.sh
THRESHOLD=80
USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')

if [ "$USAGE" -ge "$THRESHOLD" ]; then
    echo "$(date): WARNING - Disk usage is at ${USAGE}%" >> /home/user/logs/disk_alert.log
fi
```

**Step 2: Make executable**
```bash
chmod +x /home/user/scripts/disk_check.sh
```

**Step 3: Add to crontab (runs every hour)**
```bash
crontab -e
```
Add the line:
```
0 * * * * /home/user/scripts/disk_check.sh
```

**Step 4: Verify it's scheduled**
```bash
crontab -l
```

### 4.6 Special Cron Strings (Shortcuts)

| String | Equivalent |
|---|---|
| `@reboot` | Run once at startup |
| `@yearly` / `@annually` | `0 0 1 1 *` |
| `@monthly` | `0 0 1 * *` |
| `@weekly` | `0 0 * * 0` |
| `@daily` / `@midnight` | `0 0 * * *` |
| `@hourly` | `0 * * * *` |

Example:
```
@reboot /home/user/scripts/startup_script.sh
```

### 4.7 System-Wide Crontab

Beyond per-user crontabs, system jobs can go in `/etc/crontab` or `/etc/cron.d/`, which include an extra **user** field:

```
# /etc/crontab format
30 2 * * * root /usr/local/bin/system_backup.sh
```

Or drop scripts directly into:
```
/etc/cron.daily/
/etc/cron.hourly/
/etc/cron.weekly/
/etc/cron.monthly/
```

---

## Quick Reference Cheat Sheet

```bash
# crontab
crontab -e                            # edit
crontab -l                            # list
crontab -r                            # remove all
# m h dom mon dow command
```
