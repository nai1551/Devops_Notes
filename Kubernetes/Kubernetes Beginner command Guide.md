# Kubernetes Beginner Guide (Module Notes)

A step-by-step guide for beginners. Every module starts with **simple theory**, then gives the **commands**, then a **practice lab** from your earlier notes.

**How commands are written:** each command is shown in two forms, the full `kubectl` form and the short `k` form. They do exactly the same thing.

```bash
kubectl get pods     # full form
k get pods           # short form (needs the alias below)
```

**Set up the short alias once:**

```bash
alias k=kubectl
source <(kubectl completion bash)
complete -o default -F __start_kubectl k
```

(The 2nd and 3rd lines add Tab auto-completion. Skip them if they give an error.)

---

## Modules

1. Introduction
2. Kubernetes Overview
3. Kubernetes Concepts
4. YAML Instructions
5. Pods, ReplicaSets, Deployments, Rollout and Rollback
   - 5.1 Pods
   - 5.2 ReplicaSets
   - 5.3 Deployments
   - 5.4 Rollout and Rollback
6. Networking in Kubernetes
7. Services (ClusterIP, NodePort, LoadBalancer)
8. Secrets
9. Volumes, PersistentVolume (PV) and PersistentVolumeClaim (PVC)
10. DaemonSet
11. StatefulSet
12. Master Quick Reference
13. New Topics (future additions)

---

# Module 1: Introduction

## Theory

### What is a container?

A **container** is a small, lightweight package that holds your application plus everything it needs to run (code, libraries, settings). Because everything is inside the package, it runs the same way on your laptop, on a test server, and in production.

Think of a **shipping container**: it does not matter what is inside or which ship carries it, the box is always the same shape and can be moved anywhere.

- **Image** = the recipe or blueprint (for example `nginx:alpine`).
- **Container** = a running copy made from that image.
- **Registry** = a place where images are stored (for example Docker Hub).

### Why do we need Kubernetes?

Running 1 container is easy. Running hundreds across many servers is hard. You would have to handle:

| Problem | What you would need to do by hand |
|---------|-----------------------------------|
| A container crashes | Notice it and start a new one |
| Traffic increases | Start more copies, spread them across servers |
| A server dies | Move its containers to another server |
| New version of the app | Update without downtime |
| Containers need to talk to each other | Manage IPs and load balancing |

**Kubernetes** (also written **K8s**, "K", 8 letters, "s") is a tool that does all of this automatically. It is called a **container orchestrator**, like a conductor who tells every musician (container) when and where to play.

Kubernetes was created by Google (based on their internal system called Borg), released as open source in 2014, and is now maintained by the CNCF.

### What Kubernetes gives you

- **Self-healing:** crashed containers are restarted or replaced.
- **Scaling:** increase or decrease the number of copies with one command.
- **Rolling updates and rollbacks:** update the app with no downtime, and go back if something breaks.
- **Service discovery and load balancing:** containers find each other and share traffic.
- **Declarative setup:** you describe what you want, Kubernetes makes it happen.

## Commands

### Container refresher (Docker)

```bash
docker run -d --name web nginx:alpine   # run a container in the background
docker ps                               # list running containers
docker images                           # list downloaded images
docker logs web                         # see container output
docker stop web                         # stop it
docker rm web                           # remove it
```

### First Kubernetes commands: check your setup

```bash
kubectl version              # client and server versions
k version

kubectl cluster-info         # address of the control plane
k cluster-info

kubectl get nodes            # list the machines in the cluster
k get nodes

kubectl api-resources        # list all object types (pods, services, ...)
k api-resources

kubectl explain pod          # built-in documentation for any object
k explain pod
```

---

# Module 2: Kubernetes Overview

## Theory

### The cluster

A group of machines working together is called a **cluster**. A cluster has two kinds of machines (nodes):

- **Control Plane** (the brain / manager): decides what should run and where.
- **Worker Nodes** (the muscle / workers): actually run your containers.

Restaurant analogy: the control plane is the manager who takes orders and assigns work; the worker nodes are the kitchens that cook the food.

```
                  CONTROL PLANE (the brain)
   +--------------------------------------------------------+
   | kube-apiserver | etcd | kube-scheduler | controller-mgr |
   +--------------------------------------------------------+
                          ^
                          |   you talk to the API server with kubectl
          +---------------+----------------+
          |                                |
   +--------------+                +--------------+
   | Worker Node 1|                | Worker Node 2|
   | kubelet      |                | kubelet      |
   | kube-proxy   |                | kube-proxy   |
   | container    |                | container    |
   | runtime      |                | runtime      |
   | [Pod] [Pod]  |                | [Pod]        |
   +--------------+                +--------------+
```

### Control plane components

| Component | Job (simple words) |
|-----------|--------------------|
| **kube-apiserver** | The front door. Every command (kubectl) goes through it. |
| **etcd** | The database. Stores the entire state of the cluster. |
| **kube-scheduler** | Chooses which node a new pod should run on. |
| **kube-controller-manager** | Watches the cluster and fixes differences (for example, "3 pods wanted but only 2 exist, create 1"). |
| **cloud-controller-manager** | Talks to the cloud provider (load balancers, disks). Only in cloud clusters. |

### Worker node components

| Component | Job (simple words) |
|-----------|--------------------|
| **kubelet** | The node's agent. Makes sure the containers of assigned pods are running. |
| **kube-proxy** | Handles networking rules so pods and services can be reached. |
| **Container runtime** | The software that actually runs containers (containerd, CRI-O). |

### What happens when you run `kubectl run`?

1. `kubectl` sends your request to the **API server**.
2. The API server saves it in **etcd**.
3. The **scheduler** picks a node for the pod.
4. The **kubelet** on that node sees the assignment and tells the **container runtime** to pull the image and start the container.
5. The status is reported back and saved in etcd.

## Commands

```bash
kubectl get nodes                  # list nodes and their status (Ready / NotReady)
k get nodes

kubectl get nodes -o wide          # adds IP, OS, kernel, runtime
k get nodes -o wide

kubectl describe node <node-name>  # full details of one node
k describe node <node-name>

kubectl get pods -n kube-system    # the cluster's own components run as pods here
k get pods -n kube-system

kubectl cluster-info               # control plane and DNS addresses
k cluster-info

kubectl config view                # your kubeconfig (cluster, user, context)
k config view

kubectl config current-context     # which cluster you are talking to
k config current-context

kubectl config get-contexts        # all available clusters/contexts
k config get-contexts
```

Tip: in `k get nodes`, the ROLES column shows `control-plane` for the brain and `<none>` for workers.

---

# Module 3: Kubernetes Concepts

## Theory

### Everything is an "object"

In Kubernetes you create **objects** (Pod, ReplicaSet, Deployment, Service, Namespace, and many more). Each object is a "record of intent": you tell Kubernetes what you want, and it keeps working to make it true.

### Desired state vs current state

- **Desired state** = what you asked for ("I want 3 pods").
- **Current state** = what really exists right now.
- Kubernetes controllers continuously compare the two and fix any difference. This loop is why a deleted pod comes back automatically when a ReplicaSet owns it.

### Imperative vs declarative

| Style | Meaning | Example |
|-------|---------|---------|
| **Imperative** | Tell Kubernetes what to do, step by step, with commands | `kubectl run web --image=nginx` |
| **Declarative** | Write what you want in a YAML file and apply it | `kubectl apply -f web.yaml` |

Imperative is quick for testing and exams. Declarative is how real projects work (the files can be saved in Git).

### Namespaces

A **namespace** is a virtual folder that separates objects inside one cluster (for example `dev`, `test`, `prod`). Default namespaces: `default`, `kube-system` (cluster components), `kube-public`, `kube-node-lease`.

### Labels and selectors

- A **label** is a key=value tag on an object (for example `app=web`, `env=prod`).
- A **selector** finds objects by their labels.
- This is how a ReplicaSet knows which pods are its pods, and how a Service knows where to send traffic.

### Annotations

Like labels, but for extra information (notes, change history). They are not used for selecting objects.

## Commands

### Namespaces

```bash
kubectl get namespaces                          # list namespaces
k get ns

kubectl create namespace dev                    # create one
k create ns dev

kubectl get pods -n dev                         # pods in a namespace
k get pods -n dev

kubectl get pods --all-namespaces               # pods everywhere
k get pods -A

kubectl config set-context --current --namespace=dev   # make dev the default
k config set-context --current --namespace=dev

kubectl delete namespace dev                    # deletes everything inside it!
k delete ns dev
```

### Labels and selectors

```bash
kubectl get pods --show-labels                  # show labels column
k get pods --show-labels

kubectl run web --image=nginx:alpine --labels="app=web,env=prod"
k run web --image=nginx:alpine --labels="app=web,env=prod"

kubectl label pod web tier=frontend             # add a label
k label pod web tier=frontend

kubectl label pod web tier-                     # remove a label (note the dash)
k label pod web tier-

kubectl get pods -l env=prod                    # filter by label
k get pods -l env=prod

kubectl get pods -l 'env in (prod,dev)'         # filter with a set
k get pods -l 'env in (prod,dev)'
```

### Annotations

```bash
kubectl annotate pod web owner="team-a"
k annotate pod web owner="team-a"
```

### Useful output formats (use these a lot)

```bash
kubectl get pod web -o wide      # more columns (IP, node)
kubectl get pod web -o yaml      # full YAML definition
kubectl get pod web -o json      # full JSON
kubectl get pods -o name         # only names

k get pod web -o wide
k get pod web -o yaml
k get pod web -o json
k get pods -o name
```

### Get help inside the terminal

```bash
kubectl explain pod.spec.containers    # documentation for a field
k explain pod.spec.containers

kubectl get pods --help
k get pods --help
```

