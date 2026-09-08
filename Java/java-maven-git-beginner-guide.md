# Beginner's Guide: What You Just Did (Java + Git + Maven Build)

This guide explains, in simple terms, what actually happened when you built a Java project on your Ubuntu machine — **before** bringing Jenkins into the picture. If you're new to DevOps, read this top to bottom.

---

## 🧩 The Big Picture

You took a Java project from GitHub and built it manually on your own computer. That's it — no Jenkins yet.

```
   GitHub
     │  (git clone)
     ▼
 Ubuntu Machine
     │  (Maven reads pom.xml)
     ▼
  Compile Code
     │
     ▼
  Run Tests
     │
     ▼
 Package into JAR
     │
     ▼
 target/*.jar  ✅
```

**Why do this manually first?**
Because before you automate something, you need to prove it works by hand. You confirmed:

> "Can this app build and pass its tests on my machine?" → **Yes.**

Jenkins' whole job later will be to repeat these exact same steps automatically.

---

## 🛠️ The Tools You Used

| Tool | What it is | Why you need it |
|------|------------|------------------|
| **Java** | The language/runtime the app is written in | Compiles & runs the code |
| **Git** | Version control tool | Downloads the project from GitHub |
| **Maven** | Java build automation tool | Compiles, tests, and packages the project |

### Checking versions

```bash
java --version
git --version
mvn --version
```

⚠️ Note the **two hyphens** in `--version`. Running `mvn version` (no hyphens) fails, because Maven thinks you're asking it to *build* something called "version" — not asking for its own version number.

---

## ⚠️ Why the First Build Failed

The project had strict requirements set by something called the **Maven Enforcer** (a rule-checker inside the build):

```
Required: Maven >= 3.9.9   |  You had: 3.8.7  ❌
Required: Java  >= 21      |  You had: 17     ❌
```

So the build refused to run until you upgraded both tools:

```
Java 17   →  Java 21
Maven 3.8.7  →  Maven 3.9.9
```

**Lesson:** Real-world projects often demand specific tool versions. Any machine (or CI server) that builds the project must meet those requirements — this applies to Java, Node.js, Python, Docker, etc.

---

## 📥 Step-by-Step: What Each Command Did

### 1. Clone the project
```bash
git clone https://github.com/jenkins-docs/simple-java-maven-app.git
```
Downloads the *entire* GitHub repository onto your machine, into a new folder.

### 2. Move into the project folder
```bash
cd ~/simple-java-maven-app
```
`cd` = **Change Directory**. You need to be inside the project folder so Maven can find its config file.

### 3. List the files
```bash
ls -lah
```
| Flag | Meaning |
|------|---------|
| `-l` | Long/detailed listing |
| `-a` | Show hidden files too |
| `-h` | Human-readable file sizes |

### 4. Look at `pom.xml`
**POM = Project Object Model.** This file tells Maven everything about the project:
- Project name & version
- Required Java version
- Dependencies (external libraries)
- Plugins and build/test settings

Think of it as the project's **instruction manual** for Maven.

### 5. Build the project
```bash
mvn clean package
```

| Part | Meaning |
|------|---------|
| `mvn` | Run Maven |
| `clean` | Delete old build files (the `target/` folder) so nothing stale interferes |
| `package` | Compile the code, run the tests, and bundle it all into a JAR file |

Maven's simplified build order:
```
Validate → Compile → Test → Package
```

### 6. Run just the tests
```bash
mvn test
```
Output showed:
```
Tests run: 2
Failures: 0
Errors: 0
Skipped: 0
```
✅ All tests passed.

### 7. Explore the results
```bash
find target -maxdepth 2 -type f
```
| Part | Meaning |
|------|---------|
| `find target` | Search inside the `target` folder |
| `-maxdepth 2` | Only look 2 folders deep |
| `-type f` | Show files only (not folders) |

---

## 📦 What Ended Up Inside `target/`

After a successful build, Maven created a `target/` folder containing:

| File/Folder | What it contains |
|-------------|-------------------|
| `classes/` | Your compiled application code (`.class` files) |
| `test-classes/` | Compiled test code |
| `surefire-reports/` | Test result reports (Maven's "Surefire" plugin runs your tests and logs results here) |
| `maven-status/` | Internal Maven build info |
| `maven-archiver/` | Packaging metadata |
| `my-app-1.0-SNAPSHOT.jar` | 🎯 The final packaged app — this is the "build artifact" |

---

## ✅ Summary: What You Actually Accomplished

```
   GitHub
     │  git clone
     ▼
Ubuntu Machine
     │
     ▼
   pom.xml  (Maven reads this)
     │
     ▼
   Maven
   ├──► Compile → target/classes
   └──► Test    → 2/2 tests passed
     │
     ▼
   Package
     │
     ▼
 my-app-1.0-SNAPSHOT.jar  🎉
```

This is a genuine **build-and-test workflow** — the same core process every CI/CD pipeline is built around. You just did it by hand.

---

## 🚀 Where Jenkins Comes In Next

Right now, *you* are the one typing these commands every time:
```bash
git clone ...
cd project
mvn clean package
mvn test
```

That doesn't scale. Imagine a team of developers pushing code constantly — nobody wants to manually rebuild and retest by hand every time.

**Jenkins automates this entire flow:**

```
 Developer pushes code
         │
         ▼
      GitHub
         │  (webhook triggers Jenkins)
         ▼
      Jenkins
         ├── Checkout code
         ├── Build
         ├── Test
         ├── Package
         └── Archive the JAR
```

This is called **CI — Continuous Integration**: automatically building and testing every code change.

Later, this can expand into **CD — Continuous Delivery/Deployment**:

```
GitHub → Jenkins → Build → Test → Docker Image → Docker Registry → Deploy
```

### 💡 Key Takeaway
You didn't waste time doing this manually — you now **understand exactly what Jenkins will automate**, because you did every step yourself first. That understanding is what makes debugging CI pipelines possible later.
