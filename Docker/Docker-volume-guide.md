# Docker Volumes — A Complete Beginner's Guide

A volume is Docker's mechanism for storing data **outside** a container's own writable layer, so that data can survive container removal, be shared between containers, and be managed independently of any single container's lifecycle.

---

## 1. Why Volumes Exist

By default, anything a container writes lives inside its own temporary writable layer. The moment you run:

```bash
docker rm my-container
```

that data is gone permanently. For a throwaway script, that's fine. For a database, a user's uploaded files, or any real application state, that's a disaster.

Volumes solve this by moving the actual data storage **outside** the container entirely.

---

## 2. The Three (Really Four) Ways to Persist Data

| Type | Example | Who manages the location | Typical use |
|---|---|---|---|
| **Named volume** | `-v db-data:/var/lib/mysql` | Docker | Databases, anything you want Docker to manage for you |
| **Anonymous volume** | `-v /var/lib/mysql` (no name given) | Docker, but with a random name | Rare — usually accidental; hard to reuse later |
| **Bind mount** | `-v ~/site:/usr/share/nginx/html` | You (a real folder you choose) | Live development, config files, direct host access |
| **tmpfs mount** | `--tmpfs /app/cache` | Nobody — lives only in RAM | Temporary caches, secrets that should never touch disk |

This guide focuses on **named volumes** — bind mounts are covered in a separate guide.

---

## 3. Basic Named Volume Commands

```bash
docker volume create db-data      # create a volume
docker volume ls                   # list all volumes
docker volume inspect db-data      # see details: location, driver, labels
docker volume rm db-data           # delete a specific volume (fails if in use)
docker volume prune                # delete all unused volumes (careful!)
```

---

## 4. Example 1 — Basic Persistence with MySQL

This is the most common real-world use case: a database that shouldn't lose data.

### Step 1: Create the volume

```bash
docker volume create db-data
```

### Step 2: Run MySQL, mounting the volume to its data directory

```bash
docker run -d \
  --name db-container \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=mydb \
  -v db-data:/var/lib/mysql \
  mysql:8
```

`-v db-data:/var/lib/mysql` means: "mount the volume named `db-data` at the path `/var/lib/mysql` inside the container" — which happens to be exactly where MySQL stores its actual data files.

### Step 3: Add some data

```bash
docker exec -it db-container mysql -u root -prootpass mydb
```
```sql
CREATE TABLE notes (id INT AUTO_INCREMENT PRIMARY KEY, message VARCHAR(255));
INSERT INTO notes (message) VALUES ('This should survive!');
EXIT;
```

### Step 4: Destroy the container completely

```bash
docker stop db-container
docker rm db-container
```

The container is now **fully gone**. If the data were only inside the container, it would be lost forever.

### Step 5: Recreate the container, same volume

```bash
docker run -d \
  --name db-container \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=mydb \
  -v db-data:/var/lib/mysql \
  mysql:8
```

### Step 6: Confirm the data is still there

```bash
docker exec -it db-container mysql -u root -prootpass mydb -e "SELECT * FROM notes;"
```

Your row is still there — proof the volume kept the data independent of the container.

---

## 5. Example 2 — See Where a Volume Actually Lives

Volumes feel abstract because Docker hides the real path from you by default. Let's reveal it.

```bash
docker volume inspect db-data
```

Look for the `"Mountpoint"` field — something like:

```
/var/lib/docker/volumes/db-data/_data
```

That's the actual location on your host's filesystem where MySQL's data physically lives, even though you interacted with it purely through the name `db-data`.

---

## 6. Example 3 — Sharing One Volume Across Two Different Containers

Volumes aren't tied to a single container — two separate containers can mount the same volume at the same time.

```bash
docker volume create shared-data

docker run -d --name writer \
  -v shared-data:/data \
  busybox sh -c "while true; do date >> /data/log.txt; sleep 5; done"

docker run -it --name reader \
  -v shared-data:/data \
  busybox cat /data/log.txt
```

- `writer` continuously appends the current date/time to `/data/log.txt` every 5 seconds
- `reader` reads that same file from a **completely different container**, no network involved at all — just the shared volume

