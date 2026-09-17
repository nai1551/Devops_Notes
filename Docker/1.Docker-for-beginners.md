# Docker for Beginners

A simple, story-driven guide to understanding what Docker is, why it exists, and how it works.

---

## 1. The problem that existed before Docker

Imagine you're a developer. You build an app on your laptop. It works perfectly. You send it to your teammate — and it breaks on their machine. You deploy it to a server — and it breaks there too.

Why does this happen? Because your laptop, your teammate's laptop, and the server are all slightly different:

- Different operating system versions
- Different versions of Python, Node, Java, etc.
- Different installed libraries
- Different configuration files and environment variables

This became known as the classic developer complaint:

> "But it works on my machine!"

Every environment — your laptop (development), the testing server (staging), and the live server (production) — behaved a little differently, and those small differences caused constant, frustrating bugs.

---

## 2. The old fix: Virtual Machines (VMs)

Before Docker, the standard solution was **Virtual Machines**.

A VM packages an entire operating system — kernel, drivers, everything — along with your app, so it behaves identically no matter where you run it.

This worked, but it was heavy:

- Each VM contains a **full guest operating system** (several gigabytes)
- Booting a VM can take **minutes**
- Running many VMs on one server uses a huge amount of CPU and RAM, because each one duplicates the entire OS

At the same time, software design was shifting toward **microservices** — instead of one giant application, teams started building many small, independent services (an auth service, a payment service, a notifications service, etc.). Needing a separate isolated environment for every one of these services made the VM overhead problem even worse.

---

## 3. The building blocks already existed

The Linux kernel already had low-level features that could isolate processes *without* needing a full separate operating system:

- **Namespaces** — control what a process can "see" (its own filesystem, network, list of other processes, etc.)
- **cgroups (control groups)** — limit how much CPU, memory, and disk a process is allowed to use

Technologies like `chroot` and **LXC (Linux Containers)** already used these features, and companies like Google used similar internal systems (like Borg) to run software at massive scale.

The problem? These tools were powerful but hard to use. There was no simple, friendly way for an everyday developer to package an app and share it with a teammate.

---

## 4. Docker enters the story (2013)

A company called **dotCloud** (which later renamed itself **Docker, Inc.**), led by **Solomon Hykes**, took these existing Linux kernel features and built a simple, developer-friendly layer on top of them.

Docker introduced:

| Docker introduced... | What it does |
|---|---|
| **Dockerfile** | A simple text file describing how to build an environment |
| **Images** | Portable, shareable snapshots of an app + everything it needs |
| **Docker Hub** | A public registry to share images — like GitHub, but for containers |
| **Docker CLI** | Simple commands like `docker build`, `docker run`, `docker push` |

It was released as open source in **2013** and spread through the developer world extremely fast, because for the first time, containers were easy enough for *any* developer to use — not just infrastructure engineers at Google-scale companies.

---

## 5. Containers vs Virtual Machines

This is the core idea that makes Docker different from a VM.

```
┌───────────────── Virtual Machines ─────────────────┐   ┌────────────────── Containers ──────────────────┐
│                                                      │   │                                                  │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐           │   │   ┌───────┐   ┌───────┐   ┌───────┐             │
│   │   App   │   │   App   │   │   App   │           │   │   │  App  │   │  App  │   │  App  │             │
│   │Guest OS │   │Guest OS │   │Guest OS │           │   │   └───────┘   └───────┘   └───────┘             │
│   └─────────┘   └─────────┘   └─────────┘           │   │                                                  │
│   ───────────────────────────────────────           │   │   ───────────────────────────────────────       │
│               Hypervisor                            │   │              Docker Engine                      │
│   ───────────────────────────────────────           │   │   ───────────────────────────────────────       │
│                Host OS                               │   │               Host OS                           │
│   ───────────────────────────────────────           │   │   ───────────────────────────────────────       │
│              Infrastructure                          │   │             Infrastructure                      │
└──────────────────────────────────────────────────────┘   └──────────────────────────────────────────────────┘
```

**Virtual Machines** — each app carries its *own* full guest operating system. Heavy, slow to start.

**Containers** — all apps share *one* host operating system through the Docker Engine. Each container only carries the app and its dependencies — nothing more.

This is why containers:
- Start in **milliseconds** instead of minutes
- Take up **megabytes** instead of gigabytes
- Let you run **far more** of them on the same server

---

## 6. Docker host in detail: build, pull, and run

Zooming in on the Docker host, here's what actually happens when you run the three most common commands.

```
   Client                    Docker host                       Registry
 ┌───────────┐        ┌─────────────────────────┐         ┌───────────────┐
 │docker build│┄┄┄┄┄┄▶│      Docker Daemon        │         │  (Docker Hub) │
 │docker pull │──────▶│  ┌───────────┐┌─────────┐ │         │   Ubuntu      │
 │docker run  │──────▶│  │Containers ││ Images  │◀┼────────▶│   OpenStack   │
 └───────────┘        │  │  [ ]  [ ] ││ Ubuntu  │ │         │   Nginx       │
                       │  └───────────┘│ Nginx   │ │         └───────────────┘
                       │               └─────────┘ │
                       └─────────────────────────┘

   ┄┄┄  Build       ──  Pull       ▶▶  Run
```

