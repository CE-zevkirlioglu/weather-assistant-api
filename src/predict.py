import os
from typing import Dict, List

import numpy as np
import pandas as pd
from joblib import load

from prepare_data import FEATURE_COLUMNS, LABEL_COLUMNS

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "weather_model.pkl")
RAIN_LABEL_KEY = "label_rain"


def load_model(path: str = MODEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError("Model bundle not found. Please train the model first.")
    bundle = load(path)
    if not isinstance(bundle, dict) or "model" not in bundle:
        raise ValueError("Unexpected model bundle format.")
    return bundle


def _prepare_row(features: Dict[str, float], columns: List[str]) -> pd.DataFrame:
    row = {}
    for col in columns:
        if col not in features:
            if col == "uv_index":
                row[col] = 0.0
            else:
                raise ValueError(f"Missing feature '{col}'")
        else:
            row[col] = float(features[col])
    return pd.DataFrame([row], columns=columns)


def _confidence(prob: float) -> str:
    if prob >= 0.8 or prob <= 0.2:
        return "high"
    if prob >= 0.6 or prob <= 0.4:
        return "medium"
    return "low"


def predict_conditions(features: Dict[str, float], model_bundle=None) -> Dict:
    bundle = model_bundle or load_model()
    estimator = bundle["model"]
    feature_columns = bundle.get("feature_columns", FEATURE_COLUMNS)
    label_columns = bundle.get("label_columns", LABEL_COLUMNS)

    x = _prepare_row(features, feature_columns)
    preds = estimator.predict(x)[0]

    probas = {}
    if hasattr(estimator, "predict_proba"):
        raw_prob = estimator.predict_proba(x)
        for idx, label in enumerate(label_columns):
            label_prob = raw_prob[idx][0, 1] if isinstance(raw_prob, list) else raw_prob[:, idx]
            probas[label] = float(np.clip(label_prob, 0.0, 1.0))
    else:
        probas = {label: None for label in label_columns}

    states = {label: bool(preds[idx]) for idx, label in enumerate(label_columns)}
    confidences = {
        label: _confidence(probas[label]) if probas[label] is not None else "unknown"
        for label in label_columns
    }

    rain_state = states.get(RAIN_LABEL_KEY, False)
    rain_prob = probas.get(RAIN_LABEL_KEY)

    return {
        "states": states,
        "probabilities": probas,
        "confidences": confidences,
        "label": "Rain" if rain_state else "NoRain",
        "proba": rain_prob,
    }