---

# Module 4: YAML Instructions

## Theory

### What is YAML?

YAML is a simple text format used to describe Kubernetes objects. You write a YAML file, then give it to Kubernetes with `kubectl apply -f`.

### YAML rules for beginners

1. **Use spaces, never tabs.** Indentation (usually 2 spaces) shows structure.
2. **Key-value pair:** `name: my-pod` (a space after the colon is required).
3. **Nested (child) values:** indent them under the parent.
4. **Lists:** each item starts with a dash `-`.
5. **Comments:** start with `#`.
6. Text is case-sensitive: `kind: Pod` is correct, `kind: pod` is wrong.

```yaml
# key: value
name: my-pod

# nested
metadata:
  name: my-pod
  labels:
    app: web

# list
containers:
- name: nginx
  image: nginx:alpine
- name: sidecar
  image: busybox
```

### The 4 required parts of every Kubernetes YAML

| Field | Meaning | Example |
|-------|---------|---------|
| `apiVersion` | Which API version of Kubernetes to use | `v1` |
| `kind` | What type of object | `Pod` |
| `metadata` | Name, labels, namespace | `name: my-pod` |
| `spec` | The details of what you want | containers, replicas, ports |

### apiVersion by object type

| Kind | apiVersion |
|------|-----------|
| Pod | `v1` |
| Service | `v1` |
| Namespace | `v1` |
| ReplicaSet | `apps/v1` |
| Deployment | `apps/v1` |

### A complete Pod YAML, explained line by line

```yaml
apiVersion: v1            # API version for Pod
kind: Pod                 # object type (capital P)
metadata:
  name: redis             # name of the pod
  labels:
    app: redis            # a label (used by selectors)
spec:
  containers:             # list of containers in this pod
  - name: redis           # container name
    image: redis          # image to run
    ports:
    - containerPort: 6379 # port the container listens on
```

### Common YAML mistakes

| Mistake | Fix |
|---------|-----|
| Using tabs | Use spaces only |
| `kind: pod` | Use `Pod` (capital first letter) |
| Wrong `apiVersion` for the kind | Check the table above |
| Missing space after colon | `image: nginx`, not `image:nginx` |
| Wrong indentation | Children must be indented under the parent |
| Missing `-` for list items | Each container needs a dash |

## Commands

### Generate YAML instead of typing it (best trick)

`--dry-run=client -o yaml` prints the YAML without creating anything. Save it to a file with `>`.

```bash
kubectl run redis --image=redis --dry-run=client -o yaml > redis-pod.yaml
k run redis --image=redis --dry-run=client -o yaml > redis-pod.yaml

kubectl create deployment web --image=nginx:alpine --replicas=3 --dry-run=client -o yaml > web-deploy.yaml
k create deployment web --image=nginx:alpine --replicas=3 --dry-run=client -o yaml > web-deploy.yaml
```

### Work with YAML files

```bash
vi redis-pod.yaml                       # edit the file

kubectl apply -f redis-pod.yaml         # create (or update) from file
k apply -f redis-pod.yaml

kubectl create -f redis-pod.yaml        # create only (error if it exists)
k create -f redis-pod.yaml

kubectl delete -f redis-pod.yaml        # delete what the file describes
k delete -f redis-pod.yaml

kubectl apply -f ./myfolder/            # apply every YAML in a folder
k apply -f ./myfolder/

kubectl diff -f redis-pod.yaml          # preview what would change
k diff -f redis-pod.yaml

kubectl get pod redis -o yaml           # see the YAML of a running object
k get pod redis -o yaml

kubectl replace --force -f redis-pod.yaml   # delete and recreate from file
k replace --force -f redis-pod.yaml
```

### apply vs create

- `create` makes a new object and gives an error if it already exists.
- `apply` creates it if missing, or updates it if it exists. Use `apply` by default.

---

# Module 5: Pods, ReplicaSets, Deployments, Rollout and Rollback

How these three fit together:

```
Deployment  --manages-->  ReplicaSet  --manages-->  Pods  --run-->  Containers
(updates, rollback)       (keeps N pods)            (smallest unit)
```

---

## 5.1 Pods

### Theory

- A **Pod** is the smallest unit you can create in Kubernetes. It wraps one or more containers.
- Most pods have **one container**. Multi-container pods are used for helpers ("sidecars").
- All containers in a pod **share the same IP address and storage**, and can talk to each other on `localhost`.
- Pods are **temporary**. If a plain pod dies, it is not replaced. (ReplicaSets and Deployments fix this.)
- The **READY** column shows `ready containers / total containers`, for example `1/2` means 2 containers, 1 ready.

### Pod status cheat sheet

| Status | Meaning | First thing to check |
|--------|---------|----------------------|
| `Pending` | Accepted but not started yet | `describe` events: resources, scheduling |
| `ContainerCreating` | Pulling image / setting up | Wait, or check events |
| `Running` | At least one container running | READY column |
| `ErrImagePull` | Image pull failed | Image name, tag, registry access |
| `ImagePullBackOff` | Retrying image pull with delay | Same as above |
| `CrashLoopBackOff` | Container keeps crashing | `logs` and `logs --previous` |
| `Completed` | Container finished successfully | Normal for jobs |
| `Error` | Container exited with failure | `logs` |

### Commands: create, view, delete

```bash
kubectl run my-pod --image=nginx:alpine       # create a pod
k run my-pod --image=nginx:alpine

kubectl get pods                              # list pods
k get pods

kubectl get pods -o wide                      # adds IP and NODE columns
k get pods -o wide

kubectl get pod my-pod                        # one pod
k get pod my-pod

kubectl describe pod my-pod                   # full details + Events at the bottom
k describe pod my-pod

kubectl delete pod my-pod                     # delete
k delete pod my-pod

kubectl delete pod my-pod --force --grace-period=0    # delete immediately
k delete pod my-pod --force --grace-period=0
```

### Commands: look inside a pod

```bash
kubectl logs my-pod                    # container output
k logs my-pod

kubectl logs my-pod -c <container>     # a specific container in a multi-container pod
k logs my-pod -c <container>

kubectl logs my-pod --previous         # logs of the crashed (previous) container
k logs my-pod --previous

kubectl exec -it my-pod -- sh          # open a shell inside the pod
k exec -it my-pod -- sh

kubectl exec my-pod -- ls /            # run a single command
k exec my-pod -- ls /
```

### Multi-container pod example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: webapp
spec:
  containers:
  - name: nginx
    image: nginx
  - name: agentx
    image: agentx
```

### Practice Lab 1: Inspect and troubleshoot pods

**Q1. Which image is specified for the pods whose names begin with `newpods-`?**

```bash
kubectl get pods
k get pods

kubectl describe pod newpods-xxxxx | grep Image
k describe pod newpods-xxxxx | grep Image

kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}' | grep newpods
k get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}' | grep newpods
```

**Q2. Which nodes are these pods placed on?** The `NODE` column in wide output:

```bash
kubectl get pods -o wide
k get pods -o wide

kubectl describe pod newpods-xxxxx | grep Node
k describe pod newpods-xxxxx | grep Node
```

**Q3. How many containers are in the `webapp` pod?** The number after the slash in READY is the total:

```bash
kubectl get pod webapp
k get pod webapp

kubectl get pod webapp -o jsonpath='{.spec.containers[*].name}'
k get pod webapp -o jsonpath='{.spec.containers[*].name}'
```

**Q4. What images are used in `webapp`?** Look at every container, not just the first:

```bash
kubectl describe pod webapp
k describe pod webapp

kubectl get pod webapp -o jsonpath='{range .spec.containers[*]}{.name}{"\t"}{.image}{"\n"}{end}'
k get pod webapp -o jsonpath='{range .spec.containers[*]}{.name}{"\t"}{.image}{"\n"}{end}'
```

**Q5. What is the state of container `agentx`?** In `describe`, find the `agentx:` block and read `State:` and `Reason:`:

```
agentx:
  Image:   agentx
  State:   Waiting
    Reason: ImagePullBackOff
```

(It can briefly show `ErrImagePull` first.)

**Q6. Why is `agentx` in error?** Read the `Events:` section at the bottom of `describe`:

```bash
kubectl describe pod webapp
k describe pod webapp

kubectl get events --field-selector involvedObject.name=webapp
k get events --field-selector involvedObject.name=webapp
```

Typical message: `Failed to pull image "agentx": ... repository does not exist or may require authorization`. Reason: the image cannot be pulled because it does not exist (or needs a login). Kubernetes keeps retrying with a growing delay ("BackOff").

**Q7. What does the READY column mean?** `ready containers / total containers`.

| READY | Meaning |
|-------|---------|
| `1/1` | 1 container, ready |
| `2/2` | 2 containers, both ready |
| `1/2` | 2 containers, only 1 ready |
| `0/1` | 1 container, not ready |

**Q8. Delete the `webapp` pod:**

```bash
kubectl delete pod webapp
k delete pod webapp

kubectl delete pod webapp --force --grace-period=0
k delete pod webapp --force --grace-period=0
```

**Q9. Create a pod `redis` with image `redis123` using a YAML file (the wrong image is intentional, do not fix it yet):**

```bash
kubectl run redis --image=redis123 --dry-run=client -o yaml > redis-pod.yaml
k run redis --image=redis123 --dry-run=client -o yaml > redis-pod.yaml
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: redis
spec:
  containers:
  - name: redis
    image: redis123
```

```bash
kubectl apply -f redis-pod.yaml
k apply -f redis-pod.yaml

