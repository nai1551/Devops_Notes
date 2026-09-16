# Docker Bind Mounts — A Beginner's Guide

A bind mount connects a **specific folder on your host machine** directly to a folder **inside a container**. Whatever's in that host folder appears inside the container in real time — and it works both ways: edit a file from the host, the container sees it instantly; edit it from inside the container, the host sees it too.

---

## 1. Bind Mount vs Named Volume

You've likely already used a **named volume** (e.g. for a MySQL database). A bind mount solves a different problem.

| | Named Volume | Bind Mount |
|---|---|---|
| Who picks the storage location? | Docker decides (hidden path, usually under `/var/lib/docker/volumes/`) | **You** decide — any folder you choose |
| How you reference it | By name: `db-data:/var/lib/mysql` | By real path: `~/bind-demo/site:/usr/share/nginx/html` |
| Typical use | Databases, app state Docker should manage for you | Live code editing, config files, sharing files you want direct access to |
| Live sync | Yes | Yes |
| Survives container removal | Yes (volume persists independently) | Yes (it's just a folder on your host — was never "inside" the container's lifecycle to begin with) |

---

## 2. Why It Matters

Without a bind mount, changing a file inside a container normally means:

```
edit file → rebuild image → stop old container → run new container
```

That's the cycle you go through every time you update application code baked in with `COPY`.

A bind mount skips all of that for development — you edit the file on your host with a normal text editor, and the running container sees the change immediately. No rebuild, no restart. This is exactly how "live reload" development setups work.

---

## 3. The Syntax

```bash
docker run -v <host_path>:<container_path> <image>
```

- `<host_path>` → an absolute or `~`-relative path on your machine
- `<container_path>` → the path inside the container where that folder should appear
- Everything already at `<container_path>` inside the image gets **replaced** (hidden, not deleted) by whatever's in `<host_path>` while the mount is active

---

## 4. Practice: See a Live Change Without Rebuilding

### Step 1: Create a folder and a custom HTML file on the host

```bash
mkdir -p ~/bind-demo/site
cd ~/bind-demo/site
nano index.html
```

Paste in:

```html
<!DOCTYPE html>
<html>
<head><title>Bind Mount Test</title></head>
<body>
  <h1>Version 1 — served from the host</h1>
</body>
</html>
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

### Step 2: Run Nginx, bind-mounting your folder in

```bash
docker run -d \
  --name nginx-bind \
  -p 8081:80 \
  -v ~/bind-demo/site:/usr/share/nginx/html \
  nginx:alpine
```

- `-v ~/bind-demo/site:/usr/share/nginx/html` → the bind mount. This replaces Nginx's built-in HTML folder with your folder.
- `-p 8081:80` → publishes the container's port 80 to your host's port 8081, so your browser can reach it.

### Step 3: Confirm it's serving your file

Open in a browser:

```
http://localhost:8081
```

Expected: **"Version 1 — served from the host"** — proving Nginx is reading your file, not its own default welcome page.

If you still see the default Nginx page, check the mount worked:
```bash
docker exec -it nginx-bind sh
ls /usr/share/nginx/html
exit
```
It should show only your `index.html`, not the original `index.html` + `50x.html` the image ships with.

### Step 4: Edit the file on the host — no Docker commands involved

```bash
nano ~/bind-demo/site/index.html
```

Change the heading:

```html
<h1>Version 2 — updated live, no rebuild!</h1>
```

Save and exit.

### Step 5: Just refresh the browser

No `docker restart`, no `docker build` — just refresh `http://localhost:8081`.

Expected: the page immediately shows **"Version 2 — updated live, no rebuild!"** — this instant update is the entire point of a bind mount.

### Step 6 (bonus): Prove the reverse direction — container to host

```bash
docker exec -it nginx-bind sh
echo "<h1>Version 3 — written from inside the container</h1>" > /usr/share/nginx/html/index.html
exit
```

Now check the file **on the host**:

```bash
cat ~/bind-demo/site/index.html
```

Expected: it shows "Version 3" too — proving changes sync in both directions, not just host → container.

### Step 7: Clean up

```bash
docker stop nginx-bind
docker rm nginx-bind
```

Note: `~/bind-demo` and its contents remain untouched on your host. A bind mount is just a live link to a folder you already own — removing the container never deletes it.

---

## 5. Common Mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Using a relative path without `~` or `$(pwd)` | Docker may fail to find the folder or mount the wrong thing | Use `~/path` or `$(pwd)/path` for clarity, always an absolute path in practice |
| Expecting `EXPOSE` to publish the bind-mounted content externally | Page unreachable in browser | You still need `-p host:container` — bind mounts handle *files*, not networking |
| Editing the file expecting a rebuild is needed | Confusion when nothing seems to update | Bind mounts sync live — just refresh, no rebuild required |
| Mounting over a folder the image needs (e.g. accidentally mounting an empty folder over `/app` where your code lives) | App can't find its files, crashes | Make sure your host folder actually contains what the container expects at that path |

---

## 6. Quick Command Reference

```bash
# Run a container with a bind mount
docker run -d --name <name> -p <host_port>:<container_port> \
  -v <host_path>:<container_path> <image>

# Check what's mounted where
docker exec -it <container> sh

# Confirm host-side changes
cat <host_path>/<file>

# Clean up (bind-mounted folder is untouched by this)
docker stop <container>
docker rm <container>
```

---

## 7. Key Takeaway

A bind mount is best thought of as **"let this container look through a window into a folder I already control on my machine."** It's ideal for active development, config files you want to tweak without rebuilding, and log files you want to inspect directly from the host. For data a container should own and manage on its own (like a database), a named volume is usually the better fit.
