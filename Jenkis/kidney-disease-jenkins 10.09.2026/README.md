# 🏥 Kidney Disease Prediction App

A machine learning web app that predicts kidney disease risk stage (High Risk, Low Risk, Moderate Risk, No Disease, Severe Disease) from patient clinical data, with SHAP and LIME explanations for every prediction. Built with Streamlit, deployed automatically via Jenkins.

---

## What this project does

Given basic patient information (age, gender, blood test results, urine test results, clinical findings), the app:

1. **Auto-calculates eGFR** (estimated Glomerular Filtration Rate) using the CKD-EPI formula
2. **Predicts the kidney disease risk stage** using a trained machine learning model
3. **Shows the confidence and full probability breakdown** across all 5 risk stages
4. **Explains the prediction** using SHAP (which features pushed the prediction up/down) and LIME (a local, human-readable explanation)

---

## Project structure

```
python-project/
├── app.py                              # Streamlit web app (input form + predictions + explanations)
├── train_model.py                      # Standalone training script — run once to (re)generate the model
├── show_changes.sh                     # Shows what changed since the last Jenkins build
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # (optional) container build, not used by the current pipeline
├── Jenkinsfile                         # CI/CD pipeline definition
├── kidney_disease_realistic_fixed.csv  # Training dataset
└── saved_models/                       # Trained model artifacts (see below)
    ├── best_model.pkl                  # Trained model (Stacking Ensemble), joblib-compressed
    ├── scaler.pkl                      # StandardScaler fitted on training data
    ├── label_encoders.pkl              # LabelEncoders for categorical columns
    ├── metadata.pkl                    # Selected features, class names, training results
    └── model_comparison.csv            # Accuracy/ROC-AUC/F1 for every model that was tried
```

---

## How the model was built

`train_model.py` runs the full ML pipeline:

1. **Load & clean** `kidney_disease_realistic_fixed.csv`, encode categorical columns
2. **Balance classes** with SMOTE-Tomek (the raw dataset is imbalanced — e.g. far more "Severe_Disease" cases than "No_Disease")
3. **Select the top 10 features** using Chi-Square feature selection
4. **Tune 8 different models** with `RandomizedSearchCV`: Random Forest, Gradient Boosting, XGBoost, Extra Trees, Decision Tree, Logistic Regression, KNN, AdaBoost
5. **Build 2 ensembles** on top of the best 3 individual models: a Voting Ensemble and a Stacking Ensemble
6. **Evaluate all 10 models** on a held-out test set and pick the best one by ROC-AUC
7. **Save the winning model** + scaler + encoders + metadata to `saved_models/`

### Current best model

| Model | Accuracy | ROC-AUC | F1-Score |
|---|---|---|---|
| **Stacking Ensemble** (deployed) | 96.85% | 0.9988 | 0.9685 |
| Extra Trees | 96.74% | 0.9985 | 0.9674 |
| Voting Ensemble | 96.47% | 0.9983 | 0.9647 |
| XGBoost | 96.01% | 0.9982 | 0.9601 |
| Random Forest | 96.18% | 0.9978 | 0.9618 |

Full comparison across all 10 models is in `saved_models/model_comparison.csv`.

> The model file is saved with `joblib` compression (`compress=3`) instead of raw `pickle` — the uncompressed Stacking Ensemble was ~215MB, over GitHub's 100MB file limit. Compressed, it's ~57MB with no change in predictions.

---

## Running it locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Only if saved_models/ is missing or you want to retrain) train the model
python train_model.py

# 3. Run the app
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## Deployment (Jenkins CI/CD)

The app is deployed on a Jenkins worker server as a **systemd service** — no Docker required for this pipeline.

### Pipeline stages (`Jenkinsfile`)

| Stage | What it does |
|---|---|
| **Checkout** | Pulls the latest code from GitHub |
| **Show Changes** | Runs `show_changes.sh` — prints which files changed and what commits were made since the last successful build |
| **Prepare App Directory** | Copies the repo into `/opt/kidney-disease-streamlit` |
| **Python Setup** | Creates a virtualenv and installs `requirements.txt` |
| **Test** | Runs a Python syntax check on `app.py` |
| **Deploy** | Restarts the `kidney-streamlit` systemd service with the new code |
| **Health Check** | Confirms the app responds on port 8501 before declaring success |

### Why systemd instead of `nohup`

Jenkins kills any background process it spawns once a build finishes — so a simple `nohup streamlit run ... &` gets terminated right after deploy. Using a systemd service (`kidney-streamlit.service`) means the OS manages the process lifecycle instead of Jenkins: it survives after the build ends, and auto-restarts if it ever crashes.

### One-time server setup (already done on the current worker)

```bash
# systemd service definition
sudo tee /etc/systemd/system/kidney-streamlit.service > /dev/null <<'EOF'
[Unit]
Description=Kidney Disease Streamlit App
After=network.target

[Service]
Type=simple
User=jenkins
WorkingDirectory=/opt/kidney-disease-streamlit
ExecStart=/opt/kidney-disease-streamlit/venv/bin/streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kidney-streamlit

# allow Jenkins to restart the service without a password prompt
echo "jenkins ALL=(ALL) NOPASSWD: /bin/systemctl restart kidney-streamlit, /bin/systemctl status kidney-streamlit, /bin/systemctl is-active kidney-streamlit" \
  | sudo tee /etc/sudoers.d/jenkins-streamlit
sudo chmod 440 /etc/sudoers.d/jenkins-streamlit
```

### Triggering a build

Builds are triggered **manually** — click **Build Now** in Jenkins after pushing changes to `main`. The **Show Changes** stage in the console output tells you exactly what changed since the last successful deploy, so you always know what's going out.

---

## Tech stack

- **App**: Streamlit
- **ML**: scikit-learn, XGBoost, imbalanced-learn (SMOTE-Tomek)
- **Explainability**: SHAP, LIME
- **CI/CD**: Jenkins (Pipeline as Code via `Jenkinsfile`)
- **Deployment**: systemd (process supervision on the worker server)
- **Version control**: Git / GitHub

---

## Notes for anyone picking this up

- If `saved_models/` is missing or corrupted, the app will show a clear error on startup instead of crashing — just re-run `train_model.py` to regenerate it.
- Retraining takes roughly 15–20 minutes (8 models tuned via `RandomizedSearchCV` + 2 ensembles) depending on CPU.
- SHAP explanations are computed live per-prediction (`KernelExplainer`), so the first prediction after app startup will be a bit slower than the rest — this is expected.
- The dataset column names are intentionally verbose/clinical (e.g. `"Estimated Glomerular Filtration Rate (eGFR)"`) — `app.py` and `train_model.py` both rely on these exact names, so don't rename CSV columns without updating both files.
