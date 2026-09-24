from pathlib import Path

import joblib


MODEL_PATH = Path("models/risk_model.joblib")


FEATURE_NAMES = [
    "is_high_risk_tool",
    "is_unknown_tool",
    "is_resource_scoped",
    "is_assigned",
    "role_tool_mismatch",
    "malformed_arguments",
    "missing_claim_id",
    "sensitive_document",
    "prompt_injection_signal",
    "unusual_access_volume",
]


def build_risk_features(
    *,
    is_high_risk_tool=False,
    is_unknown_tool=False,
    is_resource_scoped=False,
    is_assigned=True,
    role_tool_mismatch=False,
    malformed_arguments=False,
    missing_claim_id=False,
    sensitive_document=False,
    prompt_injection_signal=False,
    unusual_access_volume=False,
):
    return {
        "is_high_risk_tool": int(is_high_risk_tool),
        "is_unknown_tool": int(is_unknown_tool),
        "is_resource_scoped": int(is_resource_scoped),
        "is_assigned": int(is_assigned),
        "role_tool_mismatch": int(role_tool_mismatch),
        "malformed_arguments": int(malformed_arguments),
        "missing_claim_id": int(missing_claim_id),
        "sensitive_document": int(sensitive_document),
        "prompt_injection_signal": int(
            prompt_injection_signal
        ),
        "unusual_access_volume": int(
            unusual_access_volume
        ),
    }


def feature_vector(features):
    return [
        features[name]
        for name in FEATURE_NAMES
    ]


def load_risk_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Risk model has not been trained. "
            "Run: python train_risk_model.py"
        )

    return joblib.load(MODEL_PATH)


def predict_risk(features):
    """
    Predict behavioural security risk.

    This function provides a supplementary risk signal.
    It does NOT authorize tools or override deterministic
    security decisions.
    """

    model = load_risk_model()

    vector = feature_vector(features)

    probability = float(
        model.predict_proba([vector])[0][1]
    )

    if probability >= 0.80:
        risk_band = "CRITICAL"
    elif probability >= 0.60:
        risk_band = "HIGH"
    elif probability >= 0.30:
        risk_band = "MEDIUM"
    else:
        risk_band = "LOW"

    return {
        "risk_probability": round(probability, 4),
        "risk_band": risk_band,
    }


def analyze_request_risk(
    request,
    *,
    allowed_tools,
    high_risk_tools,
    resource_scoped_tools,
    is_assigned=True,
    sensitive_document=False,
    prompt_injection_signal=False,
    unusual_access_volume=False,
):
    """
    Build ML features from a real security request.

    Deterministic authorization remains the responsibility
    of security_gateway.py.
    """

    arguments = request.arguments

    if not isinstance(arguments, dict):
        arguments = {}

    claim_id = arguments.get("claim_id")

    missing_claim_id = (
        request.tool_name in resource_scoped_tools
        and claim_id is None
    )

    malformed_arguments = (
        request.tool_name in resource_scoped_tools
        and claim_id is not None
        and not isinstance(claim_id, int)
    )

    features = build_risk_features(
        is_high_risk_tool=(
            request.tool_name in high_risk_tools
        ),
        is_unknown_tool=(
            request.tool_name not in allowed_tools
        ),
        is_resource_scoped=(
            request.tool_name in resource_scoped_tools
        ),
        is_assigned=is_assigned,
        role_tool_mismatch=(
            request.tool_name not in allowed_tools
        ),
        malformed_arguments=malformed_arguments,
        missing_claim_id=missing_claim_id,
        sensitive_document=sensitive_document,
        prompt_injection_signal=prompt_injection_signal,
        unusual_access_volume=unusual_access_volume,
    )

    return predict_risk(features)