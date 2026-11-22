# SuperKart Sales Forecast API - Flask backend
import os

import joblib  # to load the serialized model pipeline
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request

# Initialise the Flask application
superkart_api = Flask("SuperKart Sales Forecast API")
superkart_api.json.sort_keys = False  # keep batch predictions in row order (0, 1, 2, ... 10) in the JSON response

# Load the serialized pipeline (preprocessing + tuned Random Forest) once, when the server starts.
# The path is resolved relative to this file, so it works inside the Docker container and locally.
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "superkart_model.joblib")
model = joblib.load(MODEL_PATH)

# The input contract: the ten features the model was trained on
NUMERIC_FEATURES = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]
CATEGORICAL_FEATURES = ["Product_Sugar_Content", "Store_Size", "Store_Location_City_Type",
                        "Store_Type", "Product_Id_char", "Product_Type_Category"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def prepare_features(frame):
    """
    Validate an input dataframe against the contract.
    Returns (clean_dataframe, None) on success or (None, error_message) on failure.
    """
    missing = [col for col in FEATURES if col not in frame.columns]
    if missing:
        return None, f"Missing required feature(s): {', '.join(missing)}"

    frame = frame[FEATURES].copy()  # keep only the contract columns, in a fixed order
    for col in NUMERIC_FEATURES:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")  # invalid numbers become NaN
    bad_rows = frame[NUMERIC_FEATURES].isna().any(axis=1)
    if bad_rows.any():
        return None, f"Numeric features must be numbers; invalid or empty values in row(s): {frame.index[bad_rows].tolist()}"
    for col in CATEGORICAL_FEATURES:
        frame[col] = frame[col].astype(str).str.strip()
    return frame, None


@superkart_api.get("/")
def home():
    """Health check: confirms the API is up and lists its endpoints."""
    return jsonify({
        "message": "Welcome to the SuperKart Sales Forecast API",
        "endpoints": {"online": "POST /v1/predict (JSON)", "batch": "POST /v1/predictbatch (CSV file in field 'file')"},
        "required_features": FEATURES,
    })


@superkart_api.post("/v1/predict")
def predict_sales():
    """
    Online inference: one product-store record as a JSON object.
    Returns {"Predicted_Product_Store_Sales_Total": <value>}.
    """
    payload = request.get_json(silent=True)  # None instead of an exception if the body is not valid JSON
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object containing the product and store features."}), 400

    features, error = prepare_features(pd.DataFrame([payload]))
    if error:
        return jsonify({"error": error}), 400

    try:
        prediction = float(np.clip(model.predict(features)[0], 0, None))  # revenue cannot be negative
    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {exc}"}), 500

    return jsonify({"Predicted_Product_Store_Sales_Total": round(prediction, 2)})


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """
    Batch inference: a CSV file uploaded in the multipart field 'file', one record per row.
    Returns a JSON object mapping each row index to its predicted sales.
    """
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV file in the 'file' field of a multipart/form-data request."}), 400

    try:
        batch = pd.read_csv(request.files["file"])
    except Exception as exc:
        return jsonify({"error": f"Could not read the uploaded file as CSV: {exc}"}), 400
    if batch.empty:
        return jsonify({"error": "The uploaded CSV file has no rows."}), 400

    features, error = prepare_features(batch)
    if error:
        return jsonify({"error": error}), 400

    try:
        predictions = np.clip(model.predict(features), 0, None)
    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {exc}"}), 500

    return jsonify({str(idx): round(float(pred), 2) for idx, pred in zip(batch.index, predictions)})


# Allows running the API directly with `python app.py`; inside Docker, gunicorn serves it instead
if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=False)
