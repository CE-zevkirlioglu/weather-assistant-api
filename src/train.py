import argparse
import os

from joblib import dump
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

from prepare_data import load_dataset, FEATURE_COLUMNS, LABEL_COLUMNS


def _evaluate(y_true, y_pred):
    scores = {}
    macro_f1 = []
    for idx, label in enumerate(LABEL_COLUMNS):
        precision = precision_score(y_true[:, idx], y_pred[:, idx], zero_division=0)
        recall = recall_score(y_true[:, idx], y_pred[:, idx], zero_division=0)
        f1 = f1_score(y_true[:, idx], y_pred[:, idx], zero_division=0)
        scores[label] = {"precision": precision, "recall": recall, "f1": f1}
        macro_f1.append(f1)
    return scores, float(np.mean(macro_f1))


def _print_scores(name, scores, macro_f1):
    print(f"--- {name} ---")
    for label, metrics in scores.items():
        print(
            f"{label:>12}: precision={metrics['precision']:.3f} | recall={metrics['recall']:.3f} | f1={metrics['f1']:.3f}"
        )
    print(f"Macro F1: {macro_f1:.3f}\n")


def build_candidates():
    logistic = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "clf",
                MultiOutputClassifier(
                    LogisticRegression(
                        max_iter=800,
                        class_weight="balanced",
                        solver="lbfgs",
                    )
                ),
            ),
        ]
    )

    forest = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "clf",
                MultiOutputClassifier(
                    RandomForestClassifier(
                        n_estimators=400,
                        max_depth=20,
                        min_samples_split=40,
                        min_samples_leaf=8,
                        class_weight="balanced_subsample",
                        n_jobs=-1,
                        random_state=42,
                    )
                ),
            ),
        ]
    )

    return {
        "logistic_regression": logistic,
        "random_forest": forest,
    }


def train(csv_path, out_dir):
    X, y, _ = load_dataset(csv_path)
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y["label_rain"]
    )

    candidates = build_candidates()
    evaluated = []

    for name, model in candidates.items():
        model.fit(Xtr, ytr)
        ypred = model.predict(Xte)
        scores, macro_f1 = _evaluate(yte.values, ypred)
        _print_scores(name, scores, macro_f1)
        evaluated.append((name, macro_f1, model, scores))

    best = max(evaluated, key=lambda item: item[1])
    best_name, best_score, best_model, best_scores = best
    print(f"Selected best model: {best_name} (macro F1={best_score:.3f})")

    bundle = {
        "model": best_model,
        "feature_columns": FEATURE_COLUMNS,
        "label_columns": LABEL_COLUMNS,
        "model_name": best_name,
        "scores": best_scores,
    }

    os.makedirs(out_dir, exist_ok=True)
    dump(bundle, os.path.join(out_dir, "weather_model.pkl"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../data/processed/weather_training.csv")
    parser.add_argument("--out", default="../models")
    args = parser.parse_args()
    train(args.csv, args.out)


if __name__ == "__main__":
    main()
