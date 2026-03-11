"""
Step 4: Train XGBoost classifier and calibrate probabilities.
Only matches where BOTH players are active (not retired) are used for
training. Full historical data still flows through the Elo pipeline to
produce good features; we simply restrict which match outcomes the model
learns from so it focuses on current player patterns.
Temporal split: Train ≤2021, Val 2022-2023, Test 2024+.
Includes Optuna hyperparameter tuning (~50 trials on validation AUC).
Outputs: data/models/xgboost_model.pkl, model_metadata.json
"""

import json
import pickle
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MATCHES_CLEAN_PATH, MODEL_PATH, MODEL_METADATA_PATH, MODELS_DIR, FEATURE_COLUMNS

from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, brier_score_loss, accuracy_score
import xgboost as xgb
import optuna


def temporal_split(df: pd.DataFrame):
    train = df[df["Date"] < "2022-01-01"]
    val   = df[(df["Date"] >= "2022-01-01") & (df["Date"] < "2024-01-01")]
    test  = df[df["Date"] >= "2024-01-01"]
    return train, val, test


def evaluate(model, X, y, label=""):
    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= 0.5).astype(int)
    auc = roc_auc_score(y, probs)
    brier = brier_score_loss(y, probs)
    acc = accuracy_score(y, preds)
    print(f"  [{label}] AUC={auc:.4f}  Brier={brier:.4f}  Acc={acc:.4f}")
    return {"auc": auc, "brier": brier, "accuracy": acc}


def evaluate_per_surface(model, df, label=""):
    """Print per-surface metrics for diagnostic purposes."""
    if "Surface" not in df.columns:
        return
    print(f"  [{label}] Per-surface breakdown:")
    for surface in sorted(df["Surface"].unique()):
        subset = df[df["Surface"] == surface]
        if len(subset) < 20:
            continue
        X = subset[FEATURE_COLUMNS].values
        y = subset["p1_won"].values
        probs = model.predict_proba(X)[:, 1]
        preds = (probs >= 0.5).astype(int)
        auc = roc_auc_score(y, probs) if len(np.unique(y)) > 1 else float("nan")
        acc = accuracy_score(y, preds)
        print(f"    {surface:8s}  n={len(subset):5d}  AUC={auc:.4f}  Acc={acc:.4f}")


def tune_hyperparameters(X_train, y_train, X_val, y_val, n_trials=50):
    """Use Optuna to find the best XGBoost hyperparameters."""
    print(f"\n  Hyperparameter tuning ({n_trials} trials)...")

    def objective(trial):
        params = {
            "n_estimators": 1000,
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "gamma": trial.suggest_float("gamma", 0.0, 0.5),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.5, 3.0),
            "eval_metric": "logloss",
            "early_stopping_rounds": 50,
    
            "random_state": 42,
            "n_jobs": -1,
        }

        model = xgb.XGBClassifier(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=0,
        )

        val_probs = model.predict_proba(X_val)[:, 1]
        return roc_auc_score(y_val, val_probs)

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", study_name="xgboost-tennis")
    study.optimize(objective, n_trials=n_trials)

    print(f"  Best trial AUC: {study.best_value:.4f}")
    print(f"  Best params: {study.best_params}")

    return study.best_params


def train_model(df: pd.DataFrame):
    train, val, test = temporal_split(df)
    print(f"  Train: {len(train):,}  Val: {len(val):,}  Test: {len(test):,}")

    X_train = train[FEATURE_COLUMNS].values
    y_train = train["p1_won"].values
    X_val   = val[FEATURE_COLUMNS].values
    y_val   = val["p1_won"].values
    X_test  = test[FEATURE_COLUMNS].values
    y_test  = test["p1_won"].values

    # Hyperparameter tuning (200 trials)
    best_params = tune_hyperparameters(X_train, y_train, X_val, y_val, n_trials=200)

    # Probe fit on train-only to find the optimal iteration count via early stopping
    print("\n  Probe fit (train-only) to determine best n_estimators...")
    probe = xgb.XGBClassifier(
        n_estimators=1000,
        max_depth=best_params["max_depth"],
        learning_rate=best_params["learning_rate"],
        subsample=best_params["subsample"],
        colsample_bytree=best_params["colsample_bytree"],
        min_child_weight=best_params["min_child_weight"],
        gamma=best_params["gamma"],
        reg_alpha=best_params["reg_alpha"],
        reg_lambda=best_params["reg_lambda"],
        eval_metric="logloss",
        early_stopping_rounds=50,
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
    )
    probe.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=100)
    # Scale up slightly: more training data typically needs a few more trees
    best_n = int((probe.best_iteration + 1) * 1.15)
    print(f"  Probe best iteration: {probe.best_iteration} → using {best_n} trees for combined fit")

    # Final model trained on train + val combined (no early stopping needed)
    print("\n  Training final model on train+val combined...")
    X_combined = np.vstack([X_train, X_val])
    y_combined = np.concatenate([y_train, y_val])
    base_model = xgb.XGBClassifier(
        n_estimators=best_n,
        max_depth=best_params["max_depth"],
        learning_rate=best_params["learning_rate"],
        subsample=best_params["subsample"],
        colsample_bytree=best_params["colsample_bytree"],
        min_child_weight=best_params["min_child_weight"],
        gamma=best_params["gamma"],
        reg_alpha=best_params["reg_alpha"],
        reg_lambda=best_params["reg_lambda"],
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
    )
    base_model.fit(X_combined, y_combined, verbose=0)
    print(f"  Trained on {len(X_combined):,} matches ({len(X_train):,} train + {len(X_val):,} val)")

    print("  Calibrating probabilities (isotonic) on val set...")
    calibrated = CalibratedClassifierCV(base_model, method="isotonic", cv="prefit")
    calibrated.fit(X_val, y_val)

    print("\nEvaluation:")
    train_metrics = evaluate(calibrated, X_train, y_train, "Train")
    val_metrics   = evaluate(calibrated, X_val,   y_val,   "Val  ")
    test_metrics  = evaluate(calibrated, X_test,  y_test,  "Test ")

    # Per-surface breakdown
    evaluate_per_surface(calibrated, test, "Test ")

    # Feature importance
    importances = base_model.feature_importances_
    feat_importance = sorted(
        zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True
    )
    print("\nTop 15 features by importance:")
    for feat, imp in feat_importance[:15]:
        print(f"  {feat:35s} {imp:.4f}")

    return calibrated, test_metrics, feat_importance, best_params


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading feature matrix...")
    df = pd.read_parquet(MATCHES_CLEAN_PATH)
    print(f"  {len(df):,} total matches")

    # Restrict training to matches where both players are active (not retired)
    if "both_active" in df.columns:
        df_train = df[df["both_active"]].copy()
        print(f"  {len(df_train):,} matches kept (both players active)")
    else:
        df_train = df
        print("  WARNING: both_active flag missing — training on full dataset")

    model, test_metrics, feat_importance, best_params = train_model(df_train)

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"\nSaved model → {MODEL_PATH}")

    # Save metadata
    metadata = {
        "trained_at": datetime.utcnow().isoformat(),
        "feature_columns": FEATURE_COLUMNS,
        "test_metrics": test_metrics,
        "best_hyperparameters": best_params,
        "feature_importance": [
            {"feature": f, "importance": float(i)} for f, i in feat_importance
        ],
    }
    with open(MODEL_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata → {MODEL_METADATA_PATH}")


if __name__ == "__main__":
    main()
