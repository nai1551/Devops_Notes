# Linux Essentials: Other Basic Commands

A practical reference guide covering common Linux commands (outside grep, links, bash scripting, crontab, tar/zip).

---

## Table of Contents
1. [Navigation & File Listing](#1-navigation--file-listing)
2. [File & Directory Operations](#2-file--directory-operations)
3. [Viewing File Contents](#3-viewing-file-contents)
4. [Permissions & Ownership](#4-permissions--ownership)
5. [Process Management](#5-process-management)
6. [Disk & Storage](#6-disk--storage)
7. [System Info & Monitoring](#7-system-info--monitoring)
8. [Networking](#8-networking)
9. [User Management](#9-user-management)
10. [Package Management](#10-package-management)
11. [Text Processing Tools](#11-text-processing-tools)
12. [Search Tools](#12-search-tools)

---

## 1. Navigation & File Listing

| Command | Meaning |
|---|---|
| `pwd` | Print current working directory |
| `cd dir` | Change directory |
| `cd ..` | Go up one directory |
| `cd ~` or `cd` | Go to home directory |
| `cd -` | Go to previous directory |
| `ls` | List files in current directory |
| `ls -l` | Long listing (permissions, size, owner, date) |
| `ls -a` | Show hidden files (starting with `.`) |
| `ls -lh` | Long listing with human-readable sizes |
| `ls -R` | List recursively |
| `tree` | Show directory structure as a tree (may need install) |

**Examples:**
```bash
pwd
cd /var/log
ls -lah
tree -L 2 /home/user/project
```

---

## 2. File & Directory Operations

| Command | Meaning |
|---|---|
| `mkdir dir` | Create a directory |
| `mkdir -p a/b/c` | Create nested directories |
| `rmdir dir` | Remove an empty directory |
| `touch file` | Create an empty file / update timestamp |
| `cp src dest` | Copy a file |
| `cp -r src dest` | Copy a directory recursively |
| `mv src dest` | Move or rename a file/directory |
| `rm file` | Delete a file |
| `rm -r dir` | Delete a directory recursively |
| `rm -rf dir` | Force delete recursively (⚠️ irreversible) |
| `find` | Search for files/directories |
| `df -h` | Disk free space (human-readable) |
| `du -sh dir` | Size of a directory |

**Examples:**
```bash
mkdir -p projects/2026/backup
touch notes.txt
cp report.docx report_backup.docx
cp -r project/ project_copy/
mv oldname.txt newname.txt
rm -rf temp/
```

---

## 3. Viewing File Contents

| Command | Meaning |
|---|---|
| `cat file` | Print entire file content |
| `less file` | View file page-by-page (scrollable, `q` to quit) |
| `more file` | Similar to `less`, older/simpler |
| `head file` | Show first 10 lines |
| `head -n 20 file` | Show first 20 lines |
| `tail file` | Show last 10 lines |
| `tail -n 20 file` | Show last 20 lines |
| `tail -f file` | Follow file in real time (great for logs) |
| `wc file` | Count lines, words, bytes |
| `wc -l file` | Count lines only |
| `diff file1 file2` | Show differences between two files |
| `nano file` | Simple terminal text editor |
| `vim file` | Powerful terminal text editor |

**Examples:**
```bash
cat access.log
less /var/log/syslog
tail -f /var/log/app.log
wc -l access.log
diff config_old.conf config_new.conf
```

---

## 4. Permissions & Ownership

| Command | Meaning |
|---|---|
| `chmod` | Change file permissions |
| `chmod 755 file` | Set permissions numerically (rwxr-xr-x) |
| `chmod +x file` | Add execute permission |
| `chmod -w file` | Remove write permission |
| `chown user file` | Change file owner |
| `chown user:group file` | Change owner and group |
| `chgrp group file` | Change group ownership |
| `umask` | Show/set default permission mask |

**Permission reference:**
```
r = read (4)    w = write (2)    x = execute (1)

rwxr-xr-x  =  7 5 5
│││││││││
││││││└┴┴─ others: r-x (5)
│││└┴┴──── group:  r-x (5)
└┴┴──────── owner:  rwx (7)
```

**Examples:**
```bash
chmod 644 file.txt          # owner: rw-, group: r--, others: r--
chmod +x script.sh          # make executable
chown alice:developers app.log
chown -R www-data:www-data /var/www/html
```

---

## 5. Process Management

| Command | Meaning |
|---|---|
| `ps` | Show running processes (current shell) |
| `ps aux` | Show all running processes (detailed) |
| `top` | Real-time process/resource monitor |
| `htop` | Improved, interactive version of `top` (needs install) |
| `kill PID` | Terminate a process by PID |
| `kill -9 PID` | Force kill a process |
| `killall name` | Kill all processes matching a name |
| `pkill name` | Kill processes matching a pattern |
| `jobs` | List background jobs in current shell |
| `bg` | Resume a job in background |
| `fg` | Bring a job to foreground |
| `nohup cmd &` | Run command immune to hangups, in background |
| `&` | Run a command in background |
| `nice -n 10 cmd` | Run a command with adjusted priority |

**Examples:**
```bash
ps aux | grep nginx
top
kill 4521
kill -9 4521
pkill -f "python app.py"
nohup ./long_task.sh &
```

---

## 6. Disk & Storage

| Command | Meaning |
|---|---|
| `df -h` | Show disk space usage per filesystem |
| `du -sh dir` | Show total size of a directory |
| `du -h --max-depth=1 dir` | Show sizes of subdirectories one level deep |
| `mount` | Show/mount filesystems |
| `umount device` | Unmount a filesystem |
| `lsblk` | List block devices (disks/partitions) |
| `fdisk -l` | List disk partitions (needs root) |
| `mkfs.ext4 device` | Format a partition (⚠️ destructive) |

**Examples:**
```bash
df -h
du -sh /var/log
du -h --max-depth=1 /home/user
lsblk
```

---

## 7. System Info & Monitoring

| Command | Meaning |
|---|---|
| `uname -a` | Show kernel/system info |
| `hostname` | Show system hostname |
| `uptime` | Show how long system has been running + load average |
| `whoami` | Show current logged-in user |
| `id` | Show user/group IDs |
| `date` | Show current date/time |
| `cal` | Show a calendar |
| `free -h` | Show RAM/swap usage |
| `history` | Show command history |
| `clear` | Clear the terminal screen |
| `man command` | Show manual page for a command |
| `which command` | Show path of a command's executable |
| `alias` | Create a command shortcut |

**Examples:**
```bash
uname -a
uptime
free -h
history | tail -20
man grep
which python3
alias ll='ls -lah'
```

---

## 8. Networking

| Command | Meaning |
|---|---|
| `ping host` | Test connectivity to a host |
| `ifconfig` / `ip a` | Show network interfaces & IP addresses |
| `curl url` | Fetch content from a URL |
| `wget url` | Download a file from a URL |
| `ssh user@host` | Connect to a remote machine via SSH |
| `scp file user@host:path` | Securely copy a file to a remote machine |
| `netstat -tulnp` | Show listening ports and connections |
| `ss -tulnp` | Modern replacement for `netstat` |
| `traceroute host` | Trace the network path to a host |
| `nslookup domain` | DNS lookup for a domain |
| `dig domain` | Detailed DNS lookup |

**Examples:**
```bash
ping -c 4 google.com
ip a
curl -O https://example.com/file.zip
wget https://example.com/file.zip
ssh user@192.168.1.10
scp report.pdf user@server:/home/user/
ss -tulnp
```

---

## 9. User Management

| Command | Meaning |
|---|---|
| `useradd username` | Create a new user (needs root) |
| `passwd username` | Set/change a user's password |
| `userdel username` | Delete a user |
| `usermod -aG group user` | Add a user to a group |
| `groupadd groupname` | Create a new group |
| `su username` | Switch to another user |
| `sudo command` | Run a command as superuser |
| `sudo -i` | Start an interactive root shell |
| `whoami` | Show the current user |
| `w` | Show who is logged in and what they're doing |

**Examples:**
```bash
sudo useradd -m alice
sudo passwd alice
sudo usermod -aG sudo alice
su - alice
sudo apt update
```

---

## 10. Package Management

**Debian/Ubuntu (`apt`):**
```bash
sudo apt update                  # refresh package lists
sudo apt upgrade                 # upgrade installed packages
sudo apt install package_name    # install a package
sudo apt remove package_name     # remove a package
sudo apt search keyword          # search for a package
```

**RHEL/CentOS/Fedora (`yum` / `dnf`):**
```bash
sudo yum install package_name
sudo yum remove package_name
sudo dnf update
```

**Arch (`pacman`):**
```bash
sudo pacman -S package_name      # install
sudo pacman -R package_name      # remove
sudo pacman -Syu                 # update system
```

---

## 11. Text Processing Tools

| Command | Meaning |
|---|---|
| `awk '{print $1}' file` | Extract/process columns of text |
| `sed 's/old/new/g' file` | Find & replace text (stream editor) |
| `sort file` | Sort lines alphabetically/numerically |
| `sort -n file` | Sort numerically |
| `sort -r file` | Sort in reverse order |
| `uniq file` | Remove adjacent duplicate lines |
| `sort file | uniq` | Remove all duplicate lines |
| `cut -d',' -f1 file` | Extract a field by delimiter |
| `tr 'a-z' 'A-Z'` | Translate/replace characters |
| `xargs` | Build/execute commands from input |

**Examples:**
```bash
awk '{print $1, $4}' access.log
sed 's/error/ERROR/g' app.log
sort -n numbers.txt
sort names.txt | uniq -c
cut -d',' -f2 data.csv
cat names.txt | tr 'a-z' 'A-Z'
find . -name "*.tmp" | xargs rm
```

---

## 12. Search Tools

| Command | Meaning |
|---|---|
| `find /path -name "*.txt"` | Find files by name |
| `find /path -type d -name "logs"` | Find directories by name |
| `find /path -mtime -7` | Find files modified in the last 7 days |
| `find /path -size +100M` | Find files larger than 100MB |
| `locate filename` | Fast file search using an index (needs `updatedb`) |
| `which command` | Find the path of an executable |
| `whereis command` | Find binary, source, and man page of a command |

**Examples:**
```bash
find /home/user -name "*.log"
find /var/www -type f -mtime -1
find / -size +500M 2>/dev/null
locate nginx.conf
whereis bash
```

---

## Quick Reference Cheat Sheet

```bash
# navigation
pwd; cd dir; ls -lah

# file ops
mkdir -p a/b; cp -r src dest; mv old new; rm -rf dir

# viewing
cat file; less file; tail -f file; wc -l file

# permissions
chmod 755 file; chown user:group file

# processes
ps aux | grep name; kill -9 PID; top

# disk
df -h; du -sh dir

# system info
uname -a; uptime; free -h; man command

# networking
ping host; curl -O url; ssh user@host; scp file user@host:path

# users
sudo useradd name; sudo passwd name; sudo usermod -aG group name

# packages (Debian/Ubuntu)
sudo apt update && sudo apt install package_name

# text processing
awk '{print $1}' file; sed 's/old/new/g' file; sort file | uniq -c

# search
find /path -name "*.txt"; locate filename
```
