# Flask + MySQL on a Custom Docker Network — A Beginner's Project Guide

This guide documents a complete, real working project: two separate Docker containers (a **Flask web app** and a **MySQL database**) that live on their own custom network, talk to each other by name, persist data through a volume, and are finally packaged into a single `docker compose.yml`. Every command below was actually run and tested, in order.

---

## 1. The Goal

Build two containers that can communicate with each other:
- **Flask container** — a small web app with a form to save notes
- **MySQL container** — stores those notes in a database

Both containers sit on the same **custom Docker network**, so Flask can reach MySQL simply by using its **container name** as the hostname — no manual IP addresses required.

---

## 2. Project Folder Structure

```
flask-db-app/
├── compose.yml
└── flask-app/
    ├── app.py
    └── Dockerfile
```

---

## 3. Phase 1 — Create a Custom Network

Docker doesn't require you to manually assign IP addresses. Instead, you create a **custom bridge network**, and Docker automatically:
- Assigns each connected container its own IP
- Lets containers reach each other **by name** using built-in DNS

### Commands

```bash
docker network create myapp-network
```
Creates the network.

```bash
docker network ls
```
Lists all networks, confirming `myapp-network` exists.

```bash
docker network inspect myapp-network
```
Shows details — including the auto-assigned subnet (e.g. `172.20.0.0/16`) and, once containers join, their individual IPs.

---

## 4. Phase 2 — Build and Run the Flask Container

### `flask-app/app.py` (final version, with form + database)

```python
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

db_config = {
    "host": "db-container",
    "user": "flaskuser",
    "password": "flaskpass",
    "database": "mydb"
}

def get_connection():
    return mysql.connector.connect(**db_config)

def ensure_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message VARCHAR(255)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        message = request.form.get("message")
        if message:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (message) VALUES (%s)", (message,))
            conn.commit()
            cursor.close()
            conn.close()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, message FROM notes ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    rows_html = "".join(f"<li>#{r[0]}: {r[1]}</li>" for r in rows)

    return f"""
    <h2>Add a note</h2>
    <form method="POST">
        <input type="text" name="message" placeholder="Type something...">
        <button type="submit">Save</button>
    </form>
    <h3>Saved notes:</h3>
    <ul>{rows_html}</ul>
    """

if __name__ == "__main__":
    ensure_table()
    app.run(host="0.0.0.0", port=5000)
```

**Key detail:** `"host": "db-container"` uses the **container name**, not an IP address. This only works because both containers are on the same custom network — this is the entire point of Phase 1.

### `flask-app/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask mysql-connector-python
EXPOSE 5000
CMD ["python3", "app.py"]
```

| Instruction | What it does |
|---|---|
| `FROM python:3.11-slim` | Start from a minimal image with Python 3.11 preinstalled |
| `WORKDIR /app` | Set `/app` as the working directory inside the image |
| `COPY app.py .` | Copy your app code into the image |
| `RUN pip install ...` | Install Flask and the MySQL connector at build time |
| `EXPOSE 5000` | Documents the port the app listens on (does not publish it — that's `-p`) |
| `CMD [...]` | Default command run when the container starts |

### Build and run manually (before Compose)

```bash
cd flask-app
docker build -t flask-app .
```
Builds the image from the Dockerfile in the current folder.

```bash
docker run -d \
  --name flask-container \
  --network myapp-network \
  -p 5000:5000 \
  flask-app
```
- `-d` → run in the background
- `--name flask-container` → this name is what MySQL/other containers use to reach it
- `--network myapp-network` → joins the custom network from Phase 1
- `-p 5000:5000` → publishes the port so *you* (on the host) can reach it in a browser

### Test it

```bash
curl http://localhost:5000
```

---

## 5. Phase 3 — Add the MySQL Container

```bash
docker run -d \
  --name db-container \
  --network myapp-network \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=mydb \
  -e MYSQL_USER=flaskuser \
  -e MYSQL_PASSWORD=flaskpass \
  mysql:8
```

| Flag | What it does |
|---|---|
| `--network myapp-network` | Same network as Flask — this is what lets them talk |
| `MYSQL_ROOT_PASSWORD` | Password for the MySQL `root` admin user |
| `MYSQL_DATABASE` | Auto-creates a database named `mydb` on first startup |
| `MYSQL_USER` / `MYSQL_PASSWORD` | Creates a non-root user Flask connects as |

**No `-p` flag here on purpose** — MySQL doesn't need to be reachable from outside Docker, only from `flask-container` over the internal network. This is good security practice.

### Confirm it started correctly

```bash
docker logs -f db-container
```
Wait for a line like `ready for connections`, then `Ctrl+C` to stop watching (this doesn't stop the container).

### Confirm both containers are on the network

```bash
docker network inspect myapp-network
```
Both `flask-container` and `db-container` should appear under `"Containers"`, each with their own IP.

### Prove DNS name resolution works

```bash
docker exec -it flask-container bash
getent hosts db-container
exit
```
This should return `db-container`'s IP — proof Docker's internal DNS resolves the name.

---

## 6. Phase 4 — Connect Flask to MySQL for Real

A `/dbtest` route was added first to sanity-check the connection:

```python
@app.route("/dbtest")
def dbtest():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        return f"Connected to MySQL! Version: {version[0]}"
    except Exception as e:
        return f"Connection failed: {e}"
