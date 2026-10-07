# Voting App on Kubernetes

### Namespace, ConfigMap, Secret, Deployment and Service on a single-node kubeadm + Calico eBPF cluster

| | |
|---|---|
| **Project type** | Hands-on Kubernetes practice project |
| **Application** | Simple "Cats vs Dogs" voting website (Python + Flask) |
| **Cluster** | Single VM, Kubernetes v1.36.5, containerd 2.2.1, Calico v3.33.0 (eBPF, no kube-proxy) |
| **Node IP** | `10.11.204.124` |
| **App URL** | `http://10.11.204.124:30090` |
| **Namespace** | `voting` |
| **Level** | Beginner |

---

## 1. Goal

Run a small application on Kubernetes the way real teams do:

- **Settings live outside the code.** The poll title and options come from a **ConfigMap**.
- **Secrets live outside the code.** The admin username and password come from a **Secret**.
- **Everything is organised.** All resources live in their own **Namespace**, which can be deleted in one command.
- **The app is reachable.** A **Service** opens a port so you can use the app in a browser.

**The main lesson:** after this project you can change the poll title, the options or the admin password **without rebuilding the application**.

---

## 2. Architecture

```text
 You write code ──► Build an image ──► Load image into the cluster
                                              │
 Namespace "voting" (a separate folder)       ▼
 ┌────────────────────────────────────────────────────┐
 │  ConfigMap  (title, options)  ─┐                   │
 │  Secret     (user, password)  ─┼─► Deployment      │
 │                                │   (runs the app)  │
 │                                └──────┬────────────┘
 │  Service (opens a door: port 30090)   │            │
 └───────────────────────────────────────┼────────────┘
                                         ▼
                      Your browser: http://10.11.204.124:30090
```

| Piece | Analogy | Purpose |
|---|---|---|
| **Namespace** | A labelled folder | Keeps this project separate. Deleting it removes everything inside. |
| **ConfigMap** | A public notice board | Holds normal, non-sensitive settings. |
| **Secret** | A locked drawer | Holds the admin username and password. |
| **Deployment** | A manager | Starts the app, restarts it if it crashes, and passes it the settings. |
| **Service** | A reception desk | Gives the app a stable address, because Pod IPs change. |

### What the app does

| URL | Behaviour |
|---|---|
| `/` | Shows the poll title and one button per option. |
| `/vote` (POST) | Adds one vote. |
| `/results` | Shows vote counts. **Protected by the admin username and password from the Secret.** |
| `/healthz` | Returns `ok`. Used by Kubernetes health checks. |

Votes are kept **in memory**, so they reset when the Pod restarts. This keeps the project simple. A database such as Redis is a good next step (Section 12).

---

## 3. Prerequisites

You need a working cluster with these verified:

```bash
kubectl get nodes                      # node is Ready
kubectl get pods -A                    # all Pods Running
kubectl get tigerastatus               # calico AVAILABLE True, DEGRADED False
```

You also need:

- `podman` to build the image (installed in Step 6).
- Internet access on the VM (to download the Python base image).
- `vim` (or `nano`) to create files.

---

## 4. Project structure

```text
~/voting-app/
├── app.py                      # the application
├── Dockerfile                  # recipe to package the app as an image
└── k8s/
    ├── 00-namespace.yaml       # the "folder" for the project
    ├── 01-configmap.yaml       # normal settings
    ├── 02-deployment.yaml      # runs the app
    └── 03-service.yaml         # opens port 30090
```

The Secret is **not** a file. It is created with a command so the password is never saved in a file that could be committed to Git.

---

## 5. Why each step exists

| Step | What you do | Why |
|---|---|---|
| 1 | Create folders | Keep code and Kubernetes files together, ready for Git. |
| 2 | Write `app.py` | The app reads its title, options and credentials from **environment variables**, so Kubernetes can supply different values without changing code. |
| 3 | Write `Dockerfile` | Kubernetes runs **container images**, not source code. The Dockerfile is the recipe. |
| 4 | Write four YAML files | Describe what you want. Files can be versioned and re-applied (infrastructure as code). |
| 5 | Dry run | Catches YAML mistakes before changing anything. |
| 6 | Build with Podman | containerd can run images but cannot build them. |
| 7 | Import into containerd | The lab has no registry, so the image is handed to the node directly. |
| 8 | Create Namespace, then ConfigMap | Everything lives inside the namespace, so it must exist first. |
| 9 | Create Secret by command | Avoids saving a password in a file that could reach GitHub. |
| 10 | Apply Deployment and Service | Starts the app and opens the port. The Secret must exist first, or the Pod fails with `CreateContainerConfigError`. |
| 11 | Verify | Confirms every piece exists and the whole chain works. |
| 12 | Change ConfigMap and Secret | Proves settings can change without a rebuild. |
| 13 | Delete namespace | Removes the whole project in one command. |

