# K Practice Notes: Inspecting, Troubleshooting and Fixing Pods

Every command is shown in both `kubectl` (full) and `k` (short alias) form.

> Set up the alias first: `alias k=kubectl`

Note: answers that depend on your lab (node names, pod suffixes, image names) are found by running the commands below. The sample outputs are only examples of what you should see.

---

## 1. Which image is specified for the pods whose names begin with `newpods-`?

First list the pods:

```bash
kubectl get pods
```

```bash
k get pods
```

Then describe one of the `newpods-xxxxx` pods and look at the `Image:` line:

```bash
kubectl describe pod newpods-xxxxx | grep Image
```

```bash
k describe pod newpods-xxxxx | grep Image
```

Faster, for all `newpods-` pods at once (image names only):

```bash
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}' | grep newpods
```

```bash
k get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}' | grep newpods
```

Or use wide output, which has an IMAGES column:

```bash
kubectl get pods -o wide
```

```bash
k get pods -o wide
```

---

## 2. Which nodes are these pods placed on?

The `-o wide` output has a NODE column:

```bash
kubectl get pods -o wide
```

```bash
k get pods -o wide
```

Example output:

```
NAME             READY   STATUS    RESTARTS   AGE   IP           NODE
newpods-abcde    1/1     Running   0          5m    10.244.0.5   controlplane
```

You can also see it inside `describe`, on the `Node:` line:

```bash
kubectl describe pod newpods-xxxxx | grep Node
```

```bash
k describe pod newpods-xxxxx | grep Node
```

---

## 3. We just created a new pod named `webapp`. How many containers are part of it?

Look at the READY column. The number after the slash is the total number of containers:

```bash
kubectl get pod webapp
```

```bash
k get pod webapp
```

Example: `READY 1/2` means 2 containers in total, 1 of them ready.

To count and list the container names exactly:

```bash
kubectl get pod webapp -o jsonpath='{.spec.containers[*].name}'
```

```bash
k get pod webapp -o jsonpath='{.spec.containers[*].name}'
```

Or read the `Containers:` section of describe:

```bash
kubectl describe pod webapp
```

```bash
k describe pod webapp
```

---

## 4. What images are used in the new `webapp` pod?

You must look at every container in detail. Do not stop at the first one.

```bash
kubectl describe pod webapp
```

```bash
k describe pod webapp
```

Under `Containers:` each container has its own `Image:` line. Or print all of them in one go:

```bash
kubectl get pod webapp -o jsonpath='{range .spec.containers[*]}{.name}{"\t"}{.image}{"\n"}{end}'
```

```bash
k get pod webapp -o jsonpath='{range .spec.containers[*]}{.name}{"\t"}{.image}{"\n"}{end}'
```

---

## 5. What is the state of the container `agentx` in the pod `webapp`?

```bash
kubectl describe pod webapp
```

```bash
k describe pod webapp
```

Find the `agentx:` block under `Containers:` and read `State:` and `Reason:`. A failing container usually looks like this:

```
agentx:
  Image:   agentx
  State:   Waiting
    Reason: ImagePullBackOff
```

(It may briefly show `ErrImagePull` first, then change to `ImagePullBackOff`.)

---

## 6. Why is the container `agentx` in error?

Scroll to the `Events:` section at the bottom of `describe`:

```bash
kubectl describe pod webapp
```

```bash
k describe pod webapp
```

Typical events:

```
Failed to pull image "agentx": ... pull access denied, repository does not exist or may require authorization
Error: ErrImagePull
Back-off pulling image "agentx"
Error: ImagePullBackOff
```

Reason: the image `agentx` cannot be pulled, because it does not exist in the registry (or needs authentication). Kubernetes retries with a growing delay, which is what `BackOff` means.

You can also check events directly:

```bash
kubectl get events --field-selector involvedObject.name=webapp
```

```bash
k get events --field-selector involvedObject.name=webapp
```

---

## 7. What does the READY column in `kubectl get pods` indicate?

Format: `ready containers / total containers` in the pod.

| READY | Meaning |
|-------|---------|
| `1/1` | 1 container in the pod, and it is ready |
| `2/2` | 2 containers, both ready |
| `1/2` | 2 containers, only 1 ready (the other is failing or starting) |
| `0/1` | 1 container, not ready yet |

So for `webapp`, a value like `1/2` tells you one container is healthy and one (`agentx`) is not.

---

## 8. Delete the `webapp` Pod

```bash
kubectl delete pod webapp
```