kubectl get pod redis        # shows ImagePullBackOff
k get pod redis
```

**Q10. Change the image on `redis` to `redis`.** A pod's image can be changed while it runs. Use any one method.

```bash
# Method A: set image  (format: container-name=new-image)
kubectl set image pod/redis redis=redis
k set image pod/redis redis=redis

# Method B: edit the live pod (change image: redis123 -> image: redis)
kubectl edit pod redis
k edit pod redis

# Method C: fix the YAML file, then apply again
kubectl apply -f redis-pod.yaml
k apply -f redis-pod.yaml

# Verify: STATUS should be Running, READY 1/1
kubectl get pod redis
k get pod redis

kubectl describe pod redis | grep Image
k describe pod redis | grep Image
```

### Troubleshooting flow

1. `k get pods` and look at STATUS and READY.
2. `k describe pod <name>` and read `Containers:` and `Events:`.
3. `k logs <name>` (add `-c <container>` if more than one container).
4. Fix the cause (image, command, config), then check again.

---

## 5.2 ReplicaSets

### Theory

- A **ReplicaSet** (short name `rs`) keeps a fixed number of identical pods running at all times.
- If a pod dies, the ReplicaSet creates a new one. If there are too many, it removes the extra ones.
- It finds its pods using a **selector** (labels), so the selector must match the pod template labels.
- **Very important rule:** if you change the image in a ReplicaSet, the pods that already exist are NOT updated. Only newly created pods use the new image. That is why you must delete the old pods after fixing the image.
- In real life you rarely create a ReplicaSet directly. A **Deployment** creates and manages it for you.

### ReplicaSet YAML

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: new-replica-set
spec:
  replicas: 4
  selector:
    matchLabels:
      name: busybox-pod
  template:
    metadata:
      labels:
        name: busybox-pod
    spec:
      containers:
      - name: busybox-container
        image: busybox
        command: ["sh", "-c", "echo Hello Kubernetes! && sleep 3600"]
```

The three parts of `spec`: `replicas` (how many), `selector` (which pods are mine), `template` (the pod blueprint used to create new pods).

### Commands

```bash
kubectl get rs                              # list ReplicaSets
k get rs

kubectl get rs -o wide                      # adds CONTAINERS, IMAGES, SELECTOR
k get rs -o wide

kubectl describe rs <name>                  # details and events
k describe rs <name>

kubectl scale rs <name> --replicas=5        # change the number of pods
k scale rs <name> --replicas=5

kubectl edit rs <name>                      # edit live (replicas, image, ...)
k edit rs <name>

kubectl set image rs/<name> <container>=<image>    # change image
k set image rs/<name> <container>=<image>

kubectl delete rs <name>                    # deletes the RS and its pods
k delete rs <name>
```

### Practice Lab 2: ReplicaSets

**Q1. How many pods exist?**

```bash
kubectl get pods
k get pods

kubectl get pods --no-headers | wc -l       # exact count
k get pods --no-headers | wc -l
```

**Q2. How many ReplicaSets exist?**

```bash
kubectl get rs
k get rs

kubectl get rs --no-headers | wc -l
k get rs --no-headers | wc -l
```

Example output (DESIRED = wanted, CURRENT = existing, READY = working):

```
NAME             DESIRED   CURRENT   READY   AGE
new-replica-set  4         4         0       2m
replicaset-1     2         2         2       1m
replicaset-2     2         2         2       1m
```

**Q3. What image is used by the pods in `new-replica-set`?**

```bash
kubectl describe rs new-replica-set | grep Image
k describe rs new-replica-set | grep Image

kubectl get rs new-replica-set -o wide
k get rs new-replica-set -o wide

kubectl get rs new-replica-set -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\t"}{.image}{"\n"}{end}'
k get rs new-replica-set -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\t"}{.image}{"\n"}{end}'
```

In this lab the image is intentionally wrong, so the pods show `ImagePullBackOff` and READY is `0`.

**Q4. Delete the two new ReplicaSets `replicaset-1` and `replicaset-2`:**

```bash
kubectl delete rs replicaset-1 replicaset-2
k delete rs replicaset-1 replicaset-2

kubectl get rs
k get rs
```

**Q5. Fix `new-replica-set` to use the correct image `busybox`.** Two ways:

*Option A: update the existing ReplicaSet, then delete its pods (faster)*

```bash
# Step 1: change the image (pick one)
kubectl edit rs new-replica-set
k edit rs new-replica-set

kubectl set image rs/new-replica-set <container-name>=busybox
k set image rs/new-replica-set <container-name>=busybox

# Step 2: find the selector label
kubectl get rs new-replica-set -o wide
k get rs new-replica-set -o wide

# Step 3: delete the old pods; the RS recreates them with the new image
kubectl delete pods -l name=busybox-pod
k delete pods -l name=busybox-pod

# or delete every pod (fine in a practice lab)
kubectl delete pods --all
k delete pods --all

# Step 4: verify
kubectl get pods
k get pods
```

*Option B: delete and recreate from the file `/root/new-replica-set.yaml`*

```bash
vi /root/new-replica-set.yaml            # change the wrong image to busybox

kubectl delete rs new-replica-set
kubectl apply -f /root/new-replica-set.yaml
k delete rs new-replica-set
k apply -f /root/new-replica-set.yaml

# one-line alternative
kubectl replace --force -f /root/new-replica-set.yaml
k replace --force -f /root/new-replica-set.yaml
```

**Q6. Scale the ReplicaSet to 5 pods:**

```bash
kubectl scale rs new-replica-set --replicas=5
k scale rs new-replica-set --replicas=5

kubectl get rs new-replica-set        # DESIRED, CURRENT, READY should be 5
k get rs new-replica-set
```

(Alternative: `k edit rs new-replica-set` and change `replicas:`.)

**Q7. Scale the ReplicaSet down to 2 pods:**

```bash
kubectl scale rs new-replica-set --replicas=2
k scale rs new-replica-set --replicas=2

kubectl get rs new-replica-set
kubectl get pods
k get rs new-replica-set
k get pods
```

### ReplicaSet summary

| Point | Explanation |
|-------|-------------|
| Short name | `rs` |
| Job | Keep the desired number of pods running |
| Template change | Does not update running pods, only new ones |
| Fix a wrong image | Edit the RS, then delete old pods (or delete and recreate the RS) |
| Scaling | `k scale rs <name> --replicas=<n>` |
| Delete RS | Also deletes its pods |
| Selector | Must match the pod template labels |

---

## 5.3 Deployments

### Theory

- A **Deployment** is the standard way to run an application. It creates a ReplicaSet, and the ReplicaSet creates the pods.
- On top of what a ReplicaSet does, a Deployment adds:
  - **Rolling updates:** change the image with no downtime.
  - **Rollback:** go back to a previous version.
  - **Pause and resume** of updates.
- Updating a Deployment makes it create a **new ReplicaSet** for the new version while the old one is scaled down.
- A Deployment YAML is almost the same as a ReplicaSet YAML. Only `kind` changes to `Deployment`.

### Commands

```bash
kubectl create deployment my-first-deployment --image=nginx:alpine -n default
k create deployment my-first-deployment --image=nginx:alpine -n default

kubectl get deployments               # list (short name: deploy)
k get deploy

kubectl get deployment my-first-deployment
k get deployment my-first-deployment

kubectl describe deployment my-first-deployment
k describe deployment my-first-deployment

kubectl scale deployment my-first-deployment --replicas=3
k scale deployment my-first-deployment --replicas=3

kubectl set image deployment/my-first-deployment nginx=httpd:alpine
k set image deployment/my-first-deployment nginx=httpd:alpine

kubectl delete deployment my-first-deployment
k delete deployment my-first-deployment
```

Note: when you create a deployment with `create deployment --image=nginx:alpine`, the container name is `nginx` (taken from the image name). Check it with:

```bash
kubectl get deployment my-first-deployment -o jsonpath='{.spec.template.spec.containers[*].name}'
k get deployment my-first-deployment -o jsonpath='{.spec.template.spec.containers[*].name}'
```

### Practice Lab 3: Deployment steps

| # | Task | Command (k form) |
|---|------|------------------|
| 1 | Create pod `my-pod` with `nginx:alpine` | `k run my-pod --image=nginx:alpine` |
| 2 | Delete `my-pod` | `k delete pod my-pod` |
| 3 | Create deployment `my-first-deployment` with `nginx:alpine` in default namespace | `k create deployment my-first-deployment --image=nginx:alpine -n default` |
| 4 | Scale to 3 replicas | `k scale deployment my-first-deployment --replicas=3` |
| 5 | Check all 3 are ready (`3/3`) | `k get deployment my-first-deployment` |
| 6 | Scale down to 2 replicas | `k scale deployment my-first-deployment --replicas=2` |
| 7 | Check all 2 are ready (`2/2`) | `k get deployment my-first-deployment` |
| 8 | Change image to `httpd:alpine` | `k set image deployment/my-first-deployment nginx=httpd:alpine` |
| 9 | Delete the deployment | `k delete deployment my-first-deployment` |

Extra checks:

```bash
kubectl get pods -l app=my-first-deployment
kubectl rollout status deployment my-first-deployment
kubectl describe deployment my-first-deployment | grep Image

k get pods -l app=my-first-deployment
k rollout status deployment my-first-deployment
k describe deployment my-first-deployment | grep Image
```

### Practice Lab 4: Create a Deployment from a YAML file

**Task:** create Deployment `httpd-frontend`, replicas `3`, image `httpd:2.4-alpine`, using your own definition file.

**Method 1: generate the YAML, then apply (fastest)**

```bash
kubectl create deployment httpd-frontend --image=httpd:2.4-alpine --replicas=3 --dry-run=client -o yaml > httpd-frontend.yaml
k create deployment httpd-frontend --image=httpd:2.4-alpine --replicas=3 --dry-run=client -o yaml > httpd-frontend.yaml

vi httpd-frontend.yaml            # optional: review

kubectl apply -f httpd-frontend.yaml
k apply -f httpd-frontend.yaml
```

