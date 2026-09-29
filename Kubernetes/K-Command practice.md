# K-Command Practice

Kubernetes practice: pods and deployments. Every command is shown in both `kubectl` (full) and `k` (short alias) form.

> Set up the alias first: `alias k=kubectl`

---

## 1. Create a pod called `my-pod` of image `nginx:alpine`

```bash
kubectl run my-pod --image=nginx:alpine
```

```bash
k run my-pod --image=nginx:alpine
```

---

## 2. Delete the pod called `my-pod`

```bash
kubectl delete pod my-pod
```

```bash
k delete pod my-pod
```

---

## 3. Create a deployment called `my-first-deployment` of image `nginx:alpine` in the default namespace

```bash
kubectl create deployment my-first-deployment --image=nginx:alpine -n default
```

```bash
k create deployment my-first-deployment --image=nginx:alpine -n default
```

---

## 4. Scale `my-first-deployment` up to run 3 replicas

```bash
kubectl scale deployment my-first-deployment --replicas=3
```

```bash
k scale deployment my-first-deployment --replicas=3
```

---

## 5. Check to make sure all 3 replicas are ready

```bash
kubectl get deployment my-first-deployment
```

```bash
k get deployment my-first-deployment
```

The READY column should show `3/3`.

Other ways to check:

```bash
kubectl get pods -l app=my-first-deployment
kubectl rollout status deployment my-first-deployment
```

```bash
k get pods -l app=my-first-deployment
k rollout status deployment my-first-deployment
```

---

## 6. Scale `my-first-deployment` down to run 2 replicas

```bash
kubectl scale deployment my-first-deployment --replicas=2
```

```bash
k scale deployment my-first-deployment --replicas=2
```

---

## 7. Check to make sure all 2 replicas are ready

```bash
kubectl get deployment my-first-deployment
```

```bash
k get deployment my-first-deployment
```

The READY column should show `2/2`.

---

## 8. Change the image `my-first-deployment` runs from `nginx:alpine` to `httpd:alpine`

The container name defaults to `nginx` (from the original image name).

```bash
kubectl set image deployment/my-first-deployment nginx=httpd:alpine
```

```bash
k set image deployment my-first-deployment nginx=httpd:alpine
```

Verify the rollout:

```bash
kubectl rollout status deployment my-first-deployment
kubectl describe deployment my-first-deployment | grep Image
```

```bash
k rollout status deployment my-first-deployment
k describe deployment my-first-deployment | grep Image
```

---

## 9. Delete the deployment `my-first-deployment`

```bash
kubectl delete deployment my-first-deployment
```

```bash
k delete deployment my-first-deployment
```

---

## Quick Reference

| Task | kubectl | k |
|------|---------|---|
| Create pod | `kubectl run <name> --image=<image>` | `k run <name> --image=<image>` |
| Delete pod | `kubectl delete pod <name>` | `k delete pod <name>` |
| Create deployment | `kubectl create deployment <name> --image=<image>` | `k create deployment <name> --image=<image>` |
| Scale deployment | `kubectl scale deployment <name> --replicas=<n>` | `k scale deployment <name> --replicas=<n>` |
| Check status | `kubectl get deployment <name>` | `k get deployment <name>` |
| Update image | `kubectl set image deployment/<name> <container>=<image>` | `k set image deployment/<name> <container>=<image>` |
| Delete deployment | `kubectl delete deployment <name>` | `k delete deployment <name>` |