---

## 6. Step-by-step build

> **Tip for creating files in vim:** run `vim filename`, type `:set paste` and press Enter, press `i`, paste the content, press `Esc`, then type `:wq` and press Enter. Without `:set paste`, vim auto-indents pasted lines and breaks Python and YAML.

### Step 1: Create the folders

```bash
mkdir -p ~/voting-app/k8s
cd ~/voting-app
```

### Step 2: Create `app.py`

```bash
vim app.py
```

```python
import os
import hmac
import threading
from html import escape
from flask import Flask, request, redirect, Response

app = Flask(__name__)

# ---- Normal settings (come from the ConfigMap) ----
TITLE = os.getenv("POLL_TITLE", "Vote now!")
OPTIONS = [o.strip() for o in os.getenv("OPTIONS", "Yes,No").split(",") if o.strip()]

# ---- Sensitive values (come from the Secret) ----
ADMIN_USER = os.getenv("ADMIN_USER", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

votes = {option: 0 for option in OPTIONS}
lock = threading.Lock()


def page(body):
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>" + escape(TITLE) + "</title></head>"
        "<body style='font-family:sans-serif;max-width:480px;margin:40px auto;padding:0 16px'>"
        + body + "</body></html>"
    )


def authorized():
    auth = request.authorization
    if not ADMIN_USER or not ADMIN_PASSWORD or auth is None:
        return False
    user_ok = hmac.compare_digest((auth.username or "").encode(), ADMIN_USER.encode())
    pass_ok = hmac.compare_digest((auth.password or "").encode(), ADMIN_PASSWORD.encode())
    return user_ok and pass_ok


@app.route("/")
def home():
    buttons = "".join(
        "<form method='POST' action='/vote' style='margin:10px 0'>"
        "<button name='option' value='" + escape(o) + "' "
        "style='font-size:20px;padding:12px 28px;width:100%'>" + escape(o) + "</button></form>"
        for o in OPTIONS
    )
    thanks = "<p style='color:green'>Thanks for voting!</p>" if request.args.get("thanks") else ""
    return page(
        "<h1>" + escape(TITLE) + "</h1>" + thanks + buttons
        + "<p><a href='/results'>Results (admin only)</a></p>"
    )


@app.route("/vote", methods=["POST"])
def vote():
    option = request.form.get("option")
    with lock:
        if option in votes:
            votes[option] += 1
    return redirect("/?thanks=1")


@app.route("/results")
def results():
    if not authorized():
        return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Results"'})
    with lock:
        snapshot = dict(votes)
    total = sum(snapshot.values())
    rows = "".join(
        "<li>" + escape(o) + ": <b>" + str(n) + "</b></li>" for o, n in snapshot.items()
    )
    return page(
        "<h1>Results</h1><ul>" + rows + "</ul><p>Total votes: " + str(total) + "</p>"
        "<p><a href='/'>Back to voting</a></p>"
    )


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

Check that it is valid Python:

```bash
python3 -m py_compile app.py && echo "app.py OK"
```

**Design notes**

- The app contains **no passwords and no poll text**. It only reads environment variables.
- If the Secret is missing, `/results` stays locked instead of falling back to a default password.
- User-supplied text is passed through `escape()` to avoid HTML injection.
- Passwords are compared with `hmac.compare_digest`, which avoids timing leaks.

### Step 3: Create the `Dockerfile`

```bash
vim Dockerfile
```

```dockerfile
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir "flask>=3,<4"
COPY app.py .
RUN useradd -m appuser
USER appuser
EXPOSE 5000
CMD ["python3", "app.py"]
```

The container runs as `appuser`, not root, which is safer if the app is ever attacked.

### Step 4: Create the four Kubernetes files

**`vim k8s/00-namespace.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: voting
```

**`vim k8s/01-configmap.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: voting-config
  namespace: voting
data:
  POLL_TITLE: "Which is the best pet?"
  OPTIONS: "Cats,Dogs,Parrots"