**Method 2: write the YAML yourself**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpd-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      name: httpd-frontend
  template:
    metadata:
      labels:
        name: httpd-frontend
    spec:
      containers:
      - name: httpd-frontend
        image: httpd:2.4-alpine
```

```bash
kubectl apply -f httpd-frontend.yaml
k apply -f httpd-frontend.yaml
```

**Verify:**

```bash
kubectl get deployment httpd-frontend       # READY should be 3/3
k get deployment httpd-frontend

kubectl get rs
kubectl get pods -o wide                    # which nodes the pods are on
k get rs
k get pods -o wide

kubectl describe deployment httpd-frontend | grep Image
k describe deployment httpd-frontend | grep Image
```

Common mistakes: wrong `apiVersion` (must be `apps/v1`), `kind: deployment` in lowercase, selector labels not matching template labels, `replicas` placed under `template` (it belongs directly under `spec`), tabs instead of spaces.

---

## 5.4 Rollout and Rollback

### Theory

- A **rollout** is the process of changing a Deployment to a new version (a new image or a new setting). Every change creates a new **revision**.
- Kubernetes keeps the revision history, so you can **roll back** to an older revision if the new version is broken.

### Deployment strategies

| Strategy | What it does | Downtime? |
|----------|--------------|-----------|
| **RollingUpdate** (default) | Replaces pods a few at a time. Old pods are removed as new ones become ready. | No |
| **Recreate** | Deletes all old pods first, then creates the new ones. | Yes |

Rolling update settings (defaults are 25% each):

- `maxSurge`: how many extra pods may be created above the desired number during an update.
- `maxUnavailable`: how many pods may be unavailable during an update.

```yaml
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
```

### What happens during a rolling update

```
Before:   ReplicaSet-old [v1][v1][v1]
During:   ReplicaSet-old [v1][v1]      ReplicaSet-new [v2]      (old shrinks, new grows)
After:    ReplicaSet-old (0 pods)      ReplicaSet-new [v2][v2][v2]
```

The old ReplicaSet is kept (with 0 pods) so that a rollback is instant.

### Commands

```bash
# Start a rollout by changing the image
kubectl set image deployment/web nginx=nginx:1.25
k set image deployment/web nginx=nginx:1.25

# Watch it finish
kubectl rollout status deployment/web
k rollout status deployment/web

# See the revision history
kubectl rollout history deployment/web
k rollout history deployment/web

# Details of one revision
kubectl rollout history deployment/web --revision=2
k rollout history deployment/web --revision=2

# Roll back to the previous revision
kubectl rollout undo deployment/web
k rollout undo deployment/web

# Roll back to a specific revision
kubectl rollout undo deployment/web --to-revision=1
k rollout undo deployment/web --to-revision=1

# Restart all pods of a deployment (new pods, same image)
kubectl rollout restart deployment/web
k rollout restart deployment/web

# Pause and resume (make several changes, then roll out once)
kubectl rollout pause deployment/web
kubectl rollout resume deployment/web
k rollout pause deployment/web
k rollout resume deployment/web
```

**Add a note to each revision** so the history is readable (the old `--record` flag is deprecated):

```bash
kubectl annotate deployment/web kubernetes.io/change-cause="update to nginx 1.25"
k annotate deployment/web kubernetes.io/change-cause="update to nginx 1.25"
```

### Hands-on walkthrough

```bash
# 1. Create a deployment with 3 replicas
k create deployment web --image=nginx:1.24 --replicas=3

# 2. Update the image (revision 2)
k set image deployment/web nginx=nginx:1.25
k rollout status deployment/web

# 3. Break it on purpose with a wrong image (revision 3)
k set image deployment/web nginx=nginx:wrong-tag
k get pods                  # some pods show ImagePullBackOff, old pods keep running
k rollout status deployment/web

# 4. Look at history and roll back
k rollout history deployment/web
k rollout undo deployment/web
k rollout status deployment/web

# 5. Confirm the image is back to a working version
k describe deployment web | grep Image

# 6. Clean up
k delete deployment web
```

Why a broken rollout is safe: the rolling update keeps the old pods running until the new ones are ready, so the app stays available while you roll back.

---

# Module 6: Networking in Kubernetes

## Theory

### The basic networking rules

Kubernetes networking follows a few simple rules:

1. **Every pod gets its own IP address.**
2. **Every pod can reach every other pod by IP**, even on different nodes, without NAT.
3. Nodes can reach pods, and pods can reach nodes.
4. Containers **inside the same pod** share one IP and talk to each other over `localhost`.

### Who provides this? The CNI plugin

Kubernetes itself does not build the pod network. A **CNI plugin** (Container Network Interface) does, for example **Calico**, **Flannel**, **Weave Net**, **Cilium**. A cluster needs one installed, otherwise pods cannot get IPs and nodes stay `NotReady`.

Each node is given a slice of IP addresses (the **pod CIDR**) to hand out to its pods.

### The problem: pod IPs keep changing

Pods are temporary. When a pod is replaced, the new pod gets a **new IP**. So you cannot rely on a pod's IP address to reach your app. The fix is a **Service** (Module 7), which gives a stable IP and name in front of a group of pods.

### Kubernetes DNS (CoreDNS)

Kubernetes runs a DNS server called **CoreDNS** (as pods in `kube-system`). Every Service gets a DNS name automatically:

```
<service-name>.<namespace>.svc.cluster.local
```

- Inside the **same namespace** you can use just the short name: `web-svc`.
- From **another namespace**, use `web-svc.dev` or the full name.

### kube-proxy

`kube-proxy` runs on every node and sets up the rules (iptables or IPVS) that send traffic addressed to a Service to one of its healthy pods.

### Network Policies (introduction)

By default all pods can talk to all pods. A **NetworkPolicy** is like a firewall rule that restricts which pods may talk to which. (They only work if your CNI plugin supports them.)

### Traffic types at a glance

| Traffic | How it works |
|---------|--------------|
| Container to container in the same pod | `localhost` |
| Pod to pod | Pod IP (or better, via a Service name) |
| Pod to Service | Service name through CoreDNS |
| Outside world to pods | NodePort or LoadBalancer Service (or Ingress) |

## Commands

### See pod IPs and nodes

```bash
kubectl get pods -o wide             # IP and NODE columns
k get pods -o wide

kubectl get pod <name> -o jsonpath='{.status.podIP}'
k get pod <name> -o jsonpath='{.status.podIP}'
```

### Pod CIDR and nodes

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'
k get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'

kubectl get pods -n kube-system        # look for calico, flannel, weave, cilium, coredns
k get pods -n kube-system
```

### Test pod-to-pod connectivity

```bash
# Create two test pods
k run web --image=nginx:alpine
k run client --image=busybox:1.28 --command -- sleep 3600

# Get the IP of the web pod
k get pod web -o wide

# From the client pod, call the web pod by IP
k exec client -- wget -qO- http://<web-pod-ip>

# One-off test pod that deletes itself afterwards
k run test --image=busybox:1.28 --rm -it --restart=Never -- wget -qO- http://<web-pod-ip>
```

### Test DNS

```bash
kubectl run dns-test --image=busybox:1.28 --rm -it --restart=Never -- nslookup kubernetes
k run dns-test --image=busybox:1.28 --rm -it --restart=Never -- nslookup kubernetes

kubectl get pods -n kube-system -l k8s-app=kube-dns     # CoreDNS pods
k get pods -n kube-system -l k8s-app=kube-dns
```

### Network policies

```bash
kubectl get networkpolicy
k get netpol

kubectl describe networkpolicy <name>
k describe netpol <name>
```

### Troubleshooting networking

| Symptom | What to check |
|---------|---------------|
| Pod has no IP, stuck `ContainerCreating` | CNI plugin installed and running? `k get pods -n kube-system` |
| Node is `NotReady` | CNI or kubelet problem: `k describe node <name>` |
| Pod cannot resolve names | CoreDNS pods running? |
| Service reachable by IP but not by name | DNS issue, or wrong namespace in the name |

---

# Module 7: Services (ClusterIP, NodePort, LoadBalancer)

## Theory

### What is a Service?

A **Service** is a stable "front door" for a group of pods.

- Pods come and go and their IPs change, but the **Service keeps one fixed IP and DNS name**.
- A Service finds its pods using a **selector** (labels) and spreads traffic across all matching, healthy pods (load balancing).
- The list of pod IPs behind a Service is called its **Endpoints**.

```
   client --> [ Service: web-svc  10.96.0.15:80 ] --+--> Pod 10.244.1.4
                    (stable IP and name)             +--> Pod 10.244.2.7
                                                     +--> Pod 10.244.1.9
```

### The three ports (very important, often confused)

```
 outside user --> nodePort (on every node) --> port (Service) --> targetPort (container)
```

| Port | Meaning |
|------|---------|
| `nodePort` | Port opened on every node (NodePort only). Range **30000 to 32767**. |
| `port` | Port of the Service itself (what other pods use). |
| `targetPort` | Port the container listens on. If left out, it equals `port`. |

### Service types

| Type | Who can reach it | Typical use |
|------|------------------|-------------|
| **ClusterIP** (default) | Only inside the cluster | Internal communication, for example frontend to database |
| **NodePort** | From outside: `<node-ip>:<nodePort>` | Quick external access, testing, labs |
| **LoadBalancer** | From outside through a cloud load balancer with its own external IP | Production on cloud (AWS, Azure, GCP) |
| **ExternalName** | Maps a Service name to an outside DNS name | Pointing to an external database or API |