```

After rebuilding and recreating the Flask container:

```bash
docker build -t flask-app .
docker stop flask-container
docker rm flask-container
docker run -d --name flask-container --network myapp-network -p 5000:5000 flask-app
```

```bash
curl http://localhost:5000/dbtest
# Connected to MySQL! Version: 8.4.11
```

This confirmed real cross-container communication — Flask reached MySQL purely by container name.

---

## 7. Phase 5 — Persist Data with a Volume

Without a volume, deleting `db-container` deletes all its data permanently, since the data lives inside the container's writable layer.

### Create a named volume

```bash
docker volume create db-data
```

### Recreate the DB container, mounting the volume

```bash
docker stop db-container
docker rm db-container

docker run -d \
  --name db-container \
  --network myapp-network \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=mydb \
  -e MYSQL_USER=flaskuser \
  -e MYSQL_PASSWORD=flaskpass \
  -v db-data:/var/lib/mysql \
  mysql:8
```

`-v db-data:/var/lib/mysql` maps the volume to MySQL's actual data directory. Now the data lives in the volume, independent of the container's lifecycle.

### Proof of persistence

```bash
docker stop db-container
docker rm db-container
# recreate with the same -v db-data:/var/lib/mysql flag
```

After recreating from scratch, previously saved notes were still present — confirming the volume works.

---

## 8. Phase 6 — Build a Real Input Form

The Flask app's `/` route was updated (see full code in section 4) to:
1. Show an HTML form (`GET` request)
2. Accept a submitted value and `INSERT` it into MySQL (`POST` request)
3. Immediately query and display all saved notes below the form

Tested first with `curl` (simulating a form submission):

```bash
curl -X POST -d "message=My first saved note" http://localhost:5000
```

Then confirmed directly in a browser at `http://localhost:5000` — typing a note and clicking **Save** stored it in MySQL and displayed it in the list.

---

## 9. Phase 7 — Package Everything into Docker Compose

Instead of remembering multiple `docker run` commands, Compose describes the whole stack in one file.

### `compose.yml`

```yaml
services:
  flask-app:
    build: ./flask-app
    container_name: flask-container
    ports:
      - "5000:5000"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - myapp-network

  db:
    image: mysql:8
    container_name: db-container
    environment:
      - MYSQL_ROOT_PASSWORD=rootpass
      - MYSQL_DATABASE=mydb
      - MYSQL_USER=flaskuser
      - MYSQL_PASSWORD=flaskpass
    volumes:
      - db-data:/var/lib/mysql
    networks:
      - myapp-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-prootpass"]
      interval: 5s
      timeout: 5s
      retries: 10

networks:
  myapp-network:
    external: true

volumes:
  db-data:
    external: true
```

### Key parts explained

| Section | What it means |
|---|---|
| `build: ./flask-app` | Build the Flask image from the Dockerfile in that subfolder |
| `container_name` | Gives predictable names instead of auto-generated ones |
| `depends_on: db: condition: service_healthy` | Wait for MySQL to actually be *ready*, not just started, before starting Flask |
| `healthcheck` | Runs `mysqladmin ping` repeatedly until MySQL responds, so `depends_on` has something real to check |
| `networks: myapp-network: external: true` | Reuse the network created in Phase 1 instead of making a new one |
| `volumes: db-data: external: true` | Reuse the existing volume, so previously saved notes aren't lost |

### Why the healthcheck matters

Without it, `depends_on` only waits for the **container to start**, not for MySQL to actually **finish initializing**. Since MySQL takes a few seconds to become ready, Flask could start too early and crash trying to connect — which is exactly what happened during testing before the healthcheck was added.

### Bring the whole stack up

```bash
docker compose up -d
```
Builds the Flask image (if needed) and starts both containers, connected to the existing network and volume.

### Check status

```bash
docker compose ps
```

### View logs for a specific service

```bash
docker compose logs flask-app
```

### Tear down and bring back up

```bash
docker compose down
docker compose up -d
```
One command stops everything; one command brings it all back — correctly networked, in the right startup order.

---

## 10. Full Command Reference

```bash
# Networking
docker network create myapp-network
docker network ls
docker network inspect myapp-network

# Volumes
docker volume create db-data
docker volume ls

# Building & running manually
docker build -t flask-app .
docker run -d --name flask-container --network myapp-network -p 5000:5000 flask-app
docker run -d --name db-container --network myapp-network \
  -e MYSQL_ROOT_PASSWORD=rootpass -e MYSQL_DATABASE=mydb \
  -e MYSQL_USER=flaskuser -e MYSQL_PASSWORD=flaskpass \
  -v db-data:/var/lib/mysql mysql:8

# Inspecting
docker ps
docker ps -a
docker logs -f db-container
docker exec -it flask-container bash
getent hosts db-container

# Testing
curl http://localhost:5000
curl http://localhost:5000/dbtest
curl -X POST -d "message=Hello" http://localhost:5000

# Cleanup
docker stop flask-container db-container
docker rm flask-container db-container
docker rmi flask-app

# Compose
docker compose up -d
docker compose ps
docker compose logs flask-app
docker compose down
```

---

## 11. What This Project Demonstrates

- **Custom networking** — containers found each other by name via Docker's built-in DNS, not hardcoded IPs
- **Dockerfile fundamentals** — `FROM`, `WORKDIR`, `COPY`, `RUN`, `EXPOSE`, `CMD`
- **Environment variables** — configuring MySQL entirely through `-e` flags
- **Volumes** — data survived full container deletion and recreation
- **Security practice** — the database was never exposed to the host or outside world, only reachable internally
- **A real full-stack flow** — browser → Flask route → MySQL query → response rendered back to the browser
- **Docker Compose** — the entire manual setup collapsed into a single declarative file, with a proper startup-order guarantee via healthchecks
