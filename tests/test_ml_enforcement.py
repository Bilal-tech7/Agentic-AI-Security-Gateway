from src.hybrid_policy import apply_ml_enforcement
from src.security_gateway import (
    Decision,
    RiskLevel,
    SecurityDecision,
)


def make_allow_decision():
    return SecurityDecision(
        decision=Decision.ALLOW,
        risk_level=RiskLevel.LOW,
        reason="Tool and resource are permitted for this user.",
    )


def test_low_ml_risk_remains_allowed():

    deterministic = make_allow_decision()

    ml_result = {
        "risk_probability": 0.05,
        "risk_band": "LOW",
    }

    result = apply_ml_enforcement(
        deterministic,
        ml_result,
    )

    print()
    print("=" * 60)
    print("D.3 TEST 1 - LOW ML RISK")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.ALLOW
    assert result.ml_escalated is False


def test_medium_ml_risk_remains_allowed():

    deterministic = make_allow_decision()

    ml_result = {
        "risk_probability": 0.55,
        "risk_band": "MEDIUM",
    }

    result = apply_ml_enforcement(
        deterministic,
        ml_result,
    )

    print()
    print("=" * 60)
    print("D.3 TEST 2 - MEDIUM ML RISK")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.ALLOW
    assert result.ml_escalated is False


def test_high_ml_risk_requires_human_review():

    deterministic = make_allow_decision()

    ml_result = {
        "risk_probability": 0.80,
        "risk_band": "HIGH",
    }

    result = apply_ml_enforcement(
        deterministic,
        ml_result,
    )

    print()
    print("=" * 60)
    print("D.3 TEST 3 - HIGH ML RISK")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.HUMAN_REVIEW
    assert result.risk_level == RiskLevel.HIGH
    assert result.ml_escalated is True


def test_critical_ml_risk_is_blocked():

    deterministic = make_allow_decision()

    ml_result = {
        "risk_probability": 0.99,
        "risk_band": "CRITICAL",
    }

    result = apply_ml_enforcement(
        deterministic,
        ml_result,
    )

    print()
    print("=" * 60)
    print("D.3 TEST 4 - CRITICAL ML RISK")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.BLOCK
    assert result.risk_level == RiskLevel.CRITICAL
    assert result.ml_escalated is True


def test_ml_cannot_override_deterministic_block():

    deterministic = SecurityDecision(
        decision=Decision.BLOCK,
        risk_level=RiskLevel.HIGH,
        reason="User is not authorized for this resource.",
    )

    ml_result = {
        "risk_probability": 0.01,
        "risk_band": "LOW",
    }

    result = apply_ml_enforcement(
        deterministic,
        ml_result,
    )

    print()
    print("=" * 60)
    print("D.3 TEST 5 - ML CANNOT OVERRIDE BLOCK")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.BLOCK
    assert result.ml_escalated is False


def test_ml_cannot_bypass_human_review():

    deterministic = SecurityDecision(
        decision=Decision.HUMAN_REVIEW,
        risk_level=RiskLevel.CRITICAL,
        reason="High-risk tool requires human approval.",
    )

    ml_result = {
        "risk_probability": 0.01,
        "risk_band": "LOW",
    }

    result = apply_ml_enforcement(
        deterministic,
        ml_result,
    )

    print()
    print("=" * 60)
    print("D.3 TEST 6 - ML CANNOT BYPASS HUMAN REVIEW")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.HUMAN_REVIEW
    assert result.ml_escalated is False


def test_ml_failure_preserves_deterministic_security():

    deterministic = make_allow_decision()

    result = apply_ml_enforcement(
        deterministic,
        None,
    )

    print()
    print("=" * 60)
    print("D.3 TEST 7 - ML FAIL-SAFE")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.ALLOW
    assert result.ml_available is False
    assert result.ml_escalated is False


if __name__ == "__main__":

    test_low_ml_risk_remains_allowed()
    test_medium_ml_risk_remains_allowed()
    test_high_ml_risk_requires_human_review()
    test_critical_ml_risk_is_blocked()
    test_ml_cannot_override_deterministic_block()
    test_ml_cannot_bypass_human_review()
    test_ml_failure_preserves_deterministic_security()

    print()
    print("=" * 60)
    print("ALL STAGE D.3 ML ENFORCEMENT TESTS PASSED")
    print("=" * 60)