# Dockerfile — A Beginner's Guide

A Dockerfile is a plain text file containing step-by-step instructions that Docker reads to **build a custom image**. Each instruction creates a new layer in that image. This guide covers every core instruction, what it does, when it runs, and includes a hands-on practice exercise for each concept.

---

## 1. How a Dockerfile Works — The Big Picture

```
Dockerfile  --(docker build)-->  Image  --(docker run)-->  Container
```

- **Dockerfile**: the recipe (text instructions)
- **Image**: the packaged result of following that recipe (a read-only template)
- **Container**: a running instance of that image

Two important build-time vs run-time buckets:

| Phase | Instructions that apply |
|---|---|
| **Build time** (`docker build`) | `FROM`, `WORKDIR`, `COPY`, `ADD`, `RUN`, `ARG` |
| **Run time** (`docker run`) | `CMD`, `ENTRYPOINT` (defined at build time, executed at run time) |
| **Both** | `ENV`, `USER` |

---

## 2. Core Instructions

### `FROM` — the base image

```dockerfile
FROM python:3.11-slim
```

Every Dockerfile starts with `FROM`. It tells Docker which existing image to build on top of, instead of starting from a blank operating system. `python:3.11-slim` already has Python 3.11 installed on a minimal Linux base.

### `WORKDIR` — set the working directory

```dockerfile
WORKDIR /app
```

Creates (if needed) and switches into `/app` inside the image. Every instruction after this — `COPY`, `RUN`, `CMD` — is now relative to `/app`. Equivalent to `mkdir /app && cd /app`.

### `COPY` — copy files from host into image

```dockerfile
COPY app.py .
```

Copies `app.py` from your build folder (the "build context," where your Dockerfile lives) into the image, into the current `WORKDIR`. This is how your actual code gets baked into the image.

> `ADD` is similar but also supports fetching URLs and auto-extracting tar files. Stick with `COPY` unless you specifically need those extras.

### `RUN` — execute a command at build time

```dockerfile
RUN pip install flask
```

Runs a command *while building* the image, and saves the result as a permanent layer. Common use: installing packages.

### `ENV` — set an environment variable

```dockerfile
ENV FLASK_ENV=production
```

Sets a variable available both later in the build and inside any container started from the image.

### `EXPOSE` — document the port

```dockerfile
EXPOSE 5000
```

This is **documentation only**. It does not publish the port to your host machine — you still need `-p` on `docker run` for that. It just signals "this container expects to listen on port 5000."

### `ARG` — build-time-only variable

```dockerfile
ARG APP_VERSION=1.0
```

Exists only during `docker build`. It disappears once the image is built, unless you copy its value into an `ENV` variable:

```dockerfile
ARG APP_VERSION=1.0
ENV VERSION=$APP_VERSION
```

Override it at build time with:
```bash
docker build --build-arg APP_VERSION=2.5 -t myimage .
```

### `USER` — switch to a non-root user

```dockerfile
RUN useradd -m appuser
USER appuser
```

By default, everything in a container runs as `root`. Creating and switching to a regular user limits damage if the app is ever compromised. Everything after `USER` — including `CMD`/`ENTRYPOINT` at run time — executes as that user.

### `CMD` — default command (easily overridden)

```dockerfile
CMD ["python3", "app.py"]
```

Defines what runs when a container starts, **unless** the user overrides it:
```bash
docker run myimage python3 other.py   # replaces the whole CMD
```

### `ENTRYPOINT` — fixed command (hard to override)

```dockerfile
ENTRYPOINT ["python3", "greet.py"]
CMD ["stranger"]
```

`ENTRYPOINT` is the part that always runs. `CMD`, when paired with it, becomes the *default arguments*:

```bash
docker run myimage           # -> python3 greet.py stranger
docker run myimage Naim      # -> python3 greet.py Naim (CMD replaced, ENTRYPOINT stays)
```

To override even `ENTRYPOINT` itself:
```bash
docker run -it --entrypoint bash myimage
```

---

## 3. Quick Reference Table

| Instruction | Purpose | Runs at |
|---|---|---|
| `FROM` | Base image | Build |
| `WORKDIR` | Set working directory | Build |
| `COPY` | Copy files host → image | Build |
| `ADD` | Like COPY + URL/tar support | Build |
| `RUN` | Execute a command, save as layer | Build |
| `ARG` | Build-time-only variable | Build |
| `ENV` | Environment variable | Build & Run |
| `USER` | Switch active user | Build & Run |
| `EXPOSE` | Document a port (no real effect) | N/A |
| `CMD` | Default startup command (overridable) | Run |
| `ENTRYPOINT` | Fixed startup command | Run |

---

## 4. Practice Exercise 1 — Basics: `FROM`, `WORKDIR`, `COPY`, `CMD`

**Goal:** build and run your first image, and see `CMD` in action.

```bash
mkdir ~/dockerfile-practice1
cd ~/dockerfile-practice1
nano app.py
```

Paste into `app.py`:
```python
print("Hello from inside the container!")
```

```bash
nano Dockerfile
```

