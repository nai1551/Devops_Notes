# Docker Compose from Scratch — Network, Volume & Service Names Explained

This is a complete walkthrough of a small project built to understand Docker Compose from the ground up: a Flask web page that counts visits, backed by Redis. Every concept — networking, volumes, service-name communication — is introduced one at a time before being combined into the final working app.

---

## 1. What Problem Compose Actually Solves

Without Compose, running two connected containers means typing several separate commands:

```bash
docker network create mynet
docker volume create mydata
docker run -d --name cache --network mynet -v mydata:/data redis:alpine
docker run -d --name web --network mynet -p 8081:5000 myimage
```

Docker Compose lets you describe all of this **once**, in a single YAML file, and bring the whole thing up with one command: `docker compose up -d`.

---

## 2. Project Structure

```
compose-practice/
├── compose.yml
└── counter-app/
    ├── app.py
    └── Dockerfile
```

---

## 3. Step 1 — The Simplest Possible Compose File

Before anything else, confirm Compose can run even a single container.

```bash
mkdir -p ~/compose-practice
cd ~/compose-practice
nano compose.yml
```

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8081:80"
```

**In plain English:** "Run one thing, call it `web`, use the `nginx:alpine` image, and let me reach it on port 8081."

```bash
docker compose up -d
docker compose ps
curl http://localhost:8081
```

You should see Nginx's default welcome page.

### The hidden detail worth noticing

```bash
docker network ls
```

You'll see an entry like `compose-practice_default` — **you never typed `docker network create`**. Compose automatically creates one network per project, named after the folder. This is the first big idea: networking exists by default with Compose, you only need to configure it if you want something custom.

```bash
docker compose down
```

---

## 4. Step 2 — Two Containers, Found Automatically by Name

```bash
nano compose.yml
```

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8081:80"

  cache:
    image: redis:alpine
```

A second service, `cache`, running Redis. No networking config written anywhere.

```bash
docker compose up -d
docker compose exec web sh
```

