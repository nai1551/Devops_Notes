"""
test_predict.py

A lightweight smoke test for CI. Loads the real saved_models/ artifacts
and runs one prediction end-to-end, mirroring the core logic in app.py.
This is NOT a full unit test suite — it's a fast sanity check that:

  1. The model files actually load without error
  2. A prediction can be produced for a realistic patient input
  3. The output shape/values are sane (5 classes, probabilities sum to 1)

If this script exits non-zero, the GitHub Actions job fails, which is
exactly the signal you want before anything reaches Jenkins.

Run with pytest:  pytest tests/test_predict.py -v
Run standalone:   python tests/test_predict.py
"""

import sys
import os

import joblib
import numpy as np

MODEL_DIR = "saved_models"


def load_artifacts():
    best_model = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    label_encoders = joblib.load(os.path.join(MODEL_DIR, "label_encoders.pkl"))
    metadata = joblib.load(os.path.join(MODEL_DIR, "metadata.pkl"))
    return best_model, scaler, label_encoders, metadata


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


NORMAL_BASELINE = {
    "Age of the patient": 35, "Blood pressure (mm/Hg)": 80, "Specific gravity of urine": 1.020,
    "Albumin in urine": 0, "Sugar in urine": 0, "Red blood cells in urine": 1, "Pus cells in urine": 1,
    "Pus cell clumps in urine": 0, "Bacteria in urine": 0, "Random blood glucose level (mg/dl)": 100,
    "Blood urea (mg/dl)": 20, "Serum creatinine (mg/dl)": 1.0, "Sodium level (mEq/L)": 140,
    "Potassium level (mEq/L)": 4.0, "Hemoglobin level (gms)": 14, "Packed cell volume (%)": 44,
    "White blood cell count (cells/cumm)": 8000, "Red blood cell count (millions/cumm)": 5.0,
    "Hypertension (yes/no)": 0, "Diabetes mellitus (yes/no)": 0, "Coronary artery disease (yes/no)": 0,
    "Appetite (good/poor)": 0, "Pedal edema (yes/no)": 0, "Anemia (yes/no)": 0,
    "Estimated Glomerular Filtration Rate (eGFR)": 100, "Urine protein-to-creatinine ratio": 0.1,
    "Urine output (ml/day)": 1500, "Serum albumin level": 4.5, "Cholesterol level": 180,
    "Parathyroid hormone (PTH) level": 40, "Serum calcium level": 9.5, "Serum phosphate level": 3.5,
    "Family history of chronic kidney disease": 0, "Smoking status": 0, "Body Mass Index (BMI)": 22,
    "Physical activity level": 1, "Duration of diabetes mellitus (years)": 0, "Duration of hypertension (years)": 0,
    "Cystatin C level": 0.9, "Urinary sediment microscopy results": 0, "C-reactive protein (CRP) level": 1.0,
    "Interleukin-6 (IL-6) level": 2.0,
}


def run_smoke_test():
    print("Loading model artifacts...")
    best_model, scaler, label_encoders, metadata = load_artifacts()
    print(f"  Loaded model: {type(best_model).__name__}")
    print(f"  Best model name (from training): {metadata['best_model_name']}")

    X_columns = metadata["feature_names"]
    selected_idx = metadata["selected_idx"]
    class_names = metadata["class_names"]

    assert len(class_names) == 5, f"Expected 5 classes, got {len(class_names)}"

    # Simulate a realistic patient (moderately unwell)
    age, gender = 55, "male"
    serum_creatinine = 1.8
    egfr = calculate_egfr(age, serum_creatinine, gender)

    bacteria_enc = label_encoders["Bacteria in urine"].transform(["not present"])[0]
    hypert_enc = label_encoders["Hypertension (yes/no)"].transform(["yes"])[0]
    appetite_enc = label_encoders["Appetite (good/poor)"].transform(["good"])[0]
    anemia_enc = label_encoders["Anemia (yes/no)"].transform(["no"])[0]

    user_input = {
        "Albumin in urine": 1.0, "Bacteria in urine": float(bacteria_enc), "Blood urea (mg/dl)": 45.0,
        "Serum creatinine (mg/dl)": serum_creatinine, "Hemoglobin level (gms)": 12.5,
        "Hypertension (yes/no)": float(hypert_enc), "Appetite (good/poor)": float(appetite_enc),
        "Anemia (yes/no)": float(anemia_enc), "Estimated Glomerular Filtration Rate (eGFR)": float(egfr),
        "Serum albumin level": 4.0,
    }

    full_vector = np.array([[NORMAL_BASELINE.get(col, 0) for col in X_columns]])
    for feat, val in user_input.items():
        full_vector[0, list(X_columns).index(feat)] = val

    full_scaled = scaler.transform(full_vector)
    input_final = full_scaled[:, selected_idx]

    print("Running prediction...")
    pred_class = best_model.predict(input_final)[0]
    pred_proba = best_model.predict_proba(input_final)[0]

    print(f"  eGFR              : {egfr}")
    print(f"  Predicted class   : {pred_class} ({class_names[pred_class]})")
    print(f"  Probabilities sum : {pred_proba.sum():.6f}")

    # Sanity checks
    assert pred_class in class_names, "Predicted class not in known class names"
    assert abs(pred_proba.sum() - 1.0) < 1e-3, "Probabilities do not sum to ~1.0"
    assert len(pred_proba) == 5, f"Expected 5 probability values, got {len(pred_proba)}"
    assert all(0.0 <= p <= 1.0 for p in pred_proba), "Probability out of [0, 1] range"

    print("\n✅ Smoke test passed — model loads and predicts correctly.")


def test_smoke():
    """pytest entry point — pytest only auto-discovers functions named test_*"""
    run_smoke_test()


if __name__ == "__main__":
    try:
        run_smoke_test()
    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}")
        sys.exit(1)
