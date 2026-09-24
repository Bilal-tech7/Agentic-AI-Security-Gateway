from src.protected_tools import execute_protected_tool


def test_malformed_arguments_security():
    print()
    print("=" * 60)
    print("TEST 8 - MALFORMED ARGUMENTS SECURITY")
    print("=" * 60)

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": "INVALID"
        },
    )

    print()
    print("Security result:")
    print(result)

    assert result["success"] is False
    assert result["executed"] is False

    print()
    print("=" * 60)
    print("MALFORMED ARGUMENTS SECURITY PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_malformed_arguments_security()
