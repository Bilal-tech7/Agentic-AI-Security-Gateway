from pathlib import Path
import random

import joblib
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)
from sklearn.model_selection import train_test_split

from src.ml_risk import (
    FEATURE_NAMES,
    MODEL_PATH,
)


SEED = 42

random.seed(SEED)
np.random.seed(SEED)


def make_sample(
    *,
    is_high_risk_tool=0,
    is_unknown_tool=0,
    is_resource_scoped=1,
    is_assigned=1,
    role_tool_mismatch=0,
    malformed_arguments=0,
    missing_claim_id=0,
    sensitive_document=0,
    prompt_injection_signal=0,
    unusual_access_volume=0,
):
    return [
        is_high_risk_tool,
        is_unknown_tool,
        is_resource_scoped,
        is_assigned,
        role_tool_mismatch,
        malformed_arguments,
        missing_claim_id,
        sensitive_document,
        prompt_injection_signal,
        unusual_access_volume,
    ]


def calculate_synthetic_risk(features):
    """
    Create controlled ground-truth labels for the prototype.

    This is intentionally explicit. The generated labels are
    synthetic security scenarios, not historical production
    attack labels.
    """

    (
        high_risk,
        unknown_tool,
        resource_scoped,
        assigned,
        role_mismatch,
        malformed,
        missing_claim,
        sensitive_document,
        injection,
        unusual_volume,
    ) = features

    score = 0

    score += high_risk * 4
    score += unknown_tool * 5
    score += role_mismatch * 4
    score += malformed * 3
    score += missing_claim * 3
    score += sensitive_document * 2
    score += injection * 6
    score += unusual_volume * 3

    if resource_scoped and not assigned:
        score += 5

    # Combination effects
    if injection and sensitive_document:
        score += 3

    if high_risk and role_mismatch:
        score += 3

    if unusual_volume and sensitive_document:
        score += 2

    return score


def generate_dataset(n_samples=2500):
    X = []
    y = []

    for _ in range(n_samples):

        features = make_sample(
            is_high_risk_tool=random.randint(0, 1),
            is_unknown_tool=(
                1 if random.random() < 0.12 else 0
            ),
            is_resource_scoped=(
                1 if random.random() < 0.80 else 0
            ),
            is_assigned=(
                1 if random.random() < 0.75 else 0
            ),
            role_tool_mismatch=(
                1 if random.random() < 0.20 else 0
            ),
            malformed_arguments=(
                1 if random.random() < 0.12 else 0
            ),
            missing_claim_id=(
                1 if random.random() < 0.10 else 0
            ),
            sensitive_document=(
                1 if random.random() < 0.20 else 0
            ),
            prompt_injection_signal=(
                1 if random.random() < 0.10 else 0
            ),
            unusual_access_volume=(
                1 if random.random() < 0.15 else 0
            ),
        )

        score = calculate_synthetic_risk(features)

        # Binary behavioural-risk label.
        label = 1 if score >= 5 else 0

        X.append(features)
        y.append(label)

    return np.array(X), np.array(y)


def main():

    print()
    print("=" * 70)
    print("AURELIA ML SECURITY RISK MODEL")
    print("TRAINING AND EVALUATION")
    print("=" * 70)

    X, y = generate_dataset()

    print()
    print(f"Samples:           {len(X)}")
    print(f"Features:          {len(FEATURE_NAMES)}")
    print(f"Normal samples:    {(y == 0).sum()}")
    print(f"Risk samples:      {(y == 1).sum()}")

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=SEED,
            stratify=y,
        )
    )

    model = LogisticRegression(
        max_iter=2000,
        random_state=SEED,
        class_weight="balanced",
    )

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
    )

    tn, fp, fn, tp = matrix.ravel()

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0
    )

    false_negative_rate = (
        fn / (fn + tp)
        if (fn + tp) > 0
        else 0
    )

    print()
    print("=" * 70)
    print("MODEL PERFORMANCE")
    print("=" * 70)

    print(f"Accuracy:            {accuracy:.4f}")
    print(f"Precision:           {precision:.4f}")
    print(f"Recall:              {recall:.4f}")
    print(f"F1-score:            {f1:.4f}")
    print(
        f"False-positive rate: {false_positive_rate:.4f}"
    )
    print(
        f"False-negative rate: {false_negative_rate:.4f}"
    )

    print()
    print("Confusion matrix:")
    print(matrix)

    print()
    print("Classification report:")
    print(
        classification_report(
            y_test,
            predictions,
            digits=4,
        )
    )

    print()
    print("=" * 70)
    print("LEARNED FEATURE WEIGHTS")
    print("=" * 70)

    weights = sorted(
        zip(
            FEATURE_NAMES,
            model.coef_[0],
        ),
        key=lambda item: abs(item[1]),
        reverse=True,
    )

    for feature, weight in weights:
        print(
            f"{feature:<28} {weight:>8.4f}"
        )

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print()
    print("=" * 70)
    print("MODEL SAVED")
    print("=" * 70)

    print(MODEL_PATH)


if __name__ == "__main__":
    main()