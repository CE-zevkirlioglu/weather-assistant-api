import pandas as pd

FEATURE_COLUMNS = ["temp", "humidity", "wind_speed", "pressure", "clouds", "uv_index"]
LABEL_COLUMNS = ["label_rain", "label_hot", "label_cold", "label_uv_high", "label_windy"]


def load_dataset(csv_path):
    df = pd.read_csv(csv_path)
    for col in FEATURE_COLUMNS + LABEL_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Missing {col}")
    df = df.dropna(subset=FEATURE_COLUMNS)
    X = df[FEATURE_COLUMNS].astype(float)
    y = df[LABEL_COLUMNS].astype(int)
    return X, y, df.get("source")
