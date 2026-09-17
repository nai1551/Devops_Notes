# Jenkins CI/CD with Docker — What I Learned Today

This documents the full CI/CD workflow built today: taking a Docker project from manual `docker run` commands to a fully automated Jenkins pipeline that checks out code, tests it, builds an image, pushes it to Docker Hub, and deploys it — all triggered by one click (or eventually, a git push).

---

## 1. The Big Picture

```
Push code to GitHub
        │
        ▼
Jenkins pulls the code (Checkout)
        │
        ▼
Docker builds a new image (Build)
        │
        ▼
Automated tests run inside that image (Test)
        │
        ▼
   Tests pass? ──No──▶ STOP. Nothing pushed, nothing deployed.
        │ Yes
        ▼
Image is tagged (v1, v2, v3...) and pushed to Docker Hub (Push)
        │
        ▼
Old container is removed, new one is started (Deploy)
        │
        ▼
A health check confirms the app actually responds (Verify)
```

This is a real CI/CD loop — the same mental model used in production systems, just running at a smaller, single-machine scale.

---

## 2. Prerequisites Set Up Today

- **Jenkins** installed and running (as a system service on Ubuntu, alongside Docker)
- **Docker** already installed on the same Ubuntu machine as Jenkins
- The `jenkins` system user added to the `docker` group, so Jenkins can run Docker commands:
  ```bash
  sudo usermod -aG docker jenkins
  sudo systemctl restart jenkins
  ```
- Confirmed with:
  ```bash
  groups jenkins
  sudo systemctl status jenkins
  ```
- A **Docker Hub account** and repository (`naim8855/flask-app`) to push images to
- **Docker Hub credentials** added inside Jenkins (not in any file), so the pipeline can log in securely:
  - Jenkins → Manage Jenkins → Credentials → Add Credentials
  - Kind: Username with password
  - ID: `dockerhub-creds` (referenced by name in the Jenkinsfile — the actual password never appears in code)
- **GitHub repository** holding the project source, including the `Jenkinsfile` itself (Pipeline as Code)

---

## 3. Key Concepts Learned

### Pipeline as Code
The entire CI/CD process is described in a `Jenkinsfile`, committed to the same git repo as the application code. This means the build/deploy process is version-controlled, reviewable, and travels with the project — not configured by hand in Jenkins' UI.

### Stages run in order, and failures stop the chain automatically
Declarative Jenkins pipelines execute `stages` top to bottom. If any stage fails, **every stage after it is automatically skipped** — no manual `if` logic needed. This was proven directly: an early permission error caused every later stage to show `"skipped due to earlier failure(s)"`.

### Secrets never live in the Jenkinsfile
Docker Hub credentials are stored in Jenkins' encrypted credential store and referenced only by an ID (`dockerhub-creds`). The Jenkinsfile itself — which lives in a public git repo — never contains an actual password.

```groovy
withCredentials([usernamePassword(
    credentialsId: 'dockerhub-creds',
    usernameVariable: 'DOCKER_USER',
    passwordVariable: 'DOCKER_PASS'
)]) {
    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
}
```

### Version tagging with `BUILD_NUMBER`
Jenkins provides a built-in, auto-incrementing variable, `BUILD_NUMBER`, used to tag every image uniquely:

```groovy
IMAGE_TAG = "v${BUILD_NUMBER}"
```

Every pipeline run produces `v1`, `v2`, `v3`... on Docker Hub, plus a `latest` tag that always points to the newest build. This means any previous version can be redeployed manually if a new one breaks something.

### Idempotent setup stages
Network and volume creation were written so they only create the resource if it doesn't already exist — safe to run on every single pipeline execution without erroring:

```groovy
sh '''
    docker network inspect $NETWORK_NAME >/dev/null 2>&1 || \
    docker network create $NETWORK_NAME
'''
```

### Automated tests gate the deployment
A `Run Tests` stage runs `pytest` **inside the freshly built image itself** (using `docker run --rm`), before the image is ever pushed to Docker Hub or deployed. If tests fail, the broken code never reaches production — proven by deliberately breaking the app's SQL query and watching the pipeline stop before `Push Image`.

---

## 4. The Full Jenkinsfile (Flask + MySQL Project)

```groovy
pipeline {
    agent any

    environment {
        IMAGE_REPO = "naim8855/flask-app"
        NETWORK_NAME = "myapp-network"
        VOLUME_NAME = "db-data"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Image') {
            steps {
                dir('flask-app') {
                    sh '''
                        docker build -t $IMAGE_REPO:$IMAGE_TAG -t $IMAGE_REPO:latest .
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    docker run --rm $IMAGE_REPO:$IMAGE_TAG python3 -m pytest test_app.py -v
                '''
            }
        }

        stage('Login to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                }
            }
        }

        stage('Push Image') {
            steps {
                sh '''
                    docker push $IMAGE_REPO:$IMAGE_TAG
                    docker push $IMAGE_REPO:latest
                '''
            }
        }

        stage('Ensure Network Exists') {
            steps {
                sh '''
                    docker network inspect $NETWORK_NAME >/dev/null 2>&1 || \
                    docker network create $NETWORK_NAME
                '''
            }
        }

        stage('Ensure Volume Exists') {
            steps {
                sh '''
                    docker volume inspect $VOLUME_NAME >/dev/null 2>&1 || \
                    docker volume create $VOLUME_NAME
                '''
            }
        }

        stage('Start Database') {
            steps {
                sh '''
                    docker rm -f db-container || true
                    docker run -d \
                      --name db-container \
                      --network $NETWORK_NAME \
                      -e MYSQL_ROOT_PASSWORD=rootpass \
                      -e MYSQL_DATABASE=mydb \
                      -e MYSQL_USER=flaskuser \
                      -e MYSQL_PASSWORD=flaskpass \
                      -v $VOLUME_NAME:/var/lib/mysql \
                      mysql:8
                '''
            }
        }

        stage('Wait for Database') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                        docker exec db-container mysqladmin ping -uroot -prootpass --silent && break
                        echo "Waiting for MySQL..."
                        sleep 3
                    done
                '''
            }
        }

        stage('Deploy Flask App') {
            steps {
                sh '''
                    docker rm -f flask-container || true
                    docker run -d \
                      --name flask-container \
                      --network $NETWORK_NAME \
                      -p 5000:5000 \
                      $IMAGE_REPO:$IMAGE_TAG
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    sleep 5
                    curl -f http://localhost:5000
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded — tests passed, deployed ${IMAGE_REPO}:${IMAGE_TAG}"
        }
        failure {
            echo 'Pipeline failed — check the stage logs above. If tests failed, the image was never pushed or deployed.'
        }
        always {
            sh 'docker logout || true'
        }
    }
}
```

