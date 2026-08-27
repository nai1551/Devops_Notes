# DevOps — A Standard Guide

A complete, beginner-friendly reference explaining what DevOps is, why it exists, its lifecycle, and the tools used at every stage.

---

## DevOps Lifecycle & Tools

![DevOps DEV-OPS Infinity Loop with Tools](./../assets/Linux%20roadmap.png)

This diagram shows the **DEV–OPS infinity loop**: the left half (**DEV**) covers building the software, the right half (**OPS**) covers running it in production. The two halves meet at **RELEASE** and **PLAN**, showing that DevOps is a continuous cycle, not a one-time process.

---

## 1. What is DevOps?

**DevOps** = **Dev**elopment + **Op**erations.

It is a combination of:
- **Culture** — breaking down the wall between the team that writes code (Dev) and the team that runs/maintains it in production (Ops)
- **Practices** — agile planning, continuous integration, continuous delivery, monitoring, feedback loops
- **Tools** — automation software that makes those practices fast and repeatable

**In simple terms:** Before DevOps, developers wrote code and "threw it over the wall" to a separate operations team to deploy and maintain — this caused delays, miscommunication, and blame games when things broke. DevOps merges these two responsibilities into one continuous, collaborative workflow, so the same team (or tightly-connected teams) builds, ships, and operates the software.

### Why DevOps exists
- Faster, more frequent software releases
- Fewer failures at launch, and faster recovery when failures happen
- Better collaboration between developers, testers, and IT/operations
- Heavy automation replaces slow, manual, error-prone processes

### Core DevOps principles
| Principle | Meaning |
|---|---|
| **Automation** | Automate builds, tests, deployments, and infrastructure setup instead of doing them manually |
| **Continuous Integration (CI)** | Developers merge code changes frequently; each merge is automatically built and tested |
| **Continuous Delivery/Deployment (CD)** | Code that passes tests is automatically prepared (or even automatically released) for production |
| **Infrastructure as Code (IaC)** | Servers and environments are defined and managed using code/config files, not manual setup |
| **Monitoring & Feedback** | Constantly observe the running system and feed insights back into planning/development |
| **Collaboration/Culture** | Dev and Ops share responsibility for the whole product lifecycle, not just their own piece |

---

## 2. The DEV–OPS Infinity Loop Explained

The loop has 8 stages, split evenly between Dev (build side) and Ops (run side):

| Stage | Side | What happens here |
|---|---|---|
| **Plan** | Bridge (Dev↔Ops) | Define requirements, features, and roadmap for what will be built |
| **Code** | Dev | Developers write and manage source code |
| **Build** | Dev | Source code is compiled/packaged into a runnable artifact |
| **Test** | Dev | Automated (and manual) tests verify the code works correctly |
| **Release** | Bridge (Dev↔Ops) | The tested build is prepared and approved for deployment |
| **Deploy** | Ops | The release is pushed out to servers/production environments |
| **Operate** | Ops | The live system is managed, configured, and kept running |
| **Monitor** | Ops | The running system is watched for errors, performance issues, and usage patterns — feeding back into the next Plan phase |

This is a **loop, not a line** — feedback from Monitor and Operate flows back into Plan, so the cycle repeats continuously with each release.

---

## 3. Tools Explained — By Stage (from the diagram)

### 3.1 Code — Version Control

| Tool | What it is |
|---|---|
| **Git** | A free, open-source **distributed version control system**. It tracks every change made to source code, lets multiple developers work on the same project without overwriting each other's work, and enables branching/merging. Git itself is just the underlying technology — it runs locally and also powers hosted platforms like GitHub, GitLab, and Bitbucket. |
| **GitLab** | A web-based platform built around Git that provides repository hosting **plus** built-in CI/CD pipelines, issue tracking, and DevOps tooling all in one product. Popular as an all-in-one DevOps platform (source control + automation together). |

### 3.2 Build

| Tool | What it is |
|---|---|
| **Gradle** | A **build automation tool**, most commonly used for Java, Kotlin, and Android projects. It compiles source code, manages dependencies (external libraries), runs tests, and packages the final application — all through configuration scripts, so builds are consistent and repeatable. |
| **Sonatype Nexus** | A **repository manager** used to store and manage build artifacts and dependencies (like compiled packages, Docker images, or libraries). Teams use it as a central, secure storage/proxy for everything their build process needs to download or publish. |

### 3.3 Test