They build on each other: **LoadBalancer includes NodePort, and NodePort includes ClusterIP.**

### ClusterIP

- Gets an internal virtual IP. Not reachable from outside the cluster.
- Other pods use the Service name: `http://web-clusterip`.

### NodePort

- Opens the same port (30000 to 32767) on **every node**.
- Access from outside: `http://<any-node-ip>:<nodePort>`.
- Simple, but you must know node IPs and the port numbers are high.

### LoadBalancer

- Asks the cloud provider to create an external load balancer and gives the Service a public `EXTERNAL-IP`.
- On a local or bare-metal cluster (kind, kubeadm, a lab), the EXTERNAL-IP stays `<pending>` because there is no cloud. Use NodePort there, or `minikube tunnel` (minikube), or MetalLB.

### Which one should I use?

- Pods talking to each other: **ClusterIP**.
- Quick test from your browser/lab: **NodePort**.
- Real internet-facing app on cloud: **LoadBalancer** (often with an Ingress).

## Commands

### Create a deployment to use for the examples

```bash
kubectl create deployment web --image=nginx:alpine --replicas=3
k create deployment web --image=nginx:alpine --replicas=3
```

This gives the pods the label `app=web`, which the Services below will select.

### Create Services with `expose` (fastest)

```bash
# ClusterIP (default type)
kubectl expose deployment web --name=web-clusterip --port=80 --target-port=80
k expose deployment web --name=web-clusterip --port=80 --target-port=80

# NodePort
kubectl expose deployment web --name=web-nodeport --port=80 --target-port=80 --type=NodePort
k expose deployment web --name=web-nodeport --port=80 --target-port=80 --type=NodePort

# LoadBalancer
kubectl expose deployment web --name=web-lb --port=80 --target-port=80 --type=LoadBalancer
k expose deployment web --name=web-lb --port=80 --target-port=80 --type=LoadBalancer
```

`expose` automatically copies the selector from the deployment. A NodePort number is chosen for you (random in 30000 to 32767).

### Expose a pod (common lab task)

```bash
# Create a pod and a ClusterIP service for it in one command
kubectl run httpd --image=httpd:alpine --port=80 --expose
k run httpd --image=httpd:alpine --port=80 --expose

# Create a Service for an existing pod (redis example)
kubectl expose pod redis --port=6379 --name=redis-service
k expose pod redis --port=6379 --name=redis-service
```

### Create Services with `create service`

```bash
kubectl create service clusterip web-cip --tcp=80:80
k create service clusterip web-cip --tcp=80:80

kubectl create service nodeport web-np --tcp=80:80 --node-port=30080
k create service nodeport web-np --tcp=80:80 --node-port=30080

kubectl create service loadbalancer web-lb2 --tcp=80:80
k create service loadbalancer web-lb2 --tcp=80:80
```

Warning: `create service` sets the selector to `app=<service-name>`. It only finds your pods if they have that exact label. For this reason `expose` or a YAML file is safer.

### View and inspect Services

```bash
kubectl get svc                       # list (svc = service)
k get svc

kubectl get svc -o wide               # includes the selector
k get svc -o wide

kubectl describe svc web-nodeport     # selector, ports, endpoints
k describe svc web-nodeport

kubectl get endpoints                 # the pod IPs behind each service
k get ep

kubectl get svc web-nodeport -o yaml
k get svc web-nodeport -o yaml
```

Example output:

```
NAME           TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
web-clusterip  ClusterIP      10.96.12.4     <none>        80/TCP         1m
web-nodeport   NodePort       10.96.30.8     <none>        80:31234/TCP   1m
web-lb         LoadBalancer   10.96.55.2     <pending>     80:30987/TCP   1m
```

How to read `80:31234/TCP`: Service port 80, node port 31234.

### Service YAML files

**ClusterIP**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-clusterip
spec:
  type: ClusterIP          # optional, this is the default
  selector:
    app: web               # matches pod label app=web
  ports:
  - port: 80               # service port
    targetPort: 80         # container port
```

**NodePort**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080        # optional; 30000-32767, auto-assigned if omitted
```

**LoadBalancer**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-lb
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
```

Create from a file:

```bash
kubectl apply -f web-nodeport.yaml
k apply -f web-nodeport.yaml
```

### Test each Service type

```bash
# ClusterIP: test from inside the cluster
kubectl run test --image=busybox:1.28 --rm -it --restart=Never -- wget -qO- http://web-clusterip
k run test --image=busybox:1.28 --rm -it --restart=Never -- wget -qO- http://web-clusterip

# NodePort: from outside, use any node IP and the node port
kubectl get nodes -o wide             # find a node IP (INTERNAL-IP)
k get nodes -o wide
curl http://<node-ip>:30080

# minikube users
minikube service web-nodeport --url
minikube tunnel                       # gives LoadBalancer services an external IP

# LoadBalancer: use the EXTERNAL-IP once it is assigned
kubectl get svc web-lb
k get svc web-lb
curl http://<external-ip>

# Quick test from your own machine without any Service type
kubectl port-forward svc/web-clusterip 8080:80
k port-forward svc/web-clusterip 8080:80
curl http://localhost:8080
```

### Edit and delete

```bash
kubectl edit svc web-nodeport
k edit svc web-nodeport

kubectl delete svc web-clusterip web-nodeport web-lb
k delete svc web-clusterip web-nodeport web-lb

kubectl delete deployment web
k delete deployment web
```

### Service troubleshooting

| Problem | Likely cause and fix |
|---------|----------------------|
| `ENDPOINTS` is empty (`k get ep`) | Service selector does not match pod labels. Compare `k get svc -o wide` with `k get pods --show-labels` |
| Service works by IP, not by name | DNS problem, or you are in another namespace (use `name.namespace`) |
| NodePort not reachable from outside | Firewall or security group blocks the node port; wrong node IP |
| LoadBalancer stuck on `<pending>` | No cloud provider. Use NodePort, `minikube tunnel`, or MetalLB |
| Connection refused | `targetPort` does not match the port the container listens on |

### Service summary

| | ClusterIP | NodePort | LoadBalancer |
|---|-----------|----------|--------------|
| Reachable from | Inside cluster | Outside via node IP and port | Outside via external IP |
| Port range | any | 30000 to 32767 | any (plus an auto node port) |
| Needs cloud? | No | No | Yes (for a real external IP) |
| Default type? | Yes | No | No |
| Create fast | `k expose deploy web --port=80` | add `--type=NodePort` | add `--type=LoadBalancer` |

---

# Module 8: Secrets

## Theory

### What is a Secret?

A **Secret** is a Kubernetes object that stores small amounts of **sensitive data**: passwords, API tokens, SSH keys, TLS certificates. Instead of writing a password inside your pod YAML or your image, you put it in a Secret and let the pod read it.

**Why not just hard-code the password?**

- Anyone who can see the YAML (or the Git repo, or the image) can see the password.
- Changing a password would mean rebuilding the image.
- A Secret keeps sensitive data separate and lets you control who can read it (RBAC).

### Secret vs ConfigMap

| | ConfigMap | Secret |
|---|-----------|--------|
| Stores | Normal config (URLs, feature flags) | Sensitive data (passwords, tokens) |
| Stored as | Plain text | base64-encoded |
| Used the same way? | Yes (env var or volume) | Yes (env var or volume) |

### IMPORTANT: base64 is NOT encryption

Secret values are stored **base64-encoded**. That is just an encoding anyone can reverse in one command (`base64 -d`). To really protect Secrets:

- Limit access with **RBAC** (who can `get secrets`).
- Turn on **encryption at rest** for etcd.
- Never commit Secret YAML files with real values to Git.
- Consider an external tool (Vault, cloud secret managers) for production.

### Common Secret types

| Type | Used for |
|------|----------|
| `Opaque` (default) | Any custom key-value data |
| `kubernetes.io/dockerconfigjson` | Login for a private image registry |
| `kubernetes.io/tls` | TLS certificate and private key |
| `kubernetes.io/basic-auth` | Username and password |
| `kubernetes.io/service-account-token` | Service account token |

### Three ways a pod can use a Secret

1. **One key as an environment variable** (`secretKeyRef`).
2. **All keys as environment variables** (`envFrom`).
3. **Mounted as files** in a volume (each key becomes a file).

Difference: environment variables are fixed when the pod starts (changing the Secret later needs a pod restart). Mounted files are refreshed automatically after a short delay.

## Commands

### Create a Secret

```bash
# From literal values
kubectl create secret generic db-secret --from-literal=username=admin --from-literal=password=Passw0rd
k create secret generic db-secret --from-literal=username=admin --from-literal=password=Passw0rd

# From a file (the file name becomes the key)
kubectl create secret generic ssh-key --from-file=./id_rsa
k create secret generic ssh-key --from-file=./id_rsa

# From an env-style file (KEY=value per line)
kubectl create secret generic app-secret --from-env-file=./app.env
k create secret generic app-secret --from-env-file=./app.env

# Private registry login
kubectl create secret docker-registry regcred --docker-server=<server> --docker-username=<user> --docker-password=<pass> --docker-email=<email>
k create secret docker-registry regcred --docker-server=<server> --docker-username=<user> --docker-password=<pass> --docker-email=<email>

# TLS certificate
kubectl create secret tls my-tls --cert=tls.crt --key=tls.key
k create secret tls my-tls --cert=tls.crt --key=tls.key
```

### View Secrets

```bash
kubectl get secrets                    # list (short name: secret)
k get secret

kubectl describe secret db-secret      # shows key names and sizes, NOT the values
k describe secret db-secret

