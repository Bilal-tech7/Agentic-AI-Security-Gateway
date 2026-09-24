from src.hybrid_gateway import evaluate_hybrid_request

from src.security_gateway import (
    SecurityRequest,
    Decision,
)


def test_normal_request():

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 1
        },
    )

    result = evaluate_hybrid_request(request)

    print()
    print("=" * 60)
    print("HYBRID TEST 1 - NORMAL REQUEST")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.ALLOW


def test_prompt_injection_escalation():

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 1
        },
    )

    result = evaluate_hybrid_request(
        request,
        sensitive_document=True,
        prompt_injection_signal=True,
    )

    print()
    print("=" * 60)
    print("HYBRID TEST 2 - PROMPT INJECTION")
    print("=" * 60)
    print(result)

    assert result.ml_risk_band == "CRITICAL"
    assert result.decision == Decision.BLOCK
    assert result.ml_escalated is True


def test_deterministic_block_cannot_be_overridden():

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=999,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 50
        },
    )

    result = evaluate_hybrid_request(request)

    print()
    print("=" * 60)
    print("HYBRID TEST 3 - DETERMINISTIC BLOCK")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.BLOCK


def test_unknown_tool_remains_blocked():

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="unknown_tool",
        arguments={},
    )

    result = evaluate_hybrid_request(request)

    print()
    print("=" * 60)
    print("HYBRID TEST 4 - UNKNOWN TOOL")
    print("=" * 60)
    print(result)

    assert result.decision == Decision.BLOCK


if __name__ == "__main__":

    test_normal_request()
    test_prompt_injection_escalation()
    test_deterministic_block_cannot_be_overridden()
    test_unknown_tool_remains_blocked()

    print()
    print("=" * 60)
    print("ALL HYBRID ENFORCEMENT TESTS PASSED")
    print("=" * 60)