Inside the container:
```bash
getent hosts cache
```
(Use this instead of `ping` — many minimal images like Alpine don't include `ping`.)

```bash
exit
```

You'll get back a real IP address for `cache`. **This is Compose's built-in DNS**: every service name in the file automatically becomes a reachable hostname for every other service in that same file — zero configuration required. This is the same mechanism you'd get from `docker network create` + `--network` flags manually, just automatic.

```bash
docker compose down
```

---

## 5. Step 3 — Taking Control: a Named, Custom Network

The automatic network works, but sometimes you want to name and configure it yourself.

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8081:80"
    networks:
      - my_custom_net

  cache:
    image: redis:alpine
    networks:
      - my_custom_net

networks:
  my_custom_net:
    driver: bridge
```

**What changed:** each service now lists which network(s) it belongs to, and a top-level `networks:` block actually defines `my_custom_net` (using `bridge`, the standard type you've used with `docker network create` before).

```bash
docker compose up -d
docker network ls
```

Now you'll see `compose-practice_my_custom_net` — a name you chose, instead of the generic auto-generated one.

```bash
docker compose exec web sh
getent hosts cache
exit
```

Same result as Step 2 — the behavior is identical. This step is purely about understanding that the invisible default network and this explicit one do the exact same job; you've just taken control of its name and settings.

```bash
docker compose down
```

---

## 6. Step 4 — Adding a Volume So Data Survives Teardown

Right now, anything Redis stores disappears the moment you run `docker compose down`. Let's fix that.

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8081:80"
    networks:
      - my_custom_net

  cache:
    image: redis:alpine
    networks:
      - my_custom_net
    volumes:
      - redis-data:/data
    command: redis-server --save 60 1

networks:
  my_custom_net:
    driver: bridge

volumes:
  redis-data:
```

### What's new, explained

- **`volumes: - redis-data:/data`** (under `cache`) — mounts a named volume called `redis-data` to `/data` inside the container, exactly where Redis keeps its data files. Same pattern as `db-data:/var/lib/mysql` used for MySQL.
- **`command: redis-server --save 60 1`** — by default, this lightweight Redis setup doesn't automatically persist to disk. This tells it: "save to disk every 60 seconds if at least 1 key changed." Without this, there'd be nothing in the volume to actually test.
- **`volumes: redis-data:`** (top-level, bottom of file) — declares the named volume so Compose creates and manages it.

```bash
docker compose up -d
```

### Test persistence, step by step

```bash
docker compose exec cache redis-cli SET mykey "hello volume"
```
`redis-cli` is Redis's own command-line tool. This stores a value under the key `mykey`.

```bash
docker compose exec cache redis-cli GET mykey
```
Confirms it exists right now — should print `"hello volume"`.

```bash
docker compose exec cache redis-cli SAVE
```
Forces an immediate write to disk, rather than waiting up to 60 seconds for the automatic save. **This step is essential** — skipping it means the data still only lives in memory and could be lost if you tear the container down before the timer fires.

```bash
docker compose down
```
Removes the containers completely.

```bash
docker compose up -d
docker compose exec cache redis-cli GET mykey
```

If this prints `"hello volume"` again, the volume genuinely kept the data safe through a full teardown and recreation.

```bash
docker compose down
```

---

## 7. Step 5 — Combining Everything Into a Real App

Now build something that actually **uses** all three ideas together (service-name networking, a custom network, and a persistent volume), instead of testing them in isolation.

### The app itself

```bash
mkdir -p ~/compose-practice/counter-app
cd ~/compose-practice/counter-app
nano app.py
```

```python
from flask import Flask
import redis

app = Flask(__name__)
r = redis.Redis(host="cache", port=6379, decode_responses=True)

@app.route("/")
def home():
    count = r.incr("visits")
    return f"This page has been visited {count} times."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

- `host="cache"` — the service name again, same pattern as `"db-container"` in earlier projects.
- `r.incr("visits")` — tells Redis "add 1 to whatever number is stored under the key `visits`, and give me the new total." Redis handles the counting; the app doesn't track state itself.

### The Dockerfile

```bash
nano Dockerfile
```

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask redis
EXPOSE 5000
CMD ["python3", "app.py"]
```

Same familiar pattern as every Dockerfile built so far.

### The final Compose file

```bash
cd ~/compose-practice
nano compose.yml
```

```yaml
services:
  web:
    build: ./counter-app
    ports:
      - "8081:5000"
    depends_on:
      - cache
    networks:
      - my_custom_net

  cache:
    image: redis:alpine
    networks:
      - my_custom_net
    volumes:
      - redis-data:/data
    command: redis-server --save 60 1

networks:
  my_custom_net:
    driver: bridge

volumes:
  redis-data:
```

**What's genuinely new:** `build: ./counter-app` instead of `image: nginx:alpine`. Since this is your own code, Compose needs to build an image from the `Dockerfile` in that subfolder first, rather than pulling a ready-made image from Docker Hub. `depends_on: - cache` tells Compose to start `cache` before `web`, so the app doesn't try connecting to Redis before it exists.

---

## 8. Bringing It All Up

```bash
docker compose up -d
```

This does more work than before: builds the Flask image, creates the network and volume if they don't exist, and starts both containers in the right order.

```bash
docker compose ps
```

Confirm both `web` and `cache` show as running.

```bash
curl http://localhost:8081
curl http://localhost:8081
curl http://localhost:8081
```

Expected: the count increases each time — `1`, `2`, `3`. This single result proves everything at once: `web` found `cache` by its service name, the count is being stored via Redis, and it's all happening over the custom network.

---

## 9. Proving Persistence in the Full App

```bash
docker compose down
docker compose up -d
curl http://localhost:8081
```

If the volume is working correctly, the count should **continue** from where it left off — not reset to `1` — because `redis-data` kept the stored number safe through the full teardown, exactly like the isolated test in Section 6.

---

## 10. Full Command Reference

```bash
# Bring the stack up / down
docker compose up -d
docker compose down

# Check status
docker compose ps

# Run a command inside a running service
docker compose exec <service-name> sh
docker compose exec cache redis-cli SET mykey "value"
docker compose exec cache redis-cli GET mykey
docker compose exec cache redis-cli SAVE

# Inspect what Compose created automatically
docker network ls
docker volume ls

# DNS check between services (inside a container)
getent hosts <other-service-name>
```

---

## 11. What Each Piece Actually Does — Quick Reference

| Compose concept | What it means | Where it appeared |
|---|---|---|
| `services:` | Each entry becomes one container | Every step |
| Automatic network | Compose creates one network per project by default | Step 1 |
| Service-name DNS | Every service is reachable by its name from any other service in the file | Step 2 |
| `networks:` (per service + top-level) | Explicitly name and configure the network instead of using the automatic one | Step 3 |
| `volumes:` (per service + top-level) | Persist data outside the container's lifecycle | Step 4 |
| `build:` vs `image:` | `build` compiles your own Dockerfile; `image` pulls a ready-made one | Step 5 |
| `depends_on:` | Controls startup order (not readiness — just "starts after") | Step 5 |

---

## 12. Key Takeaway

Docker Compose isn't a new concept — it's the same networking, volumes, and container basics you already know, just described declaratively in one file instead of typed as a sequence of `docker run` commands. Once a service is listed in `compose.yml`, its name automatically becomes a working hostname for every other service in that file — that single fact is what makes multi-container apps in Compose so much simpler than wiring them together by hand.