---

## 5. Test File (`test_app.py`)

Uses Python's `unittest` + `unittest.mock` to test the Flask routes **without needing a live database** — the MySQL connection is mocked so tests run fast and don't depend on infrastructure being up.

```python
import unittest
from unittest.mock import patch, MagicMock
import app as flask_app


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        self.client = flask_app.app.test_client()
        self.client.testing = True

    @patch("app.get_connection")
    def test_home_page_loads(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add a note", response.data)

    @patch("app.get_connection")
    def test_post_note_inserts_and_redisplays(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, "Test note from pytest")]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.client.post("/", data={"message": "Test note from pytest"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test note from pytest", response.data)
        mock_cursor.execute.assert_any_call(
            "INSERT INTO notes (message) VALUES (%s)", ("Test note from pytest",)
        )

    @patch("app.get_connection")
    def test_empty_message_not_inserted(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        self.client.post("/", data={"message": ""})
        insert_calls = [
            c for c in mock_cursor.execute.call_args_list
            if "INSERT INTO notes" in str(c)
        ]
        self.assertEqual(len(insert_calls), 0)


if __name__ == "__main__":
    unittest.main()
```

**Dockerfile update to support this** — `pytest` and the test file are copied into the image:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
COPY test_app.py .
RUN pip install flask mysql-connector-python pytest
EXPOSE 5000
CMD ["python3", "app.py"]
```

---

## 6. All Commands Used Today

### Jenkins / Docker permission setup
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
groups jenkins
sudo systemctl status jenkins
```

### Docker Hub login and push (manual, before pipeline existed)
```bash
docker login -u naim8855
docker build -t naim8855/flask-app:latest .
docker tag flask-app:latest naim8855/flask-app:latest
docker push naim8855/flask-app:latest
```

### Git — pushing the project with its Jenkinsfile
```bash
cd ~/flask-db-app
git init
git add .
git commit -m "Full CI/CD with versioned tags"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

### Testing the pipeline's build stage locally before trusting Jenkins with it
```bash
docker build -t naim8855/flask-app:test .
docker run -d --name flask-test -p 5000:5000 naim8855/flask-app:test
curl -f http://localhost:5000
docker stop flask-test
docker rm flask-test
```

### Verifying the deployed app after a pipeline run
```bash
docker ps
curl http://localhost:5000
```

### Cleanup
```bash
sudo rm -rf /var/lib/jenkins/workspace/<job-name>   # clear old Jenkins checkout, safe, no rebuild cost
docker images | grep flask-app                       # check what versions exist locally
docker rmi naim8855/flask-app:v1                      # remove a specific old version
docker system df                                       # check overall disk usage before deciding to prune
```

---

## 7. Production-Readiness Self-Check

What was built today is a **real, working CI/CD pipeline** — but not yet a production-grade one. Comparing honestly:

| Practice | Status today |
|---|---|
| Source in git, triggering a pipeline | ✅ Done |
| Automated build → test → tag → push → deploy | ✅ Done |
| Versioned image tags | ✅ Done |
| Secrets kept out of code (Jenkins credential store) | ✅ Done |
| Basic health check after deploy | ✅ Done |
| Automated tests gating deployment | ✅ Done (added today) |
| Rollback strategy | ❌ Manual only — no automated revert |
| Staging environment before production | ❌ Deploys straight to the only environment |
| Zero-downtime deploys | ❌ Old container is killed before new one starts — brief downtime window |
| Monitoring / alerting | ❌ Nothing notifies of a crash |
| Multi-machine redundancy | ❌ Jenkins, Docker, and the app all live on one machine |
| Orchestration (Kubernetes/Swarm) | ❌ Single `docker run`, no scaling or self-healing |

**Takeaway:** the concepts learned today — build, test, tag, push, deploy, verify — are exactly the foundation production CI/CD is built on. Scaling this up to real production mainly means adding redundancy, staging environments, and safer deployment strategies on top of what's already understood, not learning a different system from scratch.

---

## 8. What to Learn Next (Suggested Order)

1. **Move hardcoded secrets** (MySQL passwords currently sit in plain text in the Jenkinsfile) into Jenkins credentials, same pattern as the Docker Hub login
2. **Zero-downtime deploys** — start the new container and confirm it's healthy *before* killing the old one, instead of `docker rm -f` first
3. **Staging vs production branches** — a `dev` branch pipeline that deploys to a test environment, only promoting to `main`/production after manual approval
4. **Rollback automation** — a Jenkins parameter or separate job that redeploys a specific previous version (`vN`) on demand