| Tool | What it is |
|---|---|
| **Jenkins** *(the "butler" mascot icon)* | The most widely used open-source **automation server**, primarily used to build **CI/CD pipelines**. Jenkins automatically triggers builds and test runs whenever new code is pushed, and can then automate deployment — connecting the Code → Build → Test → Deploy stages together with plugins for almost any tool. |
| **OpenStack** | An open-source platform for building and managing **private/public cloud infrastructure** (compute, storage, networking). Organizations use it to run their own cloud instead of (or alongside) AWS/Azure, often used to spin up test/staging environments. |
| **Microsoft Azure** | A major **cloud computing platform** (like AWS) offering virtual machines, storage, databases, and countless managed services. In this diagram it's grouped near Test/Build because teams commonly provision test/staging environments on cloud platforms like Azure. |

### 3.4 Release / Plan

The **Release** and **Plan** bands sit at the crossing point of the infinity loop, representing the hand-off between finishing development work and starting the operational rollout — this is typically where project management and CI/CD pipeline "release" steps (tagging a version, approving a deployment) happen, often coordinated through tools like Jira, GitLab Pipelines, or Jenkins release jobs.

### 3.5 Deploy

| Tool | What it is |
|---|---|
| **AWS (Amazon Web Services)** | The world's largest **cloud computing platform**, offering on-demand servers, storage, databases, networking, and hundreds of other services. Teams deploy their applications onto AWS infrastructure instead of managing physical servers themselves. |
| **Docker** | A platform for **containerization** — packaging an application together with everything it needs (code, libraries, settings) into a lightweight, portable **container** that runs identically on any machine. Docker eliminates the "it works on my machine" problem and is one of the most fundamental tools in modern DevOps. |

### 3.6 Operate

| Tool | What it is |
|---|---|
| **Chef** | A **configuration management** tool that automates how servers are set up and maintained, using code ("recipes" and "cookbooks") to define the desired state of infrastructure. It ensures servers are consistently configured without manual intervention. |
| **Ansible** | Another very popular **configuration management and automation** tool (by Red Hat). It uses simple, human-readable YAML files ("playbooks") to automate server setup, application deployment, and orchestration — and unlike Chef, it doesn't require installing an agent on target servers. |
| **Kubernetes (K8s)** | An open-source **container orchestration platform** (originally built by Google). It automates the deployment, scaling, networking, and management of containerized applications (like those built with Docker) across clusters of machines. It's the industry standard for running containers at scale in production. |

### 3.7 Monitor

| Tool | What it is |
|---|---|
| **Grafana** | An open-source **data visualization and dashboarding tool**. It connects to data sources (like Prometheus, Graphite, or databases) and displays metrics as live, customizable charts/dashboards — widely used to monitor system performance and health at a glance. |
| **Graylog** | A **log management platform** used to collect, index, and search through logs generated by applications and infrastructure. It helps teams quickly find the root cause of errors and issues by centralizing logs from many systems into one searchable place. |

---

## 4. Putting It All Together — A Typical DevOps Flow

1. **Plan** the feature/fix (using a tool like Jira, not pictured here, but implied by the "Plan" band)
2. **Code** it and push to **Git**, hosted on **GitLab**
3. **Build** the project with **Gradle**, pulling/storing dependencies via **Sonatype Nexus**
4. **Test** it automatically using **Jenkins**, which may spin up test environments on **OpenStack** or **Azure**
5. **Release** the approved build — tagging a version, generating release notes
6. **Deploy** it to production infrastructure on **AWS**, packaged as a **Docker** container
7. **Operate** the servers using **Chef** or **Ansible** for configuration, and **Kubernetes** to orchestrate and scale the containers
8. **Monitor** the live system with **Grafana** (metrics/dashboards) and **Graylog** (logs) to catch issues — feeding insights back into the next **Plan** cycle

---

## Quick Reference Cheat Sheet

```
DEV side:  Plan -> Code -> Build -> Test -> Release
OPS side:  Release -> Deploy -> Operate -> Monitor -> (back to Plan)

Code       -> Git, GitLab
Build      -> Gradle, Sonatype Nexus
Test       -> Jenkins, OpenStack, Azure
Deploy     -> AWS, Docker
Operate    -> Chef, Ansible, Kubernetes
Monitor    -> Grafana, Graylog

Core idea: DevOps = Dev + Ops merged into one continuous,
automated, collaborative loop — not two separate teams
throwing work "over the wall."
```
