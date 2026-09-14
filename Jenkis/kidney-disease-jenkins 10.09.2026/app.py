"""
Kidney Disease Prediction — Streamlit App
Rebuilt from the original Gradio Blocks UI in capstone_final_chi_updated.py.
Loads the pre-trained artifacts (best_model.pkl, scaler.pkl, label_encoders.pkl,
metadata.pkl) produced by the training script instead of retraining on every run.
"""

import os
import warnings

import joblib
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# ==============================
# CONFIG
# ==============================
MODEL_DIR = "saved_models"
BEST_MODEL_PATH = os.path.join(MODEL_DIR, "best_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
ENCODERS_PATH = os.path.join(MODEL_DIR, "label_encoders.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.pkl")

st.set_page_config(
    page_title="Kidney Disease Prediction + SHAP",
    page_icon="🏥",
    layout="wide",
)

# ==============================
# LOAD ARTIFACTS
# ==============================
@st.cache_resource(show_spinner="Loading model artifacts...")
def load_artifacts():
    missing = [p for p in [BEST_MODEL_PATH, SCALER_PATH, ENCODERS_PATH, METADATA_PATH] if not os.path.exists(p)]
    if missing:
        return None

    # joblib.load transparently handles both compressed (best_model.pkl)
    # and plain-pickle (scaler/label_encoders/metadata) files.
    best_model = joblib.load(BEST_MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    label_encoders = joblib.load(ENCODERS_PATH)
    metadata = joblib.load(METADATA_PATH)

    return {
        "best_model": best_model,
        "scaler": scaler,
        "label_encoders": label_encoders,
        "metadata": metadata,
    }


@st.cache_resource(show_spinner="Preparing SHAP background samples...")
def build_shap_explainer(_best_model, _X_train_selected):
    import shap
    background_idx = np.random.choice(_X_train_selected.shape[0], min(50, _X_train_selected.shape[0]), replace=False)
    return shap.KernelExplainer(_best_model.predict_proba, _X_train_selected[background_idx])


@st.cache_data(show_spinner=False)
def load_training_background():
    """
    The SHAP/LIME background needs a sample of scaled, feature-selected training data.
    We recreate it from the CSV using the saved scaler + metadata so we don't have to
    persist the full training set separately.
    """
    csv_path = "kidney_disease_realistic_fixed.csv"
    if not os.path.exists(csv_path):
        return None

    data = pd.read_csv(csv_path, encoding="latin-1").dropna()
    artifacts = load_artifacts()
    label_encoders = artifacts["label_encoders"]
    metadata = artifacts["metadata"]

    for col in data.columns:
        if col in label_encoders:
            data[col] = label_encoders[col].transform(data[col].astype(str))

    target_col = "Target"
    X = data.drop(target_col, axis=1)

    scaler = artifacts["scaler"]
    X_scaled = scaler.transform(X)

    selected_idx = metadata["selected_idx"]
    X_selected = X_scaled[:, selected_idx]

    return X, X_selected


# ==============================
# CKD-EPI eGFR FORMULA
# ==============================
def calculate_egfr(age, serum_creatinine, gender="male"):
    if gender == "female":
        kappa, alpha, sex_factor = 0.7, -0.329, 1.018
    else:
        kappa, alpha, sex_factor = 0.9, -0.411, 1.0

    scr_kappa = serum_creatinine / kappa
    if scr_kappa < 1:
        egfr = 141 * (scr_kappa ** alpha) * (0.9929 ** age) * sex_factor
    else:
        egfr = 141 * (scr_kappa ** -1.209) * (0.9929 ** age) * sex_factor

    return round(max(1.0, min(120.0, egfr)), 1)


# ==============================
# NORMAL BASELINE (used to fill unspecified features)
# ==============================
NORMAL_BASELINE = {
    "Age of the patient": 35,
    "Blood pressure (mm/Hg)": 80,
    "Specific gravity of urine": 1.020,
    "Albumin in urine": 0,
    "Sugar in urine": 0,
    "Red blood cells in urine": 1,
    "Pus cells in urine": 1,
    "Pus cell clumps in urine": 0,
    "Bacteria in urine": 0,
    "Random blood glucose level (mg/dl)": 100,
    "Blood urea (mg/dl)": 20,
    "Serum creatinine (mg/dl)": 1.0,
    "Sodium level (mEq/L)": 140,
    "Potassium level (mEq/L)": 4.0,
    "Hemoglobin level (gms)": 14,
    "Packed cell volume (%)": 44,
    "White blood cell count (cells/cumm)": 8000,
    "Red blood cell count (millions/cumm)": 5.0,
    "Hypertension (yes/no)": 0,
    "Diabetes mellitus (yes/no)": 0,
    "Coronary artery disease (yes/no)": 0,
    "Appetite (good/poor)": 0,
    "Pedal edema (yes/no)": 0,
    "Anemia (yes/no)": 0,
    "Estimated Glomerular Filtration Rate (eGFR)": 100,
    "Urine protein-to-creatinine ratio": 0.1,
    "Urine output (ml/day)": 1500,
    "Serum albumin level": 4.5,
    "Cholesterol level": 180,
    "Parathyroid hormone (PTH) level": 40,
    "Serum calcium level": 9.5,
    "Serum phosphate level": 3.5,
    "Family history of chronic kidney disease": 0,
    "Smoking status": 0,
    "Body Mass Index (BMI)": 22,
    "Physical activity level": 1,
    "Duration of diabetes mellitus (years)": 0,
    "Duration of hypertension (years)": 0,
    "Cystatin C level": 0.9,
    "Urinary sediment microscopy results": 0,
    "C-reactive protein (CRP) level": 1.0,
    "Interleukin-6 (IL-6) level": 2.0,
}


def predict_and_explain(artifacts, X_columns, age, gender, albumin_urine, bacteria,
                         blood_urea, serum_creatinine, hemoglobin, hypertension,
                         appetite, anemia, serum_albumin):
    best_model = artifacts["best_model"]
    scaler = artifacts["scaler"]
    label_encoders = artifacts["label_encoders"]
    metadata = artifacts["metadata"]

    selected_idx = metadata["selected_idx"]
    selected_features = metadata["selected_features"]
    class_names = metadata["class_names"]

    egfr = calculate_egfr(int(age), float(serum_creatinine), gender.lower())

    bacteria_enc = label_encoders["Bacteria in urine"].transform([bacteria or "not present"])[0]
    hypert_enc = label_encoders["Hypertension (yes/no)"].transform([hypertension or "no"])[0]
    appetite_enc = label_encoders["Appetite (good/poor)"].transform([appetite or "good"])[0]
    anemia_enc = label_encoders["Anemia (yes/no)"].transform([anemia or "no"])[0]

    user_input_dict = {
        "Albumin in urine": float(albumin_urine),
        "Bacteria in urine": float(bacteria_enc),
        "Blood urea (mg/dl)": float(blood_urea),
        "Serum creatinine (mg/dl)": float(serum_creatinine),
        "Hemoglobin level (gms)": float(hemoglobin),
        "Hypertension (yes/no)": float(hypert_enc),
        "Appetite (good/poor)": float(appetite_enc),
        "Anemia (yes/no)": float(anemia_enc),
        "Estimated Glomerular Filtration Rate (eGFR)": float(egfr),
        "Serum albumin level": float(serum_albumin),
    }

    full_vector = np.array([[NORMAL_BASELINE.get(col, 0) for col in X_columns]])
    for feat, val in user_input_dict.items():
        col_idx = list(X_columns).index(feat)
        full_vector[0, col_idx] = val

    full_scaled = scaler.transform(full_vector)
    input_final = full_scaled[:, selected_idx]

    pred_class = best_model.predict(input_final)[0]
    pred_proba = best_model.predict_proba(input_final)[0]
    confidence = pred_proba[pred_class] * 100

    return {
        "egfr": egfr,
        "pred_class": pred_class,
        "pred_label": class_names[pred_class],
        "confidence": confidence,
        "pred_proba": pred_proba,
        "class_names": class_names,
        "input_final": input_final,
        "selected_features": selected_features,
    }


# ==============================
# UI HEADER (mirrors Gradio Markdown headers)
# ==============================
st.title("🏥 Kidney Disease Prediction + SHAP")
st.markdown("### Enter patient information — eGFR is auto-calculated from Age + Creatinine")

artifacts = load_artifacts()

if artifacts is None:
    st.error(
        "Saved model files were not found in `saved_models/`. "
        "This app expects `best_model.pkl`, `scaler.pkl`, `label_encoders.pkl`, "
        "and `metadata.pkl` to already exist (produced by the training script). "
        "Copy those files into the `saved_models/` folder next to `app.py` and reload."
    )
    st.stop()

label_encoders = artifacts["label_encoders"]
metadata = artifacts["metadata"]

# ==============================
# INPUT LAYOUT (mirrors gr.Row / gr.Column split)
# ==============================
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("#### 👤 Patient Info")
    age = st.number_input("Age of the patient (years)", value=35, step=1)
    gender = st.selectbox("Gender", ["male", "female"], index=0)

    st.markdown("#### 🧪 Urine Test")
    albumin_urine = st.number_input("Albumin in urine (0–5 scale)", value=0, step=1)
    bacteria = st.selectbox("Bacteria in urine", ["present", "not present"], index=1)

with col_right:
    st.markdown("#### 💉 Blood Tests")
    blood_urea = st.number_input("Blood urea (mg/dl)", value=20.0)
    serum_creatinine = st.number_input("Serum creatinine (mg/dl)", value=1.0)
    hemoglobin = st.number_input("Hemoglobin level (gms)", value=14.0)
    serum_albumin = st.number_input("Serum albumin level", value=4.5)

    st.markdown("#### 📋 Clinical Findings")
    hypertension = st.selectbox("Hypertension (yes/no)", ["yes", "no"], index=1)
    appetite = st.selectbox("Appetite (good/poor)", ["good", "poor"], index=0)
    anemia = st.selectbox("Anemia (yes/no)", ["yes", "no"], index=1)

st.markdown("#### ℹ️ eGFR is auto-calculated — no manual input needed")

predict_clicked = st.button("🔍 Predict & Explain", type="primary", use_container_width=False)

# ==============================
# OUTPUT (mirrors gr.Textbox + gr.Image + gr.File)
# ==============================
if predict_clicked:
    try:
        with st.spinner("Running prediction..."):
            result = predict_and_explain(
                artifacts, metadata["feature_names"],
                age, gender, albumin_urine, bacteria,
                blood_urea, serum_creatinine, hemoglobin,
                hypertension, appetite, anemia, serum_albumin,
            )

        result_text = f"Predicted Stage: {result['pred_label']}\n"
        result_text += f"Confidence     : {result['confidence']:.2f}%\n"
        result_text += f"Auto eGFR      : {result['egfr']} ml/min/1.73m²\n"
        result_text += "=" * 40 + "\n"
        result_text += "All Class Probabilities:\n"
        result_text += "=" * 40 + "\n"
        for i, prob in enumerate(result["pred_proba"]):
            bar = "█" * int(prob * 30)
            result_text += f"{result['class_names'][i]:20s}: {prob*100:5.2f}% {bar}\n"

        st.text_area("Prediction Results", value=result_text, height=340)

        img_col, lime_col = st.columns(2)

        # ── SHAP ──
        with img_col:
            with st.spinner("Computing SHAP explanation..."):
                try:
                    X_train_df, X_train_selected = load_training_background()
                    explainer_shap = build_shap_explainer(artifacts["best_model"], X_train_selected)

                    shap_values_raw = explainer_shap.shap_values(result["input_final"], nsamples=500)

                    if isinstance(shap_values_raw, list):
                        shap_values_class = shap_values_raw[result["pred_class"]]
                    elif shap_values_raw.ndim == 3:
                        shap_values_class = shap_values_raw[:, :, result["pred_class"]]
                    else:
                        shap_values_class = shap_values_raw

                    import shap
                    n_display = min(10, len(result["selected_features"]))
                    fig = plt.figure(figsize=(8, 5))
                    shap.summary_plot(
                        shap_values_class,
                        result["input_final"],
                        feature_names=result["selected_features"],
                        max_display=n_display,
                        show=False,
                    )
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)
                except Exception as shap_err:
                    st.warning(f"SHAP explanation unavailable: {shap_err}")

        # ── LIME ──
        with lime_col:
            with st.spinner("Computing LIME explanation..."):
                try:
                    import lime
                    import lime.lime_tabular

                    explainer_lime = lime.lime_tabular.LimeTabularExplainer(
                        training_data=np.array(X_train_selected),
                        feature_names=result["selected_features"],
                        class_names=list(result["class_names"].values()),
                        mode="classification",
                    )

                    exp = explainer_lime.explain_instance(
                        data_row=result["input_final"][0],
                        predict_fn=artifacts["best_model"].predict_proba,
                        num_samples=500,
                    )

                    lime_html = exp.as_html()
                    st.components.v1.html(lime_html, height=420, scrolling=True)
                    st.download_button(
                        "Download LIME Explanation (HTML)",
                        data=lime_html,
                        file_name="lime_explanation.html",
                        mime="text/html",
                    )
                except Exception as lime_err:
                    st.warning(f"LIME explanation unavailable: {lime_err}")

    except Exception as e:
        import traceback
        st.error(f"Error: {str(e)}")
        st.code(traceback.format_exc())
