# Linux Essentials: grep

A practical reference guide with detailed explanations and working examples.

---

## 1. grep

`grep` (Global Regular Expression Print) searches text using patterns and prints matching lines. It's one of the most-used tools for searching inside files.

### 1.1 Basic Syntax

```bash
grep [OPTIONS] "pattern" file(s)
```

### 1.2 Common Options

| Option | Meaning |
|--------|---------|
| `-i` | Case-insensitive search |
| `-v` | Invert match (show non-matching lines) |
| `-r` or `-R` | Recursive search through directories |
| `-n` | Show line numbers |
| `-l` | Show only file names with matches |
| `-c` | Count matching lines |
| `-w` | Match whole words only |
| `-E` | Extended regex (same as `egrep`) |
| `-A n` | Show `n` lines **after** match |
| `-B n` | Show `n` lines **before** match |
| `-C n` | Show `n` lines of context around match |
| `--color` | Highlight matches |

### 1.3 Examples

**Sample file `access.log`:**
```
192.168.1.10 - GET /home 200
192.168.1.15 - GET /login 404
192.168.1.10 - POST /submit 500
192.168.1.22 - GET /home 200
```

**Basic search:**
```bash
grep "404" access.log
```
Output:
```
192.168.1.15 - GET /login 404
```

**Case-insensitive search:**
```bash
grep -i "get" access.log
```

**Show line numbers:**
```bash
grep -n "200" access.log
```
Output:
```
1:192.168.1.10 - GET /home 200
4:192.168.1.22 - GET /home 200
```

**Invert match (lines NOT containing "200"):**
```bash
grep -v "200" access.log
```

**Count matches:**
```bash
grep -c "GET" access.log
```
Output: `3`

**Recursive search in a directory for a word:**
```bash
grep -rn "TODO" /home/user/project/
```

**Search using regex (extended):**
```bash
grep -E "50[0-9]" access.log
```
Matches any 5xx status code (500–509).

**Search with context (2 lines before & after):**
```bash
grep -C 2 "500" access.log
```

**Search only file names containing a match:**
```bash
grep -l "error" *.log
```

**Combine with pipes (very common real-world use):**
```bash
ps aux | grep "nginx"
```

**Match whole word only (avoid partial matches):**
```bash
grep -w "cat" animals.txt   # matches "cat" but not "category"
```

---

## Quick Reference Cheat Sheet

```bash
# grep
grep -rn "pattern" /path/            # recursive, with line numbers
grep -i "pattern" file                # case-insensitive
grep -v "pattern" file                # invert match
grep -c "pattern" file                # count matches
```
