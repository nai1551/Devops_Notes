# Linux Essentials: Soft Links vs Hard Links

A practical reference guide with detailed explanations and working examples.

---

## 2. Soft Links vs Hard Links

Both are ways to create references to files, created with the `ln` command, but they behave very differently.

### 2.1 Hard Link

- Points directly to the same **inode** (the actual data on disk) as the original file.
- Original and hard link are indistinguishable — both are "real" file entries.
- Deleting the original file does **not** delete the data; the hard link still works.
- **Cannot** link across different filesystems/partitions.
- **Cannot** hard link directories (in most systems).

**Create a hard link:**
```bash
echo "Hello World" > original.txt
ln original.txt hardlink.txt
```

**Verify they share the same inode:**
```bash
ls -li original.txt hardlink.txt
```
Output (note the same inode number, first column):
```
123456 -rw-r--r-- 2 user user 12 Aug 25 10:00 original.txt
123456 -rw-r--r-- 2 user user 12 Aug 25 10:00 hardlink.txt
```
The `2` in the third field is the **link count** — it shows two names point to this same inode.

**Test independence from deletion:**
```bash
rm original.txt
cat hardlink.txt      # Still prints "Hello World"
```

### 2.2 Soft Link (Symbolic Link)

- A separate special file that just **stores the path** to the target file.
- Has its **own inode**, different from the original.
- If the original file is deleted or moved, the soft link **breaks** (becomes "dangling").
- **Can** link across filesystems/partitions.
- **Can** link to directories.

**Create a soft link:**
```bash
ln -s original.txt softlink.txt
```

**Verify:**
```bash
ls -li original.txt softlink.txt
```
Output:
```
123456 -rw-r--r-- 1 user user 12 Aug 25 10:00 original.txt
789012 lrwxrwxrwx 1 user user 12 Aug 25 10:01 softlink.txt -> original.txt
```
Notice: different inode numbers, and the `l` at the start of the permissions field, plus the `->` pointing to the target.

**Test what happens when original is deleted:**
```bash
rm original.txt
cat softlink.txt      # cat: softlink.txt: No such file or directory (broken link)
```

**Symlink to a directory:**
```bash
ln -s /var/www/html webroot
cd webroot     # takes you into /var/www/html
```

### 2.3 Comparison Table

| Feature | Hard Link | Soft Link (Symlink) |
|---|---|---|
| Points to | Inode (data) | File path (name) |
| Own inode? | No (shares original's) | Yes |
| Works across filesystems | No | Yes |
| Can link directories | No | Yes |
| Breaks if original deleted | No | Yes (dangling link) |
| Command | `ln target link` | `ln -s target link` |
| Identifiable via `ls -l` | Looks like a normal file | Shown with `l` and `->` |

---

## Quick Reference Cheat Sheet

```bash
# links
ln target hardlink                    # hard link
ln -s target softlink                 # soft/symbolic link
ls -li                                # check inode numbers
```
