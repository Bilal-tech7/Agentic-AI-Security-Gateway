from unittest.mock import patch

from src.security_gateway import (
    Decision,
    SecurityRequest,
    evaluate_request_with_ml,
)


def test_ml_failure_does_not_bypass_block():

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=999,
        user_role="CLAIMS_ASSISTANT",
        tool_name="delete_claim",
        arguments={
            "claim_id": 1
        },
    )

    with patch(
        "src.ml_risk.analyze_request_risk",
        side_effect=RuntimeError(
            "Simulated ML model failure"
        ),
    ):

        result = evaluate_request_with_ml(request)

    print()
    print("=" * 60)
    print("ML FAIL-SAFE TEST")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.BLOCK

    assert result.ml_analysis_available is False

    assert result.ml_risk_probability is None

    assert result.ml_risk_band == "UNAVAILABLE"

    print()
    print(
        "PASS: deterministic security remained active "
        "during ML failure."
    )


if __name__ == "__main__":

    test_ml_failure_does_not_bypass_block()

    print()
    print("=" * 60)
    print("ML FAIL-SAFE SECURITY PASSED")
    print("=" * 60)