Paste into `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
CMD ["python3", "app.py"]
```

Build and run:
```bash
docker build -t hello-py .
docker images                 # confirm the image exists
docker run hello-py           # -> Hello from inside the container!
docker history hello-py       # see each instruction as a layer
docker run hello-py python3 -c "print('I overrode CMD!')"   # override CMD
```

**Try this:** run `docker ps -a` afterward. You'll notice the container shows `Exited (0)` — because the script finishes and exits immediately, there's no long-running process to keep it alive.

---

## 5. Practice Exercise 2 — `RUN`, `ENV`, `EXPOSE` (a real web server)

**Goal:** install a package at build time, set an environment variable, and expose a port for a Flask app that stays running.

```bash
mkdir ~/dockerfile-practice2
cd ~/dockerfile-practice2
nano app.py
```

Paste into `app.py`:
```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from Flask running inside Docker!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

> Note: `host="0.0.0.0"` lets connections reach Flask from outside the container. Leaving it as `127.0.0.1` would make it unreachable from your host machine.

```bash
nano Dockerfile
```

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask
ENV FLASK_ENV=production
EXPOSE 5000
CMD ["python3", "app.py"]
```

Build and run:
```bash
docker build -t flask-demo .
docker run -d -p 5000:5000 --name flask-container flask-demo
curl http://localhost:5000     # -> Hello from Flask running inside Docker!
docker ps                      # notice STATUS is "Up", not "Exited"
```

Go inside the running container (this works now because Flask keeps running):
```bash
docker exec -it flask-container bash
echo $FLASK_ENV      # -> production
exit
```

Clean up:
```bash
docker stop flask-container
docker rm flask-container
docker rmi flask-demo
```

---

## 6. Practice Exercise 3 — `ARG`, `USER`, `ENTRYPOINT`

**Goal:** pass a build-time variable into the image, run as a non-root user, and understand the ENTRYPOINT + CMD combo.

```bash
mkdir ~/dockerfile-practice3
cd ~/dockerfile-practice3
nano greet.py
```

```python
import sys
name = sys.argv[1] if len(sys.argv) > 1 else "stranger"
print(f"Hello, {name}! This is running as a non-root user.")
```

```bash
nano Dockerfile
```

```dockerfile
FROM python:3.11-slim

ARG APP_VERSION=1.0
ENV VERSION=$APP_VERSION

WORKDIR /app
COPY greet.py .

RUN useradd -m appuser
USER appuser

ENTRYPOINT ["python3", "greet.py"]
CMD ["stranger"]
```

Build with a custom `ARG` value:
```bash
docker build --build-arg APP_VERSION=2.5 -t greet-demo .
```

Run with default CMD:
```bash
docker run greet-demo
# -> Hello, stranger! This is running as a non-root user.
```

Override just the CMD portion (ENTRYPOINT stays fixed):
```bash
docker run greet-demo Naim
# -> Hello, Naim! This is running as a non-root user.
```

Override the ENTRYPOINT itself, to inspect the container manually:
```bash
docker run -it --entrypoint bash greet-demo
whoami          # -> appuser
echo $VERSION   # -> 2.5
exit
```

Clean up:
```bash
docker rmi greet-demo
```

---

## 7. Common Mistakes & Fixes

| Mistake | What happens | Fix |
|---|---|---|
| `docker rmf <id>` or `docker rm-f <id>` | `unknown command` error | It's two words: `docker rm -f <id>` (container) or `docker rmi -f <id>` (image) |
| Trying to `docker attach` a stopped container | `No such container` or nothing happens | `attach` only works on a *running* process. Use `docker logs <name>` to see past output instead |
| Container exits immediately after `docker run` | `STATUS: Exited (0)` | Normal if your script finishes fast (e.g. a `print` and exit). Only processes that keep running (servers, `sleep infinity`) stay "Up" |
| Using `EXPOSE` and expecting the port to work from the host | `curl: connection refused` | `EXPOSE` is documentation only — you still need `-p host:container` on `docker run` |
| App unreachable from host despite `-p` | Connection refused | Inside the app, bind to `0.0.0.0`, not `127.0.0.1` |
| Forgetting `.` at the end of `docker build -t name` | `"docker build" requires exactly 1 argument` | The `.` tells Docker where the build context (and Dockerfile) is — usually the current folder |

---

## 8. Cheat Sheet — Commands Used in This Guide

```bash
docker build -t <name> .                        # build image from Dockerfile
docker build --build-arg KEY=value -t <name> .   # build, overriding an ARG
docker images                                     # list images
docker run <image>                                # run a container
docker run -d -p HOST:CONTAINER --name X <image>  # run detached, with port mapping and a name
docker run -it --entrypoint bash <image>          # override entrypoint, get a shell
docker ps                                          # list running containers
docker ps -a                                       # list all containers (incl. stopped)
docker logs <container>                            # view a container's output
docker exec -it <container> bash                   # shell into a running container
docker history <image>                             # see image layers
docker stop <container>                            # stop a running container
docker rm <container>                               # remove a container
docker rmi <image>                                   # remove an image
```
