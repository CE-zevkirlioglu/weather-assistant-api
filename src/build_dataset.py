import argparse
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURE_COLUMNS = ["temp", "humidity", "wind_speed", "pressure", "clouds", "uv_index"]
LABEL_COLUMNS = ["label_rain", "label_hot", "label_cold", "label_uv_high", "label_windy"]
HOT_THRESHOLD = 30.0
COLD_THRESHOLD = 15.0  # 15°C ve altı soğuk kabul edilir (daha gerçekçi eşik)
UV_THRESHOLD = 5.0  # 5 ve üzeri UV yüksek kabul edilir
WIND_THRESHOLD = 10.0


def _clip(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["humidity"] = df["humidity"].clip(0, 100)
    df["clouds"] = df["clouds"].clip(0, 100)
    df["pressure"] = df["pressure"].clip(870, 1100)
    df["uv_index"] = df["uv_index"].clip(lower=0)
    return df


def _ensure_uv_column(df: pd.DataFrame) -> pd.DataFrame:
    if "uv_index" not in df.columns:
        df["uv_index"] = np.nan
    return df


def _standard_clean(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = _ensure_uv_column(df)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["temp", "humidity", "wind_speed", "pressure", "clouds", "rain"])
    df = _clip(df)
    df["source"] = source
    return df


def _estimate_clouds(summary: str, fallback: float = 50.0) -> float:
    text = (summary or "").lower()
    if "overcast" in text:
        return 95.0
    if "mostly" in text:
        return 80.0
    if "partly" in text:
        return 55.0
    if "cloud" in text:
        return 70.0
    if "fog" in text:
        return 85.0
    if "clear" in text or "sun" in text:
        return 15.0
    return fallback


def load_sample() -> pd.DataFrame:
    sample_path = DATA_DIR / "samples" / "weather_sample.csv"
    if not sample_path.exists():
        return pd.DataFrame(columns=FEATURE_COLUMNS + ["rain", "source"])
    df = pd.read_csv(sample_path)
    df = df.rename(
        columns={
            "temp": "temp",
            "humidity": "humidity",
            "wind_speed": "wind_speed",
            "pressure": "pressure",
            "clouds": "clouds",
            "rain": "rain",
        }
    )
    df["uv_index"] = np.nan
    return _standard_clean(df[["temp", "humidity", "wind_speed", "pressure", "clouds", "rain", "uv_index"]], "sample")


def load_forecast() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "kaggle" / "weather_forecast_data.csv")
    rain_map = (
        df["Rain"].astype(str).str.strip().str.lower().map({"rain": 1, "no rain": 0})
    )
    out = pd.DataFrame(
        {
            "temp": df["Temperature"].astype(float),
            "humidity": df["Humidity"].astype(float),
            "wind_speed": df["Wind_Speed"].astype(float),
            "pressure": df["Pressure"].astype(float),
            "clouds": df["Cloud_Cover"].astype(float),
            "rain": rain_map,
            "uv_index": np.nan,
        }
    )
    return _standard_clean(out, "weather_forecast_data")


def load_global_repo() -> pd.DataFrame:
    usecols = [
        "temperature_celsius",
        "humidity",
        "wind_kph",
        "pressure_mb",
        "cloud",
        "condition_text",
    ]
    df = pd.read_csv(DATA_DIR / "kaggle" / "GlobalWeatherRepository.csv", usecols=usecols)
    condition = (
        df["condition_text"].astype(str).str.lower().str.contains("rain|drizzle|shower|storm|thunder")
    )
    out = pd.DataFrame(
        {
            "temp": df["temperature_celsius"].astype(float),
            "humidity": df["humidity"].astype(float),
            "wind_speed": (df["wind_kph"].astype(float) * 1000.0 / 3600.0),
            "pressure": df["pressure_mb"].astype(float),
            "clouds": df["cloud"].astype(float),
            "rain": condition.astype(int),
            "uv_index": np.nan,
        }
    )
    return _standard_clean(out, "global_weather_repository")