```bash
k delete pod webapp
```

Faster option (skips the graceful wait, useful in practice labs):

```bash
kubectl delete pod webapp --force --grace-period=0
```

```bash
k delete pod webapp --force --grace-period=0
```

---

## 9. Create a pod `redis` with image `redis123` using a pod-definition YAML

Important: `redis123` is intentionally wrong. Do not fix it yet.

Step 1: generate the YAML skeleton instead of typing it from scratch:

```bash
kubectl run redis --image=redis123 --dry-run=client -o yaml > redis-pod.yaml
```

```bash
k run redis --image=redis123 --dry-run=client -o yaml > redis-pod.yaml
```

Step 2: the file `redis-pod.yaml` looks like this (extra empty fields can be removed):

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

Step 3: create the pod from the file:

```bash
kubectl apply -f redis-pod.yaml
```

```bash
k apply -f redis-pod.yaml
```

(`kubectl create -f redis-pod.yaml` / `k create -f redis-pod.yaml` also works.)

Step 4: check the status. It should show an image error:

```bash
kubectl get pod redis
```

```bash
k get pod redis
```

```
NAME    READY   STATUS             RESTARTS   AGE
redis   0/1     ImagePullBackOff   0          30s
```

---

## 10. Change the image on the `redis` pod to `redis`

The `image` field of a running pod can be changed in place. Pick any one of these three methods.

**Method A: `set image` (fastest)**

```bash
kubectl set image pod/redis redis=redis
```

```bash
k set image pod/redis redis=redis
```

Format: `<container-name>=<new-image>`. Here the container name is `redis` (the `name:` in the YAML), and the new image is `redis`.

**Method B: edit the live object**

```bash
kubectl edit pod redis
```

```bash
k edit pod redis
```

Change `image: redis123` to `image: redis`, save and exit.

**Method C: edit the YAML file and re-apply**

Change `image: redis123` to `image: redis` in `redis-pod.yaml`, then:

```bash
kubectl apply -f redis-pod.yaml
```

```bash
k apply -f redis-pod.yaml
```

**Verify the pod is now running:**

```bash
kubectl get pod redis
```

```bash
k get pod redis
```

```
NAME    READY   STATUS    RESTARTS   AGE
redis   1/1     Running   0          2m
```

Confirm the image:

```bash
kubectl describe pod redis | grep Image
```

```bash
k describe pod redis | grep Image
```

---

## Pod Status Cheat Sheet

| Status | Meaning | First thing to check |
|--------|---------|----------------------|
| `Pending` | Accepted but not scheduled/started yet | `describe` events: resources, node, scheduling |
| `ContainerCreating` | Pulling image / setting up | Wait, or check events |
| `Running` | At least one container running | READY column |
| `ErrImagePull` | Image pull failed | Image name, tag, registry access |
| `ImagePullBackOff` | Retrying image pull with delay | Same as above |
| `CrashLoopBackOff` | Container keeps crashing | `logs` and `logs --previous` |
| `Completed` | Container finished successfully | Normal for jobs |
| `Error` | Container exited with failure | `logs` |

## Troubleshooting Flow

1. `k get pods` and look at STATUS and READY.
2. `k describe pod <name>` and read the `Containers:` section and the `Events:` section.
3. `k logs <name>` (add `-c <container>` for multi-container pods).
4. Fix the cause (image, command, config), then re-check with `k get pod <name>`.

## Quick Command Reference

| Task | kubectl | k |
|------|---------|---|
| List pods | `kubectl get pods` | `k get pods` |
| Pods with node and IP | `kubectl get pods -o wide` | `k get pods -o wide` |
| Pod details | `kubectl describe pod <name>` | `k describe pod <name>` |
| Image of a pod | `kubectl describe pod <name> \| grep Image` | `k describe pod <name> \| grep Image` |
| Container logs | `kubectl logs <name> -c <container>` | `k logs <name> -c <container>` |
| Generate pod YAML | `kubectl run <name> --image=<img> --dry-run=client -o yaml` | `k run <name> --image=<img> --dry-run=client -o yaml` |
| Create from file | `kubectl apply -f <file>` | `k apply -f <file>` |
| Change pod image | `kubectl set image pod/<name> <container>=<img>` | `k set image pod/<name> <container>=<img>` |
| Edit live pod | `kubectl edit pod <name>` | `k edit pod <name>` |
| Delete pod | `kubectl delete pod <name>` | `k delete pod <name>` |