```

**`vim k8s/02-deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voting-app
  namespace: voting
spec:
  replicas: 1
  selector:
    matchLabels:
      app: voting-app
  template:
    metadata:
      labels:
        app: voting-app
    spec:
      containers:
        - name: voting
          image: localhost/voting-app:1.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
          envFrom:
            - configMapRef:
                name: voting-config
            - secretRef:
                name: voting-secret
          readinessProbe:
            httpGet:
              path: /healthz
              port: 5000
            initialDelaySeconds: 3
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 20
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              memory: 128Mi
```

| Field | Meaning |
|---|---|
| `envFrom` | Loads every key from the ConfigMap and the Secret as environment variables. |
| `imagePullPolicy: IfNotPresent` | Use the locally imported image; do not try to download it. |
| `readinessProbe` | Traffic is sent to the Pod only once `/healthz` answers. |
| `livenessProbe` | Kubernetes restarts the container if `/healthz` stops answering. |
| `resources` | Keeps the app small so it cannot use up the VM's RAM. |

**`vim k8s/03-service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: voting-app
  namespace: voting
spec:
  type: NodePort
  selector:
    app: voting-app
  ports:
    - port: 80
      targetPort: 5000
      nodePort: 30090
```

| Field | Meaning |
|---|---|
| `type: NodePort` | Opens a port on the VM so a browser can reach the app. |
| `port: 80` | The port the Service listens on inside the cluster. |
| `targetPort: 5000` | The port the app listens on. Must match `containerPort`. |
| `nodePort: 30090` | The fixed port on the VM (allowed range: 30000 to 32767). |

### Step 5: Dry run

```bash
ls -R ~/voting-app
kubectl apply --dry-run=client -f k8s/
```

Expected: four lines ending in `created (dry run)`. A YAML error names the file and line. Each indentation level uses 2 spaces and **tabs are not allowed**.

### Step 6: Build the image

```bash
sudo apt install -y podman
echo 'unqualified-search-registries = ["docker.io"]' | sudo tee /etc/containers/registries.conf.d/docker.conf

cd ~/voting-app
sudo podman build -t voting-app:1.0 .
```

The `registries.conf.d` line stops Podman from asking which registry `python:3.11-slim` comes from.

### Step 7: Load the image into containerd

```bash
sudo podman save -o /tmp/voting-app.tar localhost/voting-app:1.0
sudo ctr -n k8s.io images import /tmp/voting-app.tar
sudo ctr -n k8s.io images ls | grep voting-app
```

The last command must list `localhost/voting-app:1.0`. If it prints nothing, the import failed. Do not continue until it does.

### Step 8: Create the namespace and ConfigMap

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
```

### Step 9: Create the Secret

```bash
kubectl create secret generic voting-secret \
  --namespace voting \
  --from-literal=ADMIN_USER=admin \
  --from-literal=ADMIN_PASSWORD='Vote_Admin_2026'
```

Replace the example values with your own. Keep the single quotes around the password.

> Kubernetes only **base64-encodes** Secret values. That is encoding, not encryption, so anyone with access to the namespace can decode them. Never commit real Secret values to Git.

### Step 10: Create the Deployment and Service

```bash
kubectl apply -f k8s/02-deployment.yaml -f k8s/03-service.yaml
```

### Step 11: Verify

```bash
kubectl get all,configmap,secret -n voting
```

Expected:

- The Pod is `1/1 Running`.
- The Service shows `80:30090/TCP`.
- The ConfigMap `voting-config` and Secret `voting-secret` exist.

Then test in a browser:

1. Open `http://10.11.204.124:30090`. You should see "Which is the best pet?" with three buttons.
2. Vote a few times.
3. Open `http://10.11.204.124:30090/results`. A wrong password is refused. `admin` with your Secret password shows the counts.

---

## 7. Prove that ConfigMap and Secret drive the app

### Change the ConfigMap

```bash
kubectl patch configmap voting-config -n voting --type merge \
  -p '{"data":{"POLL_TITLE":"Best programming language?","OPTIONS":"Python,Go,Rust,Java"}}'
kubectl rollout restart deployment/voting-app -n voting
kubectl rollout status deployment/voting-app -n voting
```

Reload the page. The title and buttons change with **no rebuild**. The restart is required because an app reads its environment variables only at startup.

### Change the Secret

