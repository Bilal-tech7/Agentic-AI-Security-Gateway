from src.ml_risk import (
    build_risk_features,
    predict_risk,
)


def test_normal_request():

    features = build_risk_features(
        is_resource_scoped=True,
        is_assigned=True,
    )

    result = predict_risk(features)

    print()
    print("=" * 60)
    print("ML TEST 1 - NORMAL ASSIGNED ACCESS")
    print("=" * 60)
    print(result)

    assert 0 <= result["risk_probability"] <= 1


def test_prompt_injection():

    features = build_risk_features(
        is_resource_scoped=True,
        is_assigned=True,
        sensitive_document=True,
        prompt_injection_signal=True,
    )

    result = predict_risk(features)

    print()
    print("=" * 60)
    print("ML TEST 2 - PROMPT INJECTION")
    print("=" * 60)
    print(result)

    assert result["risk_probability"] >= 0.50


def test_unauthorized_resource():

    features = build_risk_features(
        is_resource_scoped=True,
        is_assigned=False,
    )

    result = predict_risk(features)

    print()
    print("=" * 60)
    print("ML TEST 3 - UNASSIGNED RESOURCE")
    print("=" * 60)
    print(result)

    assert result["risk_probability"] >= 0.30
    assert result["risk_band"] in {
      "MEDIUM",
      "HIGH",
      "CRITICAL",
    }


def test_combined_attack():

    features = build_risk_features(
        is_high_risk_tool=True,
        is_unknown_tool=True,
        is_resource_scoped=True,
        is_assigned=False,
        role_tool_mismatch=True,
        sensitive_document=True,
        prompt_injection_signal=True,
        unusual_access_volume=True,
    )

    result = predict_risk(features)

    print()
    print("=" * 60)
    print("ML TEST 4 - COMBINED ATTACK")
    print("=" * 60)
    print(result)

    assert result["risk_probability"] >= 0.80
    assert result["risk_band"] in {
        "HIGH",
        "CRITICAL",
    }


if __name__ == "__main__":

    test_normal_request()
    test_prompt_injection()
    test_unauthorized_resource()
    test_combined_attack()

    print()
    print("=" * 60)
    print("ALL ML RISK TESTS PASSED")
    print("=" * 60)