- **`docker build`** — the client tells the daemon to build a new image from a Dockerfile, right there on the host.
- **`docker pull`** — the client tells the daemon to fetch a ready-made image from the registry (Docker Hub) and store it locally.
- **`docker run`** — the daemon takes an image (built or pulled) and starts it as a running container.

---

## 7. What's really inside the Docker Engine

"Docker daemon" is actually a stack of smaller programs, each handling one job. Here's the full chain from the command you type down to the actual running container:

```
                 ┌──────────────┐
                 │ Docker client│── Docker commands (CLI)
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │ Docker daemon│── REST API & other features
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │  containerd  │── Container lifecycle mgmt:
                 └───┬───┬───┬──┘   start, stop, pause, delete
                     │   │   │
              ┌──────┘   │   └──────┐
              ▼          ▼          ▼
           ┌─────┐    ┌─────┐    ┌─────┐
           │Shim │    │Shim │    │Shim │  ── one per container, enables
           └──┬──┘    └──┬──┘    └──┬──┘     "daemonless" containers
              ▼          ▼          ▼
           ┌─────┐    ┌─────┐    ┌─────┐
           │runc │    │runc │    │runc │   ── talks to the Linux kernel
           └──┬──┘    └──┬──┘    └──┬──┘      (namespaces & cgroups)
              ▼          ▼          ▼
          [Container][Container][Container] ── the actual running processes
```

Each layer has exactly one job:

- **Docker client** — where you type commands like `docker run`.
- **Docker daemon** — exposes the REST API and coordinates everything.
- **containerd** — manages the full lifecycle of containers: starting, stopping, pausing, deleting.
- **shim** — a small helper process, one per container, that lets containers keep running even if the daemon restarts. This is what makes containers "daemonless."
- **runc** — the low-level runtime that actually talks to the Linux kernel (namespaces and cgroups) to create the isolated container.

---

## 8. The core Docker concepts

### Dockerfile
A plain text file with step-by-step instructions for building an environment. Example idea (not exact syntax):

```
Start from a base Linux system
Install Python
Copy my application code into the image
Run this app when the container starts
```

### Image
Built from a Dockerfile using `docker build`. An image is:
- **Read-only** — it doesn't change once built
- **Layered** — each instruction in the Dockerfile adds a layer, and Docker reuses layers it has already built, which makes builds fast
- **Portable** — the same image runs identically on any machine with Docker installed

### Container
A **running instance** of an image, started with `docker run`. Think of it like this:

> Image is the *recipe*. Container is the *meal* made from that recipe.

You can start many containers from the same image, and each one is isolated from the others.

### Registry (e.g. Docker Hub)
A place to store and share images, similar to how GitHub stores code.
- `docker push` — upload your image to the registry
- `docker pull` — download an image from the registry

---

## 9. How it all fits together

```
   Dockerfile
       │
       │  docker build
       ▼
     Image  ───────push / pull───────►  Registry (Docker Hub)
       │
       │  docker run
       ▼
   Container
```

1. You write a **Dockerfile**.
2. `docker build` turns it into an **Image**.
3. `docker run` starts a **Container** from that image.
4. You can **push** the image to a **Registry** so others can **pull** and run the exact same environment.

### What happens under the hood when you run `docker run`

1. You type `docker run` in the terminal — this is the **Docker CLI** (the client).
2. The CLI sends the request to the **Docker daemon** (`dockerd`), which runs in the background.
3. The daemon checks if the image exists locally. If not, it **pulls** it from a registry.
4. The daemon creates a new container using:
   - **Namespaces** → isolates what the container can see (its own filesystem, network, processes)
   - **cgroups** → limits how much CPU/memory/disk the container can use
5. Your app starts running inside that isolated container.

---

## 10. Why Docker actually matters

| Benefit | What it means |
|---|---|
| **Consistency** | The exact same image runs on your laptop, in testing, and in production. No more "works on my machine." |
| **Speed** | Containers start in milliseconds, not minutes. |
| **Density** | You can run far more containers than VMs on the same hardware. |
| **Portability** | An image runs the same way on any machine with Docker installed, regardless of the underlying OS. |
| **Enabled microservices** | Teams can package each small service independently and run them together — often using **Docker Compose** for local multi-container setups, or **Kubernetes** for large-scale orchestration in production. |

---

## 11. Quick glossary

| Term | Meaning |
|---|---|
| **Dockerfile** | Text file with build instructions |
| **Image** | A built, read-only snapshot of an app + its environment |
| **Container** | A running instance of an image |
| **Docker Engine / daemon** | The background service that builds and runs containers |
| **Docker CLI** | The command-line tool you type commands into |
| **Registry (Docker Hub)** | Where images are stored and shared |
| **containerd** | Manages each container's full lifecycle — start, stop, pause, delete |
| **shim** | One per container; keeps it running even if the daemon restarts |
| **runc** | Low-level runtime that talks directly to the Linux kernel to create the container |
| **Namespace** | Linux feature that isolates what a process can see |
| **cgroup** | Linux feature that limits resources (CPU, memory) a process can use |

---

## 12. One-line summary

> Docker is a tool that packages an application together with everything it needs to run, into a lightweight, portable "container" — so it behaves exactly the same anywhere it's deployed, without the heavy overhead of a full virtual machine.
