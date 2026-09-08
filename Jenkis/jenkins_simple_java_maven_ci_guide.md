# Jenkins CI/CD Pipeline — Simple Java Maven App

**Level:** Beginner-friendly
**Goal:** Build a basic Jenkins Continuous Integration (CI) pipeline that checks out a Java project from GitHub, verifies the build tools, compiles it with Maven, runs its tests, and shows the resulting artifact.

---

## Table of Contents

1. [Prerequisites & Glossary](#1-prerequisites--glossary)
2. [Project Overview](#2-project-overview)
3. [Environment](#3-environment)
4. [GitHub Repository](#4-github-repository)
5. [Project Structure](#5-project-structure)
6. [Maven Requirements](#6-maven-requirements)
7. [Why the JDK (Not Just the JRE) Is Required](#7-why-the-jdk-not-just-the-jre-is-required)
8. [Install Java 21 JDK](#8-install-java-21-jdk)
9. [Verify Tools as the Jenkins User](#9-verify-tools-as-the-jenkins-user)
10. [Maven Installation](#10-maven-installation)
11. [Jenkins Service](#11-jenkins-service)
12. [Jenkins Workspace](#12-jenkins-workspace)
13. [The Complete Jenkins Pipeline](#13-the-complete-jenkins-pipeline)
14. [Understanding Each Pipeline Stage](#14-understanding-each-pipeline-stage)
15. [Troubleshooting Reference](#15-troubleshooting-reference)
16. [Final Working Environment](#16-final-working-environment)
17. [Useful Commands Cheat Sheet](#17-useful-commands-cheat-sheet)
18. [What You Learned](#18-what-you-learned)
19. [Recommended Next Step](#19-recommended-next-step)

---

## 1. Prerequisites & Glossary

**Before you start, you should have:**
- Jenkins installed and running on a Linux server.
- `sudo` access to that server.
- A GitHub repository containing a Maven-based Java project.

**Key terms explained:**

| Term | What it means |
|---|---|
| **CI (Continuous Integration)** | Automatically building and testing code every time it changes, to catch problems early. |
| **Maven** | A build tool for Java projects. It compiles code, runs tests, manages dependencies, and packages the result into a `.jar` file, all based on rules in a `pom.xml` file. |
| **JDK vs. JRE** | The **JRE** (Java Runtime Environment) can only *run* Java programs. The **JDK** (Java Development Kit) includes the JRE *plus* the compiler (`javac`) needed to *build* Java programs. Maven needs the JDK. |
| **`pom.xml`** | Maven's configuration file — defines the project's Java version, dependencies, plugins, and build settings. |
| **Jenkinsfile** | A text file (Groovy syntax) that defines the pipeline's stages. It typically lives inside the project's repository. |
| **Declarative Pipeline** | A structured, readable way of writing a Jenkinsfile using a fixed `pipeline { agent { stages { stage { steps { ... } } } } }` layout. |
| **Jenkins agent** | The machine that actually executes a pipeline's steps. `agent any` means "any available machine." |
| **Jenkins workspace** | The working directory Jenkins uses on the agent to check out code and run the build — e.g. `/var/lib/jenkins/workspace/<job-name>`. |
| **`sudo -u jenkins <command>`** | Runs a command *as* the `jenkins` service user, to test that Jenkins itself will see the same tools your normal user account sees. |
| **Build artifact** | The output file(s) produced by a build — here, a `.jar` file. |

---

## 2. Project Overview

This project demonstrates a basic CI pipeline using:

- GitHub
- Jenkins
- Java 21
- Maven 3.9.9
- Git
- Linux
- Jenkins Declarative Pipeline

**The pipeline automatically:**

1. Checks out source code from GitHub.
2. Verifies Java, `javac`, Git, and Maven are available.
3. Builds the Maven application.
4. Runs automated tests.
5. Displays the generated artifact.

### CI Flow

```text
GitHub
  ↓
Jenkins
  ↓
Checkout
  ↓
Verify Tools
  ↓
Maven Build
  ↓
Maven Test
  ↓
Show Artifact
```

---

## 3. Environment

### Architecture

```text
Ansible Master
      │
      │ provisions
      ▼
Worker Server
      │
      └── Jenkins
             │
             └── CI Pipeline
```

Jenkins runs on the worker server, and this pipeline executes there.

### Software Versions Used

| Software | Version |
|---|---|
| Jenkins | 2.568.3 |
| Java | 21.0.12 |
| javac | 21.0.12 |
| Maven | 3.9.9 |
| Git | 2.43.0 |
| OS | Ubuntu Linux |

---

## 4. GitHub Repository

```text
https://github.com/nai1551/simple-java-maven-app.git
```

The repository's default branch is **`master`** (not `main` — this matters, see [Troubleshooting](#15-troubleshooting-reference)).

To check which branches actually exist on a repository before configuring Jenkins:

```bash
git ls-remote --heads https://github.com/nai1551/simple-java-maven-app.git
```

Expected output includes:

```text
refs/heads/master
```

> **Beginner note:** Always verify the branch name yourself rather than assuming. Many tutorials default to `main`, but plenty of existing repositories (like this one) still use `master`. Mismatched branch names are a very common source of Jenkins pipeline failures.

---

## 5. Project Structure

```text
.
├── jenkins
│   ├── Jenkinsfile
│   └── scripts
│       └── deliver.sh
│
├── LICENSE.txt
├── pom.xml
├── README.md
│
├── src
│   ├── main
│   │   └── java/com/mycompany/app/App.java
│   │
│   └── test
│       └── java/com/mycompany/app/AppTest.java
│
└── target
    ├── classes
    ├── test-classes
    ├── surefire-reports
    └── my-app-1.0-SNAPSHOT.jar
```

### Key files explained

| File | Purpose |
|---|---|
| **`pom.xml`** | Maven's project descriptor — defines project info, Java version, dependencies, plugins, build settings, and test configuration. |
| **`App.java`** | The main Java application code. |
| **`AppTest.java`** | Automated tests for the application. |
| **`Jenkinsfile`** | Defines the Jenkins CI pipeline (see [Section 13](#13-the-complete-jenkins-pipeline)). |
| **`target/`** | Generated by Maven at build time — contains compiled classes, test reports, and the final `.jar` artifact. Not committed to Git. |

---

## 6. Maven Requirements

This project requires:

```text
Maven >= 3.9.9
Java  >= 21
```

Verify each tool is installed and on the expected version:

```bash
java --version
javac --version
mvn --version
```

Expected output:

```text
Java 21.0.12
javac 21.0.12
Apache Maven 3.9.9
```

---

## 7. Why the JDK (Not Just the JRE) Is Required

A common problem during the Jenkins build: the Java **runtime** was available (`java --version` worked), but the **compiler** was missing:

```bash
javac --version
```

```text
javac: not found
```

This causes Maven to fail while compiling the project, because Maven needs to invoke the compiler, not just run already-compiled code.

### JRE vs. JDK

| | Contains | Used for |
|---|---|---|
| **JRE** (Java Runtime Environment) | `java` only | Running Java applications |
| **JDK** (Java Development Kit) | `java`, `javac`, and other dev tools | Developing and **compiling** Java applications |

Because Maven needs to *compile* Java source code, the **JDK** is required — the JRE alone is not enough.

---

## 8. Install Java 21 JDK

On Ubuntu:

```bash
sudo apt update
sudo apt install openjdk-21-jdk -y
```

Verify:

```bash
java --version
javac --version
```

Expected output:

```text
openjdk 21.0.12
javac 21.0.12
```

---

## 9. Verify Tools as the Jenkins User

It's important to test tools as the `jenkins` user, because Jenkins runs as its own service account and doesn't necessarily inherit the same environment (`PATH`, installed tools) as your interactive shell.

```bash
sudo -u jenkins bash -c 'java --version'
sudo -u jenkins bash -c 'javac --version'
```

Both commands should succeed and report the same versions as when run under your own user.

---

## 10. Maven Installation

Maven 3.9.9 was installed under:

```text
/opt/apache-maven-3.9.9
```

And made available on the command line via a symlink at:

```text
/usr/local/bin/mvn
```

Verify it works:

```bash
mvn --version
```

Expected:

```text
Apache Maven 3.9.9
```

And, as before, verify it also works as the Jenkins user:

```bash
sudo -u jenkins bash -c 'mvn --version'
```

---

## 11. Jenkins Service

Check whether Jenkins is running:

```bash
sudo systemctl status jenkins
```

Expected status:

```text
active (running)
```

Restart Jenkins when needed (e.g., after installing new tools it should pick up):

```bash
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

---

## 12. Jenkins Workspace

The pipeline runs inside a dedicated Jenkins workspace directory, for example:

```text
/var/lib/jenkins/workspace/simple-java-maven-app
```

Inside the workspace, Jenkins performs:

```text
Workspace
   │
   ├── Clone Git repository
   ├── Compile source
   ├── Run tests
   └── Generate target/
```

The final build artifact ends up in `target/`, inside the workspace.

---

## 13. The Complete Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/nai1551/simple-java-maven-app.git'
            }
        }

        stage('Verify Tools') {
            steps {
                sh '''
                    echo "===== JAVA ====="
                    java --version

                    echo "===== JAVAC ====="
                    javac --version

                    echo "===== JAVA HOME ====="
                    echo "$JAVA_HOME"

                    echo "===== WHICH JAVA ====="
                    which java

                    echo "===== WHICH JAVAC ====="
                    which javac

                    echo "===== MAVEN ====="
                    mvn --version
                '''
            }
        }

        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }

        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }

        stage('Show Artifact') {
            steps {
                sh 'ls -lh target/'
            }
        }
    }
}
```

---

## 14. Understanding Each Pipeline Stage

### `pipeline { ... }` and `agent any`

`pipeline { }` marks this as a Jenkins **Declarative Pipeline** — every stage and step must be nested inside this block.

```groovy
agent any
```

tells Jenkins the pipeline can run on any available agent. In this setup, Jenkins runs it directly on the configured machine, inside its workspace:

```text
Running on Jenkins in /var/lib/jenkins/workspace/simple-java-maven-app
```

### Stage: Checkout

```groovy
stage('Checkout') {
    steps {
        git branch: 'master',
            url: 'https://github.com/nai1551/simple-java-maven-app.git'
    }
}
```

Downloads the project source code from GitHub into the Jenkins workspace (`GitHub → Jenkins Workspace`). The branch is explicitly set to `master` to match the actual repository.

### Stage: Verify Tools

```groovy
stage('Verify Tools') { ... }
```

Checks that Jenkins can actually see the required development tools before attempting a build — this is a diagnostic stage, not a build step. It prints:

| Command | What it confirms |
|---|---|
| `java --version` | Java runtime is available |
| `javac --version` | Java **compiler** is available (needed for JDK, not just JRE) |
| `echo "$JAVA_HOME"` | Where Jenkins thinks the JDK is installed |
| `which java` / `which javac` | The exact path being used, useful when multiple versions exist |
| `mvn --version` | Maven is available and which Java version *it* reports using |

> **Beginner tip:** This stage looks unnecessary once everything works, but it's extremely valuable when *diagnosing* failures — keep it in your pipeline even after things are stable.

### Stage: Build

```groovy
stage('Build') {
    steps {
        sh 'mvn clean package'
    }
}
```

`mvn clean package` runs two Maven lifecycle phases:

| Phase | What it does |
|---|---|
| `clean` | Deletes previous build output (the `target/` directory) |
| `package` | Compiles the project, runs required build steps, and packages it into a `.jar` |

Result: a jar such as `target/my-app-1.0-SNAPSHOT.jar`.

### Stage: Test

```groovy
stage('Test') {
    steps {
        sh 'mvn test'
    }
}
```

Runs the project's automated tests. Successful output looks like:

```text
Tests run: 2
Failures: 0
Errors: 0
Skipped: 0
BUILD SUCCESS
```

### Stage: Show Artifact

```groovy
stage('Show Artifact') {
    steps {
        sh 'ls -lh target/'
    }
}
```

Lists what Maven produced, e.g.:

```text
target/
├── classes/
├── test-classes/
├── surefire-reports/
└── my-app-1.0-SNAPSHOT.jar
```

The `.jar` file is the build artifact — the actual deliverable of this pipeline.

---

## 15. Troubleshooting Reference

| Symptom | Cause | Fix |
|---|---|---|
| `Authentication failed` | Repository URL still had a placeholder like `https://github.com/YOUR-USERNAME/...` | Use the real repository URL (`https://github.com/nai1551/simple-java-maven-app.git`). For private repos, configure a GitHub credential/PAT via **Jenkins Credentials** — never hardcode secrets in the Jenkinsfile. |
| `Couldn't find any revision to build. Verify the repository and branch configuration.` | Jenkins was configured for branch `main`, but the repo actually uses `master` | Check with `git ls-remote --heads <repo-url>`, then change `branch: 'main'` to `branch: 'master'` in the Jenkinsfile |
| `No such DSL method 'steps'` | Only a `stage { }` block was pasted as the whole Jenkinsfile, missing the outer `pipeline`/`stages` structure | Wrap it correctly: `pipeline { agent any; stages { stage('X') { steps { ... } } } }` — see the required hierarchy below |
| `javac: not found` | Only the JRE was installed, not the full JDK | Install the JDK: `sudo apt install openjdk-21-jdk -y`, verify with `java --version` / `javac --version`, then test again as Jenkins (`sudo -u jenkins bash -c 'javac --version'`) and restart Jenkins |
| `Fatal error compiling: error: release version 21 not supported` | Maven is running against a Java version/toolchain that can't compile for Java 21 | Check `mvn --version` (it reports which Java it's using) and confirm `java --version` / `javac --version` are both 21+ |
| Works in your terminal (`mvn --version`) but Jenkins can't find Maven | Jenkins runs as its own service user with a potentially different `PATH`/environment | Test explicitly as Jenkins: `sudo -u jenkins bash -c 'mvn --version'` (and the same for `java`/`javac`). The pipeline's **Verify Tools** stage is designed to catch exactly this. |

### Required Declarative Pipeline hierarchy

A very common beginner mistake is pasting only a `stage { }` block as if it were the whole Jenkinsfile. The full structure must be:

```text
pipeline
 ├── agent
 └── stages
      └── stage
           └── steps
                └── sh
```

Correct minimal example:

```groovy
pipeline {
    agent any

    stages {
        stage('Verify Tools') {
            steps {
                sh 'java --version'
            }
        }
    }
}
```

---

## 16. Final Working Environment

After troubleshooting, the confirmed working environment was:

| Component | Version |
|---|---|
| Java | 21.0.12 |
| javac | 21.0.12 |
| Maven | 3.9.9 |
| Git | 2.43.0 |
| Jenkins | 2.568.3 |

With this environment, the pipeline completes successfully:

```text
GitHub
  ↓
Jenkins
  ↓
Checkout
  ↓
Verify Java / JDK / Maven
  ↓
Build
  ↓
Test
  ↓
Generate JAR
  ↓
SUCCESS
```

---

## 17. Useful Commands Cheat Sheet

**Jenkins service**
```bash
sudo systemctl status jenkins
sudo systemctl restart jenkins
```

**Check tools (as your normal user)**
```bash
java --version
javac --version
mvn --version
```

**Check tools (as the Jenkins user)**
```bash
sudo -u jenkins bash -c 'java --version'
sudo -u jenkins bash -c 'javac --version'
sudo -u jenkins bash -c 'mvn --version'
```

**Check available Git branches**
```bash
git ls-remote --heads https://github.com/nai1551/simple-java-maven-app.git
```

**Build and test locally (before trusting Jenkins to do it)**
```bash
mvn clean package
mvn test
ls -lh target/
```

---

## 18. What You Learned

This project covers several Jenkins/CI fundamentals:

**Jenkins:** installation, service management, workspaces, agents, Declarative Pipeline syntax, stages, steps, `agent any`, `sh` commands, reading console logs.

**Git:** GitHub repository integration, branch configuration, `master` vs. `main`, repository URL troubleshooting, `git ls-remote`.

**Java:** the runtime vs. the JDK, `javac`, version compatibility, `JAVA_HOME`, and how Jenkins' environment can differ from your own shell.

**Maven:** installation and version verification, `mvn clean package`, `mvn test`, compilation, dependencies, build artifacts, and the `target/` directory.

**Troubleshooting:** authentication problems, branch mismatches, pipeline syntax errors, missing `javac`, JDK vs. JRE confusion, Jenkins environment differences, and Maven compilation errors.

---

## 19. Recommended Next Step

With a working CI pipeline in place, the natural next step in a DevOps progression is to add **Continuous Delivery**:

```text
GitHub → Jenkins → Checkout → Build → Test → Docker Build → Docker Image → Container Registry → Deployment → Kubernetes
```

A good next project: extend this same Java application so Jenkins automatically builds a **Docker image** after the Maven tests pass, then pushes it to a container registry.