kubectl get secret db-secret -o yaml   # shows the base64 values
k get secret db-secret -o yaml
```

### Decode a value

```bash
kubectl get secret db-secret -o jsonpath='{.data.password}' | base64 -d
k get secret db-secret -o jsonpath='{.data.password}' | base64 -d
```

### Encode a value by hand (for YAML files)

```bash
echo -n 'admin' | base64        # YWRtaW4=
echo -n 'Passw0rd' | base64     # UGFzc3cwcmQ=
```

Always use `-n`. Without it, a hidden newline is added to the value and your password will be wrong.

### Secret YAML

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:                       # values must be base64-encoded
  username: YWRtaW4=
  password: UGFzc3cwcmQ=
```

Easier: use `stringData` and write normal text. Kubernetes encodes it for you.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:                 # plain text, converted to base64 automatically
  username: admin
  password: Passw0rd
```

```bash
kubectl apply -f db-secret.yaml
k apply -f db-secret.yaml
```

### Use a Secret in a pod

**1. One key as an environment variable**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mysql-pod
spec:
  containers:
  - name: mysql
    image: mysql:8
    env:
    - name: MYSQL_ROOT_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret        # the Secret name
          key: password          # the key inside the Secret
```

**2. All keys as environment variables**

```yaml
spec:
  containers:
  - name: app
    image: nginx:alpine
    envFrom:
    - secretRef:
        name: db-secret          # every key in the Secret becomes an env var
```

(Each key becomes an env var with the same name as the key, here `username` and `password`.)

**3. Mount as files**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-vol-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    volumeMounts:
    - name: secret-vol
      mountPath: /etc/secret     # each key becomes a file here
      readOnly: true
  volumes:
  - name: secret-vol
    secret:
      secretName: db-secret
```

**Use a registry Secret to pull a private image**

```yaml
spec:
  imagePullSecrets:
  - name: regcred
  containers:
  - name: app
    image: myregistry.com/private-app:1.0
```

### Verify inside the pod

```bash
kubectl exec secret-vol-pod -- ls /etc/secret
kubectl exec secret-vol-pod -- cat /etc/secret/password
kubectl exec mysql-pod -- env
k exec secret-vol-pod -- ls /etc/secret
k exec secret-vol-pod -- cat /etc/secret/password
k exec mysql-pod -- env
```

### Edit and delete

```bash
kubectl edit secret db-secret          # values are base64 here
k edit secret db-secret

kubectl delete secret db-secret
k delete secret db-secret
```

### Practice Lab: Secrets

1. Create a Secret `db-secret` with `username=admin` and `password=Passw0rd`.
2. Check it with `k describe secret db-secret` (values are hidden) and decode the password with `base64 -d`.
3. Create a pod `mysql-pod` (YAML above) that reads `MYSQL_ROOT_PASSWORD` from the Secret.
4. Run `k exec mysql-pod -- env` and find `MYSQL_ROOT_PASSWORD`.
5. Mount the same Secret as files in a second pod and read `/etc/secret/password`.
6. Delete the Secret and watch what happens to a new pod that uses it (see below).

### Troubleshooting Secrets

| Symptom | Cause and fix |
|---------|---------------|
| Pod status `CreateContainerConfigError` | The Secret or the key does not exist. Check `k describe pod <name>` Events, then `k get secret` and the key names |
| Wrong password inside the app | Value was encoded with a hidden newline. Re-encode with `echo -n` |
| Changed Secret but pod still uses old value | Env vars do not refresh. Restart: `k rollout restart deployment/<name>` |
| `ImagePullBackOff` on a private image | Missing or wrong `imagePullSecrets` |
| Secret in another namespace not found | Secrets are namespaced; a pod can only use Secrets from its own namespace |

---

# Module 9: Volumes, PersistentVolume (PV) and PersistentVolumeClaim (PVC)

## Theory

### The problem: container storage is temporary

Files written inside a container disappear when the container restarts or the pod is deleted. For databases, uploads, or logs you need storage that **outlives the pod**. Kubernetes solves this with **volumes**.

### Types of volumes (simple view)

| Volume | Lifetime | Use |
|--------|----------|-----|
| **emptyDir** | Lives as long as the pod. Gone when the pod is deleted. | Scratch space, sharing files between containers in the same pod |
| **hostPath** | Uses a folder on the node. Survives pod deletion. | Testing only (data is tied to one node, security risk) |
| **PersistentVolume + Claim** | Independent of any pod. Survives pod deletion. | Real persistent storage (disks, NFS, cloud volumes) |

### PV, PVC and the pod: the parking analogy

```
   PersistentVolume (PV)        = a parking space that exists in the car park
   PersistentVolumeClaim (PVC)  = a request: "I need a space of at least this size"
   Pod                          = the car that uses the space it was given
```

- **PV:** a piece of storage in the cluster. Usually created by an admin, or created automatically. It is **cluster-wide** (no namespace).
- **PVC:** a request for storage made by a user or application. It is **namespaced**.
- Kubernetes **binds** a PVC to a matching PV. The pod then mounts the PVC.

```
  Pod  --uses-->  PVC  --bound to-->  PV  --is-->  Real disk (node folder, NFS, cloud disk)
```

Why two objects? So developers ask for "1Gi of storage" without needing to know where the disk really is.

### How a PVC finds a PV (binding rules)

A PVC binds to a PV when all of these match:

1. The PV **capacity** is equal to or bigger than the request.
2. The **access mode** is supported by the PV.
3. The **storageClassName** is the same.

Binding is one-to-one: one PV serves one PVC. If the PVC asks for 500Mi and the PV is 1Gi, the PVC gets the whole 1Gi PV.

### Access modes

| Mode | Short | Meaning |
|------|-------|---------|
| ReadWriteOnce | RWO | Read and write by a single node |
| ReadOnlyMany | ROX | Read only by many nodes |
| ReadWriteMany | RWX | Read and write by many nodes |
| ReadWriteOncePod | RWOP | Read and write by a single pod |

### Reclaim policy: what happens to the PV after the PVC is deleted

| Policy | Result |
|--------|--------|
| **Retain** | PV and data are kept. An admin must clean it up manually. |
| **Delete** | PV and the underlying storage are deleted automatically. |

### PV status (phase)

| Phase | Meaning |
|-------|---------|
| `Available` | Free, not yet claimed |
| `Bound` | Claimed by a PVC |
| `Released` | The PVC was deleted, but the PV is not yet reclaimed |
| `Failed` | Automatic reclaim failed |

### StorageClass and dynamic provisioning

Creating PVs by hand does not scale. A **StorageClass** describes a type of storage ("fast SSD", "standard"). When a PVC names a StorageClass, Kubernetes **creates the PV automatically**. This is called **dynamic provisioning**, and it is how most clusters work (minikube, kind and cloud clusters have a default StorageClass).

- A PVC with **no** `storageClassName` uses the cluster's **default** StorageClass.
- A PVC with `storageClassName: ""` asks for **no** class, so it can only bind to a manually created PV that also has no class.

## Commands

### emptyDir: shared scratch space

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: emptydir-pod
spec:
  containers:
  - name: writer
    image: busybox
    command: ["sh", "-c", "echo hello > /data/msg.txt && sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /data
  - name: reader
    image: busybox
    command: ["sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: shared
      mountPath: /data
  volumes:
  - name: shared
    emptyDir: {}
```

```bash
kubectl apply -f emptydir-pod.yaml
k apply -f emptydir-pod.yaml

kubectl exec emptydir-pod -c reader -- cat /data/msg.txt     # reader sees the writer's file
k exec emptydir-pod -c reader -- cat /data/msg.txt
```

### hostPath: a folder on the node (testing only)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    volumeMounts:
    - name: host-vol
      mountPath: /usr/share/nginx/html
  volumes:
  - name: host-vol
    hostPath:
      path: /mnt/data
      type: DirectoryOrCreate
```

### PersistentVolume (PV): manual creation

There is no `kubectl create pv` command, so use YAML. File `pv-demo.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-demo
spec:
  capacity:
    storage: 1Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/data          # folder on the node (for labs only)
```

```bash
kubectl apply -f pv-demo.yaml
k apply -f pv-demo.yaml

kubectl get pv               # STATUS should be Available
k get pv
```

### PersistentVolumeClaim (PVC)

File `pvc-demo.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-demo
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: manual   # must match the PV
  resources:
    requests:
      storage: 500Mi
```

```bash
kubectl apply -f pvc-demo.yaml
k apply -f pvc-demo.yaml

kubectl get pvc              # STATUS should be Bound
k get pvc

kubectl get pv,pvc           # see both together
k get pv,pvc
```

The PV status changes from `Available` to `Bound`, and the PVC shows the PV name under VOLUME.

### Use the PVC in a pod

File `pvc-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pvc-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: pvc-demo    # the PVC name
```

```bash
kubectl apply -f pvc-pod.yaml
k apply -f pvc-pod.yaml
```

### Prove the data survives

```bash
# 1. Write a file into the volume
kubectl exec pvc-pod -- sh -c 'echo "I survive pod deletion" > /usr/share/nginx/html/index.html'
k exec pvc-pod -- sh -c 'echo "I survive pod deletion" > /usr/share/nginx/html/index.html'

# 2. Delete the pod
kubectl delete pod pvc-pod
k delete pod pvc-pod

# 3. Create it again
kubectl apply -f pvc-pod.yaml
k apply -f pvc-pod.yaml

# 4. The file is still there
kubectl exec pvc-pod -- cat /usr/share/nginx/html/index.html
k exec pvc-pod -- cat /usr/share/nginx/html/index.html
```

### Dynamic provisioning (PVC without a manual PV)

```bash
kubectl get storageclass          # short: sc ; look for "(default)"
k get sc
```

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-dynamic
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  # no storageClassName: the default StorageClass creates a PV automatically
```

