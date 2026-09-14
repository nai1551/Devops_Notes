# React + Jenkins CI/CD — Quick Reference Guide

A personal cheat sheet for setting up and running a React (Create React App) project through Jenkins CI/CD, based on lessons learned from `react-ci-cd-demo`.

**Project references:**
- https://github.com/nai1551/react-ci-cd-demo.git
- https://github.com/Marwizz/react-ci-cd-demo.git

---

## 1. Prerequisites on the Worker Server

You need **Node.js and npm** only. You do NOT need Java, Maven, or the Jenkins NodeJS plugin if Node is already installed system-wide.

```bash
sudo apt update
sudo apt install -y nodejs npm

node --version
npm --version
```

**Important:** Jenkins jobs run as the `jenkins` user, not your personal user. Always double-check Node is visible to that user too:

```bash
sudo -u jenkins node --version
sudo -u jenkins npm --version
sudo -u jenkins which node
sudo -u jenkins which npm
```

If this fails while your own user works fine, it's usually a PATH issue for the `jenkins` service account.

---

## 2. Clone / Work With the Project Locally

```bash
cd ~
git clone https://github.com/nai1551/react-ci-cd-demo.git
cd react-ci-cd-demo

npm install        # installs React, React DOM, React Scripts, test libs, etc.
npm start           # runs dev server on http://localhost:3000
npm test             # interactive test mode
npm run build        # creates production build/ folder
```

To access the dev server from another machine:

```bash
HOST=0.0.0.0 npm start
```

Do **not** manually create or edit `node_modules/` — it's fully managed by `npm install`.

---

## 3. Jenkinsfile Naming Gotcha

Jenkins looks for a file named exactly `Jenkinsfile` (capital J) by default. If your repo has it lowercase (`jenkinsfile`), either:

- **Quick fix:** In the Jenkins job config → *Pipeline → Definition → Pipeline script from SCM*, set **Script Path** to `jenkinsfile` (lowercase, matching your repo).
- **Better fix:** Rename the file in your repo to `Jenkinsfile` so Jenkins can use its default expected filename.

---

## 4. Avoid the NodeJS Plugin (Unless You Actually Install It)

If your Jenkinsfile has this:

```groovy
tools {
    nodejs 'NodeJS 21.4.0'
}
```

...and Jenkins throws:

```
Invalid tool type "nodejs". Valid tool types: [ant, git, gradle, jdk, jgit, jgitapache, maven]
```

That means the **NodeJS plugin isn't installed** in Jenkins. Two options:

- **Simplest:** Remove the `tools { nodejs ... }` block and any `nodejs(...) { }` step wrappers. Just call `node`/`npm` directly via `sh` steps, relying on the system-installed Node.js.
- **Alternative:** Install the *NodeJS Plugin* via **Manage Jenkins → Plugins**, restart Jenkins, then configure a named NodeJS installation under **Manage Jenkins → Tools**.

---

## 5. CI Test Mode

`npm test` runs Create React App's test runner in **watch mode** by default — it will hang forever in a non-interactive Jenkins shell. Always run tests with:

```bash
CI=true npm test -- --watchAll=false
```

---

## 6. GitHub Credentials for Auto-Commit/Push Steps

If your pipeline needs to `git push` back to GitHub (e.g. after auto-formatting code), you need a **Jenkins credential**, and its *type* must match how your Jenkinsfile references it:

| Jenkinsfile syntax | Required Jenkins credential type |
|---|---|
| `withCredentials([string(credentialsId: 'x', variable: 'TOKEN')])` | **Secret text** |
| `withCredentials([usernamePassword(credentialsId: 'x', usernameVariable: 'U', passwordVariable: 'P')])` | **Username with password** |

Mismatching these throws:

```
ERROR: Credentials 'x' is of type 'Username with password' where 'StringCredentials' was expected
```

**To add a Secret text credential:**
1. Manage Jenkins → Credentials → System → Global credentials → Add Credentials
2. Kind = `Secret text`
3. Secret = your GitHub Personal Access Token (PAT)
4. ID = e.g. `github-token`

**Using it in the Jenkinsfile:**

```groovy
withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
    sh '''
        git config --global user.email "your-email@example.com"
        git config --global user.name "your-github-username"
        git add .
        git diff-index --quiet HEAD || git commit -m "CI: automated changes"
        git remote set-url origin https://$GITHUB_TOKEN@github.com/your-username/your-repo.git
        git push origin main
    '''
}
```

**If you don't want to deal with credentials at all:** skip the commit/push stage entirely. Lint, format, test, and build steps can all run and validate code without pushing anything back to GitHub — you just won't get automated commits.

---

## 7. Minimal Working Jenkinsfile (No Auto-Push, No Plugin Required)

This is the leanest version that builds successfully without any extra Jenkins plugins or credentials:

```groovy
pipeline {
    agent any
    stages {

        stage('List current directory') {
            steps {
                sh 'pwd'
                sh 'ls -la'
            }
        }

        stage('Verify Node.js') {
            steps {
                sh '''
                    node --version
                    npm --version
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh 'npm install'
            }
        }

        stage('Check code practices with ESLint') {
            steps {
                sh 'npm run lint'
            }
        }

        stage('Format code with Prettier') {
            steps {
                sh 'npm run format'
            }
        }

        stage('Run tests') {
            steps {
                sh 'CI=true npm test -- --watchAll=false'
            }
        }

        stage('Build app') {
            steps {
                sh 'npm run build'
            }
        }

        stage('Clean up') {
            steps {
                sh 'rm -rf build'
            }
        }
    }

    post {
        success {
            echo 'React project CI pipeline completed successfully!'
        }
        failure {
            echo 'React project CI pipeline failed!'
        }
        always {
            echo 'Pipeline execution finished.'
        }
    }
}
```

---

## 8. Quick Troubleshooting Checklist

When a pipeline fails, check in this order:

1. **"Unable to find Jenkinsfile"** → check filename case (`Jenkinsfile` vs `jenkinsfile`) and Script Path setting.
2. **"Invalid tool type nodejs"** → remove `tools { nodejs ... }` block, use system Node via `sh` instead, or install the NodeJS plugin.
3. **Tests hang / never finish** → add `CI=true` and `--watchAll=false` to the test command.
4. **Credential type mismatch error** → match `string()` ↔ Secret text, `usernamePassword()` ↔ Username with password.
5. **"jenkins user can't find node"** → run `sudo -u jenkins which node` to confirm PATH visibility.

---

## 9. Commands Cheat Sheet

```bash
# Local dev
npm install
npm start
npm test
npm run build

# Jenkins-safe test run
CI=true npm test -- --watchAll=false

# Check jenkins user's environment
sudo -u jenkins node --version
sudo -u jenkins npm --version
sudo -u jenkins which node
```