Run it again after waiting a bit:
```bash
docker start -ai reader
```
You'll see more lines than before, proving both containers are reading/writing the exact same underlying storage.

Clean up:
```bash
docker stop writer
docker rm writer reader
docker volume rm shared-data
```

---

## 7. Example 4 — Read-Only Volumes

Sometimes you want a container to see data but never be able to modify it — useful for shared config or reference data.

```bash
docker run -v db-data:/var/lib/mysql:ro mysql:8
```

Adding `:ro` after the container path makes the mount read-only. Any attempt by that container to write to `/var/lib/mysql` will fail.

---

## 8. Example 5 — Backing Up and Restoring a Volume

Since a volume isn't a simple folder you can casually `cp`, the standard approach is to spin up a temporary helper container that has access to both the volume and a host backup folder.

### Backup

```bash
mkdir -p ~/backup

docker run --rm \
  -v db-data:/data \
  -v ~/backup:/backup \
  busybox tar czf /backup/db-data-backup.tar.gz -C /data .
```

- `--rm` → automatically deletes this helper container once it finishes (it's just a temporary tool, not a real service)
- `-v db-data:/data` → mounts your real volume
- `-v ~/backup:/backup` → mounts a host folder to write the backup into
- `tar czf ... -C /data .` → compresses everything inside the volume into a `.tar.gz` file

Check the result:
```bash
ls -la ~/backup
```

### Restore (into a new, empty volume)

```bash
docker volume create db-data-restored

docker run --rm \
  -v db-data-restored:/data \
  -v ~/backup:/backup \
  busybox tar xzf /backup/db-data-backup.tar.gz -C /data
```

This extracts your backup into a fresh volume — useful for migrating data to a new machine, or recovering after a mistake.

---

## 9. Anonymous Volumes — Know Them, Avoid Them

```bash
docker run -d -v /var/lib/mysql mysql:8
```

No name before the colon — just a container path. Docker still creates a real volume, but with a random hash-like name (e.g. `a3f9c2e1d8b7...`). It persists just like a named volume, but:

- It's hard to reference later — you'd have to look it up with `docker volume ls`
- It gets silently abandoned ("dangling") the moment its container is removed, unless you explicitly run `docker rm -v` to also remove it

Almost always prefer named volumes over anonymous ones for anything you intend to keep track of.

---

## 10. Common Mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Forgetting `-v` entirely on a database container | Data vanishes on `docker rm` | Always mount a volume for stateful services |
| Using an anonymous volume by accident (forgetting the name before `:`) | Data persists, but under an unmemorable random name | Always write `volume-name:/path`, never just `/path` |
| Running `docker volume prune` without checking what's in use first | Can silently delete volumes not currently attached to a running container | Run `docker volume ls` and `docker ps -a` first; make sure nothing important is stopped-but-still-needed |
| Assuming `docker rm <container>` deletes its volumes | Volumes survive by default | Use `docker rm -v <container>` if you deliberately want the volume gone too — but be careful, this is permanent |
| Confusing volumes with bind mounts | Expecting to find data at a path you chose | Volumes live wherever Docker decides (check `Mountpoint` via `inspect`) — only bind mounts let you pick the host path |

---

## 11. Quick Command Reference

```bash
# Manage volumes
docker volume create <name>
docker volume ls
docker volume inspect <name>
docker volume rm <name>
docker volume prune

# Use a volume
docker run -v <volume-name>:<container-path> <image>
docker run -v <volume-name>:<container-path>:ro <image>   # read-only

# Backup a volume
docker run --rm -v <volume>:/data -v <host-backup-folder>:/backup \
  busybox tar czf /backup/backup.tar.gz -C /data .

# Restore a volume
docker run --rm -v <new-volume>:/data -v <host-backup-folder>:/backup \
  busybox tar xzf /backup/backup.tar.gz -C /data
```

---

## 12. Key Takeaway

A volume is Docker's answer to "where should this container's important data actually live, so it doesn't disappear the moment the container does?" Use named volumes for anything you want Docker to manage on your behalf — databases, persistent app state — and reach for bind mounts instead when you specifically need to control the exact host folder yourself (like live code editing).