```bash
kubectl apply -f pvc-dynamic.yaml
kubectl get pv,pvc               # a new PV appears by itself
k apply -f pvc-dynamic.yaml
k get pv,pvc
```

### Inspect and delete

```bash
kubectl describe pv pv-demo
k describe pv pv-demo

kubectl describe pvc pvc-demo        # Events explain why it is Pending
k describe pvc pvc-demo

# Delete in this order: pod first, then PVC, then PV
kubectl delete pod pvc-pod
kubectl delete pvc pvc-demo
kubectl delete pv pv-demo
k delete pod pvc-pod
k delete pvc pvc-demo
k delete pv pv-demo
```

With reclaim policy `Retain`, after deleting the PVC the PV becomes `Released` and its data stays on disk until you clean it up.

### Practice Lab: PV and PVC

1. Create `pv-demo` (1Gi, `storageClassName: manual`) and check `k get pv` shows `Available`.
2. Create `pvc-demo` (500Mi, `storageClassName: manual`) and check both show `Bound`.
3. Create `pvc-pod` using the PVC. Write a file inside `/usr/share/nginx/html`.
4. Delete the pod, recreate it, and confirm the file still exists.
5. Delete pod, PVC and PV in that order. Check the PV status at each step.

### Troubleshooting volumes

| Symptom | Cause and fix |
|---------|---------------|
| PVC stuck in `Pending` | No matching PV (size, access mode or `storageClassName` differ), or no default StorageClass. Read `k describe pvc` Events |
| Pod stuck in `Pending` or `ContainerCreating` | PVC is not Bound yet, or volume cannot be mounted. `k describe pod` |
| PV shows `Released` and will not rebind | Old claim reference remains. Delete and recreate the PV, or edit out `claimRef` |
| Data lost after pod deletion | You used `emptyDir`. Use a PVC |
| Cannot delete PVC (stuck `Terminating`) | A pod is still using it. Delete the pod first |

---

# Module 10: DaemonSet

## Theory

### What is a DaemonSet?

A **DaemonSet** makes sure **exactly one copy of a pod runs on every node** (or on selected nodes).

- A new node joins the cluster: the DaemonSet automatically starts a pod on it.
- A node is removed: its pod is cleaned up.
- You do **not** set `replicas`. The number of pods equals the number of matching nodes.

Analogy: a security guard posted at **every building** in a campus. A new building opens, a new guard is posted automatically.

```
  Node 1: [DS pod]      Node 2: [DS pod]      Node 3: [DS pod]
```

### Typical use cases

| Use case | Example tools |
|----------|---------------|
| Log collection | Fluentd, Filebeat |
| Node monitoring | Prometheus node-exporter, Datadog agent |
| Networking | `kube-proxy`, CNI plugins (Calico, Flannel) |
| Storage agents | Ceph, GlusterFS daemons |

You can see real DaemonSets in your cluster: `k get ds -n kube-system` (you will find `kube-proxy` and your CNI plugin).

### DaemonSet vs Deployment

| | Deployment | DaemonSet |
|---|-----------|-----------|
| Number of pods | You choose `replicas` | One per node, automatic |
| Pod placement | Scheduler picks any node | One on each node |
| Typical use | Web apps, APIs | Node-level agents |

### Control plane nodes and tolerations

Control plane nodes usually have a **taint** that stops normal pods from running there. A DaemonSet pod will not appear on them unless you add a **toleration**.

```yaml
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
```

### Run only on some nodes

Add a `nodeSelector` in the pod template, for example `nodeSelector: { disk: ssd }`, and label the nodes with `k label node <node> disk=ssd`.

### Updates

DaemonSets support `RollingUpdate` (default) and `OnDelete` (pods are replaced only when you delete them manually).

## Commands

### Create a DaemonSet

There is no `kubectl create daemonset` command. Use YAML. **Fast trick:** generate a Deployment YAML, then change it.

```bash
kubectl create deployment monitoring-daemon --image=nginx:alpine --dry-run=client -o yaml > ds.yaml
k create deployment monitoring-daemon --image=nginx:alpine --dry-run=client -o yaml > ds.yaml

vi ds.yaml
# Change:  kind: Deployment  ->  kind: DaemonSet
# Remove:  replicas: 1
# Remove:  strategy: {}
# Remove:  status: {}
```

Final file `monitoring-daemon.yaml`:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: monitoring-daemon
spec:
  selector:
    matchLabels:
      app: monitoring-agent
  template:
    metadata:
      labels:
        app: monitoring-agent
    spec:
      containers:
      - name: monitoring-agent
        image: nginx:alpine
```

```bash
kubectl apply -f monitoring-daemon.yaml
k apply -f monitoring-daemon.yaml
```

### View and manage

```bash
kubectl get daemonsets                 # short name: ds
k get ds

kubectl get ds -n kube-system          # real examples: kube-proxy, CNI
k get ds -n kube-system

kubectl get ds -A                      # all namespaces
k get ds -A

kubectl get pods -o wide               # one pod on each NODE
k get pods -o wide

kubectl describe ds monitoring-daemon
k describe ds monitoring-daemon

kubectl rollout status ds/monitoring-daemon
k rollout status ds/monitoring-daemon

kubectl set image ds/monitoring-daemon monitoring-agent=nginx:1.25
k set image ds/monitoring-daemon monitoring-agent=nginx:1.25

kubectl rollout undo ds/monitoring-daemon
k rollout undo ds/monitoring-daemon

kubectl delete ds monitoring-daemon
k delete ds monitoring-daemon
```

How to read `k get ds`:

```
NAME                DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR
monitoring-daemon   2         2         2       2            2           <none>
```

`DESIRED` = number of nodes that should run the pod.

### Practice Lab: DaemonSet

1. Run `k get nodes` to count your nodes.
2. Create `monitoring-daemon` from the YAML above.
3. Check `k get ds` and `k get pods -o wide`: there should be one pod per node.
4. Delete one of its pods. It is recreated on the same node.
5. Update the image with `k set image` and watch `k rollout status ds/monitoring-daemon`.
6. Look at `k get ds -n kube-system` and find `kube-proxy`.
7. Delete the DaemonSet.

### Troubleshooting DaemonSet

| Symptom | Cause and fix |
|---------|---------------|
| No pod on the control plane node | Node taint. Add a toleration |
| `DESIRED` is `0` | `nodeSelector` matches no node. Check node labels with `k get nodes --show-labels` |
| Pod stuck `Pending` on one node | Not enough resources or taint on that node. `k describe pod` |

---

# Module 11: StatefulSet

## Theory

### What is a StatefulSet?

A **StatefulSet** runs pods that need a **stable identity and their own storage**, such as databases (MySQL, PostgreSQL, MongoDB) and systems like Kafka or Elasticsearch.

With a Deployment, pods are identical and interchangeable: random names, shared or no storage, any pod can be replaced by any other. With a database, each pod is **different** (one is the primary, others are replicas) and each needs **its own data**. That is what a StatefulSet provides.

### The 4 guarantees of a StatefulSet

| Guarantee | What it means |
|-----------|---------------|
| **Stable pod names** | `web-0`, `web-1`, `web-2` (not random). A recreated pod keeps its name. |
| **Ordered start and stop** | Pods start one by one: `web-0`, then `web-1`, then `web-2`. They stop in reverse order. |
| **Stable network identity** | Each pod has a fixed DNS name through a **headless Service**. |
| **Stable storage** | Each pod gets its **own PVC**. When the pod is recreated, it reattaches to the same PVC and the same data. |

### Deployment vs StatefulSet

| | Deployment | StatefulSet |
|---|-----------|-------------|
| Pod names | Random (`web-7d9f-xk2lp`) | Ordered (`web-0`, `web-1`) |
| Start order | All at once | One by one (default) |
| Storage | Shared or none | Separate PVC per pod |
| Network identity | Changes when pod is replaced | Stable DNS per pod |
| Use for | Stateless apps (web, API) | Stateful apps (databases, queues) |

### Headless Service

A normal Service gives one virtual IP. A **headless Service** (`clusterIP: None`) has **no virtual IP**. Instead, DNS returns the **individual pod addresses**, and each pod gets its own DNS name:

```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
web-0.web-svc.default.svc.cluster.local
web-1.web-svc.default.svc.cluster.local
```

The StatefulSet field `serviceName` must name this headless Service.

### volumeClaimTemplates

Instead of one PVC for all pods, you give a **template**. Kubernetes creates a PVC per pod automatically:

```
web-0  ->  PVC data-web-0
web-1  ->  PVC data-web-1
web-2  ->  PVC data-web-2
```

Important: when you delete a pod or scale down, **the PVCs are kept** so data is safe. You must delete PVCs yourself.

This needs dynamic provisioning (a default StorageClass) or pre-created PVs. If none exists, the PVCs stay `Pending`.

### Other points

- **podManagementPolicy:** `OrderedReady` (default) or `Parallel` (start all together, ordering not required).
- **Updates:** RollingUpdate goes in **reverse order** (`web-2`, then `web-1`, then `web-0`).
- Deleting a StatefulSet does **not** guarantee ordered shutdown. To stop in order, scale it to 0 first.

## Commands

### Create a StatefulSet

There is no `kubectl create statefulset`. Use YAML. File `web-statefulset.yaml` (headless Service and StatefulSet together):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  clusterIP: None            # headless
  selector:
    app: web
  ports:
  - port: 80
    name: web
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: web-svc       # must match the headless Service name
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: data
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

Tip: you can generate a starting point from a Deployment (`k create deployment ... --dry-run=client -o yaml`), then change `kind` to `StatefulSet` and add `serviceName` and `volumeClaimTemplates`.

```bash
kubectl apply -f web-statefulset.yaml
k apply -f web-statefulset.yaml
```

### Watch the ordered startup

```bash
kubectl get pods -w          # -w = watch; web-0 first, then web-1, then web-2
k get pods -w
```

### View and manage

```bash
kubectl get statefulsets             # short name: sts
k get sts

