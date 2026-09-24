from src.database import SessionLocal
from src.models import (
    Claim,
    ClaimAssignment,
    User,
)

from src.security_gateway import (
    Decision,
    SecurityRequest,
    evaluate_request_with_ml,
)


def find_assigned_user_and_claim():

    db = SessionLocal()

    try:

        result = (
            db.query(
                User,
                Claim,
            )
            .join(
                ClaimAssignment,
                ClaimAssignment.user_id == User.user_id,
            )
            .join(
                Claim,
                Claim.claim_id == ClaimAssignment.claim_id,
            )
            .filter(
                User.role == "CLAIMS_ASSISTANT",
                ClaimAssignment.active.is_(True),
            )
            .first()
        )

        if result is None:
            raise AssertionError(
                "No active claim assignment found "
                "for a CLAIMS_ASSISTANT."
            )

        user, claim = result

        return user.user_id, claim.claim_id

    finally:
        db.close()


def test_normal_request_with_ml():

    user_id, claim_id = find_assigned_user_and_claim()

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=user_id,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": claim_id
        },
    )

    result = evaluate_request_with_ml(request)

    print()
    print("=" * 60)
    print("HYBRID TEST 1 - NORMAL REQUEST")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.ALLOW
    assert result.ml_analysis_available is True
    assert result.ml_risk_probability is not None


def test_ml_cannot_override_deterministic_block():

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=999,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 50
        },
    )

    result = evaluate_request_with_ml(request)

    print()
    print("=" * 60)
    print("HYBRID TEST 2 - BLOCK CANNOT BE OVERRIDDEN")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.BLOCK

    print(
        "PASS: ML did not override deterministic BLOCK."
    )


def test_injection_signal():

    user_id, claim_id = find_assigned_user_and_claim()

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=user_id,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim_documents",
        arguments={
            "claim_id": claim_id
        },
    )

    result = evaluate_request_with_ml(
        request,
        sensitive_document=True,
        prompt_injection_signal=True,
    )

    print()
    print("=" * 60)
    print("HYBRID TEST 3 - INJECTION SIGNAL")
    print("=" * 60)
    print(result)

    assert result.ml_analysis_available is True

    assert result.ml_risk_probability >= 0.80

    assert result.ml_risk_band == "CRITICAL"


def test_unknown_tool_still_blocked():

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=999,
        user_role="CLAIMS_ASSISTANT",
        tool_name="totally_fake_tool",
        arguments={},
    )

    result = evaluate_request_with_ml(request)

    print()
    print("=" * 60)
    print("HYBRID TEST 4 - UNKNOWN TOOL")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.BLOCK

    assert result.ml_analysis_available is True

    assert result.ml_risk_probability >= 0.80


if __name__ == "__main__":

    test_normal_request_with_ml()
    test_ml_cannot_override_deterministic_block()
    test_injection_signal()
    test_unknown_tool_still_blocked()

    print()
    print("=" * 60)
    print("ALL HYBRID ML GATEWAY TESTS PASSED")
    print("=" * 60)