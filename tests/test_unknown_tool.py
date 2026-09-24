from src.protected_tools import execute_protected_tool


def test_unknown_tool_security():
    print()
    print("=" * 60)
    print("TEST 7 - UNKNOWN TOOL SECURITY")
    print("=" * 60)

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="unknown_tool",
        arguments={},
    )

    print()
    print("Security result:")
    print(result)

    assert result["success"] is False
    assert result["executed"] is False
    assert result["decision"] == "BLOCK"
    assert result["risk_level"] == "HIGH"

    print()
    print("=" * 60)
    print("UNKNOWN TOOL SECURITY PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_unknown_tool_security()