kubectl get pods -l app=web
k get pods -l app=web

kubectl get pvc                      # data-web-0, data-web-1, data-web-2
k get pvc

kubectl describe sts web
k describe sts web

kubectl scale sts web --replicas=5   # adds web-3, web-4 in order
k scale sts web --replicas=5

kubectl scale sts web --replicas=2   # removes web-4, web-3, web-2 in reverse order
k scale sts web --replicas=2

kubectl rollout status sts/web
k rollout status sts/web

kubectl set image sts/web nginx=nginx:1.25
k set image sts/web nginx=nginx:1.25

kubectl rollout undo sts/web
k rollout undo sts/web
```

### Prove stable identity and storage

```bash
# 1. Write unique data into web-0
kubectl exec web-0 -- sh -c 'echo "hello from web-0" > /usr/share/nginx/html/index.html'
k exec web-0 -- sh -c 'echo "hello from web-0" > /usr/share/nginx/html/index.html'

# 2. Delete the pod
kubectl delete pod web-0
k delete pod web-0

# 3. A new pod with the SAME name appears and reattaches to the SAME PVC
kubectl get pods -w
k get pods -w

# 4. The data is still there
kubectl exec web-0 -- cat /usr/share/nginx/html/index.html
k exec web-0 -- cat /usr/share/nginx/html/index.html
```

### Test the stable DNS name

```bash
kubectl run dns-test --image=busybox:1.28 --rm -it --restart=Never -- nslookup web-0.web-svc
k run dns-test --image=busybox:1.28 --rm -it --restart=Never -- nslookup web-0.web-svc
```

### Clean up (the PVCs stay unless you delete them)

```bash
kubectl delete sts web
kubectl delete svc web-svc
kubectl get pvc                                  # they are still here
kubectl delete pvc data-web-0 data-web-1 data-web-2

k delete sts web
k delete svc web-svc
k get pvc
k delete pvc data-web-0 data-web-1 data-web-2
```

### Practice Lab: StatefulSet

1. Create the headless Service and StatefulSet from the YAML above.
2. Watch with `k get pods -w` and note the order `web-0`, `web-1`, `web-2`.
3. Run `k get pvc` and find one PVC per pod.
4. Write a different file in `web-0` and `web-1`, delete both pods, and confirm each keeps its own data.
5. Scale to 5, then back to 2, and note which pods are removed first.
6. Check the DNS name `web-0.web-svc` with a test pod.
7. Delete the StatefulSet, then delete the PVCs.

### Troubleshooting StatefulSet

| Symptom | Cause and fix |
|---------|---------------|
| `web-0` stays `Pending` | PVC is `Pending` (no default StorageClass or no PV). `k describe pvc data-web-0` |
| `web-1` never starts | Ordered startup: `web-0` is not Ready yet. Fix `web-0` first |
| DNS name does not resolve | Headless Service missing, or `serviceName` does not match, or selector labels differ |
| Old data appears in a "new" setup | PVCs were kept from a previous StatefulSet. Delete the PVCs to start clean |

---

## Workload Comparison: Deployment vs DaemonSet vs StatefulSet

| | Deployment | DaemonSet | StatefulSet |
|---|-----------|-----------|-------------|
| Purpose | Stateless apps | One pod per node | Stateful apps |
| Number of pods | `replicas` | One per node | `replicas` |
| Pod names | Random | Random | Ordered (`name-0`, `name-1`) |
| Storage | Shared or none | Usually host paths | Own PVC per pod |
| Needs headless Service | No | No | Yes (`serviceName`) |
| Example | Web server, API | Log collector, `kube-proxy` | MySQL, Kafka |
| Short name | `deploy` | `ds` | `sts` |

---

# Module 12: Master Quick Reference

| Task | kubectl | k |
|------|---------|---|
| Cluster info | `kubectl cluster-info` | `k cluster-info` |
| List nodes | `kubectl get nodes -o wide` | `k get nodes -o wide` |
| List namespaces | `kubectl get namespaces` | `k get ns` |
| Create namespace | `kubectl create namespace <name>` | `k create ns <name>` |
| All namespaces | `kubectl get pods --all-namespaces` | `k get pods -A` |
| List pods | `kubectl get pods` | `k get pods` |
| Pods with node and IP | `kubectl get pods -o wide` | `k get pods -o wide` |
| Pods with labels | `kubectl get pods --show-labels` | `k get pods --show-labels` |
| Pod details | `kubectl describe pod <name>` | `k describe pod <name>` |
| Create pod | `kubectl run <name> --image=<image>` | `k run <name> --image=<image>` |
| Generate pod YAML | `kubectl run <name> --image=<img> --dry-run=client -o yaml` | `k run <name> --image=<img> --dry-run=client -o yaml` |
| Create from file | `kubectl apply -f <file>` | `k apply -f <file>` |
| Force recreate from file | `kubectl replace --force -f <file>` | `k replace --force -f <file>` |
| Change pod image | `kubectl set image pod/<name> <container>=<img>` | `k set image pod/<name> <container>=<img>` |
| Edit live object | `kubectl edit <type> <name>` | `k edit <type> <name>` |
| Pod logs | `kubectl logs <pod> -c <container>` | `k logs <pod> -c <container>` |
| Shell in pod | `kubectl exec -it <pod> -- sh` | `k exec -it <pod> -- sh` |
| Delete pod | `kubectl delete pod <name>` | `k delete pod <name>` |
| Delete all pods | `kubectl delete pods --all` | `k delete pods --all` |
| Delete pods by label | `kubectl delete pods -l <key>=<value>` | `k delete pods -l <key>=<value>` |
| List ReplicaSets | `kubectl get rs` | `k get rs` |
| Scale ReplicaSet | `kubectl scale rs <name> --replicas=<n>` | `k scale rs <name> --replicas=<n>` |
| Update ReplicaSet image | `kubectl set image rs/<name> <container>=<image>` | `k set image rs/<name> <container>=<image>` |
| Delete ReplicaSet | `kubectl delete rs <name>` | `k delete rs <name>` |
| Create deployment | `kubectl create deployment <name> --image=<image>` | `k create deployment <name> --image=<image>` |
| Generate deployment YAML | `kubectl create deployment <name> --image=<img> --replicas=<n> --dry-run=client -o yaml > <file>` | `k create deployment <name> --image=<img> --replicas=<n> --dry-run=client -o yaml > <file>` |
| Scale deployment | `kubectl scale deployment <name> --replicas=<n>` | `k scale deployment <name> --replicas=<n>` |
| Update deployment image | `kubectl set image deployment/<name> <container>=<image>` | `k set image deployment/<name> <container>=<image>` |
| Rollout status | `kubectl rollout status deployment/<name>` | `k rollout status deployment/<name>` |
| Rollout history | `kubectl rollout history deployment/<name>` | `k rollout history deployment/<name>` |
| Roll back | `kubectl rollout undo deployment/<name>` | `k rollout undo deployment/<name>` |
| Roll back to revision | `kubectl rollout undo deployment/<name> --to-revision=<n>` | `k rollout undo deployment/<name> --to-revision=<n>` |
| Restart deployment | `kubectl rollout restart deployment/<name>` | `k rollout restart deployment/<name>` |
| Delete deployment | `kubectl delete deployment <name>` | `k delete deployment <name>` |
| Expose as ClusterIP | `kubectl expose deployment <name> --port=<p>` | `k expose deploy <name> --port=<p>` |
| Expose as NodePort | `kubectl expose deployment <name> --port=<p> --type=NodePort` | `k expose deploy <name> --port=<p> --type=NodePort` |
| Expose as LoadBalancer | `kubectl expose deployment <name> --port=<p> --type=LoadBalancer` | `k expose deploy <name> --port=<p> --type=LoadBalancer` |
| Expose a pod | `kubectl expose pod <name> --port=<p> --name=<svc>` | `k expose pod <name> --port=<p> --name=<svc>` |
| List services | `kubectl get svc` | `k get svc` |
| Service endpoints | `kubectl get endpoints` | `k get ep` |
| Port-forward | `kubectl port-forward svc/<name> 8080:80` | `k port-forward svc/<name> 8080:80` |
| Delete service | `kubectl delete svc <name>` | `k delete svc <name>` |
| Count items | `kubectl get <type> --no-headers` then add `wc -l` | `k get <type> --no-headers` then add `wc -l` |
| Create secret | `kubectl create secret generic <name> --from-literal=<key>=<value>` | `k create secret generic <name> --from-literal=<key>=<value>` |
| Decode secret value | `kubectl get secret <name> -o jsonpath='{.data.<key>}' \| base64 -d` | `k get secret <name> -o jsonpath='{.data.<key>}' \| base64 -d` |
| List PV and PVC | `kubectl get pv,pvc` | `k get pv,pvc` |
| List StorageClasses | `kubectl get storageclass` | `k get sc` |
| List DaemonSets | `kubectl get daemonsets` | `k get ds` |
| List StatefulSets | `kubectl get statefulsets` | `k get sts` |
| Scale StatefulSet | `kubectl scale sts <name> --replicas=<n>` | `k scale sts <name> --replicas=<n>` |
| Watch pods live | `kubectl get pods -w` | `k get pods -w` |
| Explain a field | `kubectl explain <path>` | `k explain <path>` |

---

# Module 13: New Topics (future additions)

New questions and commands will be added below as new modules.

