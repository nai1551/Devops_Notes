# Linux Essentials: tar and zip

A practical reference guide with detailed explanations and working examples.

---

## Table of Contents
1. [tar](#1-tar)
2. [zip / unzip](#2-zip--unzip)
3. [tar vs zip](#3-tar-vs-zip)

---

## 1. tar

`tar` (Tape Archive) bundles multiple files/directories into a single archive file. It doesn't compress by default — compression is added via flags (gzip, bzip2, xz).

### 1.1 Basic Syntax

```bash
tar [OPTIONS] archive_name file(s)/directory
```

### 1.2 Common Options

| Option | Meaning |
|--------|---------|
| `-c` | Create a new archive |
| `-x` | Extract files from an archive |
| `-t` | List contents of an archive (without extracting) |
| `-v` | Verbose (show files being processed) |
| `-f` | Specify the filename of the archive (must come right before the filename) |
| `-z` | Compress/decompress using **gzip** (`.tar.gz` / `.tgz`) |
| `-j` | Compress/decompress using **bzip2** (`.tar.bz2`) |
| `-J` | Compress/decompress using **xz** (`.tar.xz`) |
| `-C` | Change to a directory before extracting/creating |
| `--exclude=pattern` | Exclude files matching a pattern |
| `-r` | Append files to an existing archive |
| `-p` | Preserve file permissions |

### 1.3 Examples

**Create an uncompressed archive:**
```bash
tar -cvf project.tar project/
```

**Create a gzip-compressed archive:**
```bash
tar -czvf project.tar.gz project/
```

**Create a bzip2-compressed archive:**
```bash
tar -cjvf project.tar.bz2 project/
```

**Create an xz-compressed archive (best compression, slower):**
```bash
tar -cJvf project.tar.xz project/
```

**Extract a `.tar` archive:**
```bash
tar -xvf project.tar
```

**Extract a `.tar.gz` archive:**
```bash
tar -xzvf project.tar.gz
```

**Extract a `.tar.bz2` archive:**
```bash
tar -xjvf project.tar.bz2
```

**Extract into a specific directory:**
```bash
tar -xzvf project.tar.gz -C /home/user/restore/
```

**List contents without extracting:**
```bash
tar -tvf project.tar.gz
```

**Extract only a single file from an archive:**
```bash
tar -xzvf project.tar.gz project/config.yml
```

**Create an archive while excluding certain files:**
```bash
tar -czvf project.tar.gz --exclude="*.log" --exclude="node_modules" project/
```

**Append a file to an existing (uncompressed) archive:**
```bash
tar -rvf project.tar newfile.txt
```

**Check archive size vs compressed size:**
```bash
du -sh project/
du -sh project.tar.gz
```

### 1.4 Quick Identification Cheat Sheet

| File Extension | Command to Extract |
|---|---|
| `.tar` | `tar -xvf file.tar` |
| `.tar.gz` / `.tgz` | `tar -xzvf file.tar.gz` |
| `.tar.bz2` / `.tbz2` | `tar -xjvf file.tar.bz2` |
| `.tar.xz` | `tar -xJvf file.tar.xz` |

---

## 2. zip / unzip

`zip` creates compressed archives (`.zip` format), widely compatible across Linux, macOS, and Windows. `unzip` extracts them. Unlike `tar`, `zip` compresses files as it archives them (all-in-one step).

### 2.1 Installation (if not already present)

```bash
sudo apt install zip unzip        # Debian/Ubuntu
sudo yum install zip unzip        # RHEL/CentOS
```

### 2.2 Common `zip` Options

| Option | Meaning |
|--------|---------|
| `-r` | Recursively zip a directory and its contents |
| `-e` | Encrypt the archive with a password |
| `-9` | Maximum compression level (0 = none, 9 = best) |
| `-x` | Exclude files matching a pattern |
| `-u` | Update an existing zip with newer files |
| `-d` | Delete a file from an existing zip |
| `-v` | Verbose output |
| `-m` | Move files into the zip (deletes originals after) |

### 2.3 Common `unzip` Options

| Option | Meaning |
|--------|---------|
| `-l` | List contents without extracting |
| `-d` | Extract into a specified directory |
| `-o` | Overwrite existing files without prompting |
| `-x` | Exclude specific files during extraction |
| `-t` | Test archive integrity |

### 2.4 Examples

**Zip a single file:**
```bash
zip archive.zip file.txt
```

**Zip multiple files:**
```bash
zip archive.zip file1.txt file2.txt file3.txt
```

**Zip an entire directory (recursive):**
```bash
zip -r project.zip project/
```

**Zip with maximum compression:**
```bash
zip -r -9 project.zip project/
```

**Create a password-protected zip:**
```bash
zip -er secure.zip project/
```
(You'll be prompted to enter and confirm a password.)

**Exclude files while zipping:**
```bash
zip -r project.zip project/ -x "*.log" -x "node_modules/*"
```

**Update an existing zip with changed files:**
```bash
zip -ur project.zip project/
```

**Delete a file from an existing zip:**
```bash
zip -d project.zip unwanted_file.txt
```

**List contents of a zip without extracting:**
```bash
unzip -l project.zip
```

**Extract a zip into the current directory:**
```bash
unzip project.zip
```

**Extract into a specific directory:**
```bash
unzip project.zip -d /home/user/restore/
```

**Extract, overwriting existing files without prompts:**
```bash
unzip -o project.zip
```

**Extract a single file from a zip:**
```bash
unzip project.zip file1.txt
```

**Test a zip archive for corruption:**
```bash
unzip -t project.zip
```

**Extract a password-protected zip:**
```bash
unzip secure.zip
# Prompts for password interactively
```

---

## 3. tar vs zip

| Feature | tar (+gzip/xz) | zip |
|---|---|---|
| Native to | Linux/Unix | Cross-platform (Windows-friendly) |
| Compression | Separate step (`-z`, `-j`, `-J`) | Built-in, per-file |
| Preserves Linux permissions/symlinks | Yes | Limited |
| Password protection | Not built-in (needs extra tools) | Built-in (`-e`) |
| Random access to single files | Slower (sequential format) | Faster (indexed format) |
| Typical use case | Backups, Linux-to-Linux transfers | Sharing files with Windows/macOS users |

---

## Quick Reference Cheat Sheet

```bash
# tar
tar -cvf archive.tar dir/             # create archive
tar -czvf archive.tar.gz dir/         # create gzip-compressed archive
tar -xvf archive.tar                  # extract
tar -xzvf archive.tar.gz              # extract gzip archive
tar -tvf archive.tar.gz               # list contents

# zip / unzip
zip -r archive.zip dir/               # zip a directory
zip -er secure.zip dir/               # password-protected zip
unzip archive.zip                     # extract
unzip -l archive.zip                  # list contents
unzip -d /path/ archive.zip           # extract to a directory
```