def load_classification() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "kaggle" / "weather_classification_data.csv")
    cloud_map = {
        "clear": 5.0,
        "partly cloudy": 45.0,
        "cloudy": 70.0,
        "overcast": 95.0,
    }
    clouds = df["Cloud Cover"].astype(str).str.strip().str.lower().map(cloud_map)
    out = pd.DataFrame(
        {
            "temp": df["Temperature"].astype(float),
            "humidity": df["Humidity"].astype(float),
            "wind_speed": df["Wind Speed"].astype(float),
            "pressure": df["Atmospheric Pressure"].astype(float),
            "clouds": clouds,
            "rain": df["Weather Type"].astype(str).str.strip().str.lower().str.contains("rain").astype(int),
            "uv_index": df["UV Index"].astype(float),
        }
    )
    return _standard_clean(out, "weather_classification_data")


def load_weather_history() -> pd.DataFrame:
    usecols = [
        "Temperature (C)",
        "Humidity",
        "Wind Speed (km/h)",
        "Pressure (millibars)",
        "Loud Cover",
        "Precip Type",
        "Summary",
    ]
    df = pd.read_csv(DATA_DIR / "kaggle" / "weatherHistory.csv", usecols=usecols)
    humidity = df["Humidity"].astype(float)
    if humidity.max() <= 1.5:
        humidity = humidity * 100.0
    loud_cover = df["Loud Cover"].astype(float)
    clouds = loud_cover * 100.0
    missing_clouds = clouds.isna() | (clouds == 0)
    if missing_clouds.any():
        clouds[missing_clouds] = [
            _estimate_clouds(s, fallback=60.0) for s in df.loc[missing_clouds, "Summary"].tolist()
        ]
    rain = df["Precip Type"].astype(str).str.lower().eq("rain").astype(int)
    out = pd.DataFrame(
        {
            "temp": df["Temperature (C)"].astype(float),
            "humidity": humidity,
            "wind_speed": df["Wind Speed (km/h)"].astype(float) / 3.6,
            "pressure": df["Pressure (millibars)"].astype(float),
            "clouds": clouds,
            "rain": rain,
            "uv_index": np.nan,
        }
    )
    return _standard_clean(out, "weather_history")


def _add_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df["uv_index"].notnull().any():
        uv_fill = float(df["uv_index"].median(skipna=True))
    else:
        uv_fill = 3.0
    df["uv_index"] = df["uv_index"].fillna(uv_fill)
    df["label_rain"] = df["rain"].astype(int)
    df["label_hot"] = (df["temp"] >= HOT_THRESHOLD).astype(int)
    df["label_cold"] = (df["temp"] <= COLD_THRESHOLD).astype(int)
    df["label_uv_high"] = (df["uv_index"] >= UV_THRESHOLD).astype(int)
    df["label_windy"] = (df["wind_speed"] >= WIND_THRESHOLD).astype(int)
    return df


def build_dataset(include_samples: bool = True) -> pd.DataFrame:
    loaders: List[pd.DataFrame] = [
        load_forecast(),
        load_global_repo(),
        load_classification(),
        load_weather_history(),
    ]
    if include_samples:
        loaders.append(load_sample())
    df = pd.concat(loaders, ignore_index=True)
    df = df.drop_duplicates(subset=["temp", "humidity", "wind_speed", "pressure", "clouds", "rain"])
    df = df[df["wind_speed"] >= 0]
    df = df[df["pressure"].notnull()]
    df = _add_labels(df)
    ordered_columns = FEATURE_COLUMNS + ["rain", "source"] + LABEL_COLUMNS
    return df[ordered_columns]


def main(out_path: Path) -> None:
    df = build_dataset()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
    summary = df.groupby("source")[LABEL_COLUMNS].mean()
    print(summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Build unified weather dataset")
    parser.add_argument(
        "--out",
        type=Path,
        default=PROCESSED_DIR / "weather_training.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()
    main(args.out)