```bash
kubectl delete secret voting-secret -n voting
kubectl create secret generic voting-secret \
  --namespace voting \
  --from-literal=ADMIN_USER=admin \
  --from-literal=ADMIN_PASSWORD='New_Password_2026'
kubectl rollout restart deployment/voting-app -n voting
```

The old password is now refused at `/results` and the new one works.

### Inspect what Kubernetes stored

```bash
kubectl get secret voting-secret -n voting -o jsonpath='{.data.ADMIN_USER}' | base64 -d; echo
kubectl exec -n voting deploy/voting-app -- env | grep -E 'POLL|OPTIONS|ADMIN'
```

The first command shows how easily a Secret is decoded. That is why Secrets must be protected with access controls and kept out of Git.

---

## 8. Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `ErrImagePull` or `ImagePullBackOff` | Image not loaded into containerd | `sudo ctr -n k8s.io images ls \| grep voting-app` |
| `CreateContainerConfigError` | Secret missing or misnamed | `kubectl get secret -n voting` |
| `CrashLoopBackOff` | Application error | `kubectl logs -n voting deploy/voting-app` |
| `/results` always refuses login | Wrong or stale credentials | Re-create the Secret, then `kubectl rollout restart` |
| Browser cannot connect | Wrong address or port | `kubectl get svc -n voting` (look for `80:30090/TCP`) |
| Pod stays `Pending` | Not enough resources | `kubectl describe pod -n voting <pod-name>` |

Useful commands:

```bash
kubectl get pods -n voting -w                      # watch Pods
kubectl describe pod -n voting <pod-name>          # events at the bottom
kubectl logs -n voting deploy/voting-app           # app output
kubectl get events -n voting --sort-by=.lastTimestamp
```

**Vim problems**

| Problem | Fix |
|---|---|
| Pasted text looks like a staircase | You forgot `:set paste`. Press `Esc`, type `:q!`, reopen the file and redo it. |
| Nothing happens when typing | Press `Esc`, then `i` to enter insert mode. |
| Vim warns about a `.swp` file | A previous session did not close. Choose `(D)elete it`. |

---

## 9. Saving the project to GitHub safely

```bash
cd ~/voting-app
git init
git add app.py Dockerfile k8s/
git status
git commit -m "Voting app with Kubernetes manifests"
git remote add origin <your-repo-url>
git push -u origin main
```

Replace `<your-repo-url>` with your real repository address. Run `git status` first and confirm no file contains a password. The Secret was created from the command line, so none of the committed files should.

---

## 10. Security notes

- **Secrets are base64, not encrypted.** Restrict who can read the namespace.
- **Never commit** real passwords, tokens or the `~/.kube/config` file.
- **Pick your own credentials.** The example values in this document are for practice only.
- **Run as non-root.** The Dockerfile uses `USER appuser`.
- **Keep the NodePort private.** Do not expose this lab to the public internet.

---

## 11. Clean up

```bash
kubectl delete namespace voting
```

This removes the Deployment, Service, ConfigMap and Secret together. To also remove the image:

```bash
sudo ctr -n k8s.io images rm localhost/voting-app:1.0
```

---

## 12. Next steps

1. **Scale to 2 replicas** (`kubectl scale deployment/voting-app -n voting --replicas=2`), vote several times and watch `/results`. The counts are split between Pods because each keeps its own in-memory votes. This shows why shared storage is needed.
2. **Add Redis** in the same namespace and store votes there, using a Secret for its password.
3. **Add a NetworkPolicy** so only the voting Pods can reach Redis.
4. **Practise a rolling update:** change the app text, build `voting-app:1.1`, import it, and update the Deployment image.
5. **Add an Ingress controller** to reach the app by hostname instead of a port.

---

## 13. Verification status

- The application code was tested with Flask's test client: voting works, unknown options are ignored, `/results` returns 401 without credentials or with a wrong password, and returns 200 with the correct ones.
- All four YAML files were checked for valid syntax.
- The image build, import and deployment steps follow the standard Podman and containerd flow. Run them on your cluster and check each "expected" result before moving on.

---

## 14. Quick reference

| Task | Command |
|---|---|
| See everything | `kubectl get all,configmap,secret -n voting` |
| App logs | `kubectl logs -n voting deploy/voting-app` |
| Restart the app | `kubectl rollout restart deployment/voting-app -n voting` |
| Edit the ConfigMap | `kubectl edit configmap voting-config -n voting` |
| Open the app | `http://10.11.204.124:30090` |
| Delete the project | `kubectl delete namespace voting` |
