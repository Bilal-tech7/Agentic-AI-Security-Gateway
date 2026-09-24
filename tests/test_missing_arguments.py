from src.protected_tools import execute_protected_tool


def test_missing_required_arguments():
    print()
    print("=" * 60)
    print("TEST 9 - MISSING REQUIRED ARGUMENTS SECURITY")
    print("=" * 60)

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=3,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={},
    )

    print()
    print("Security result:")
    print(result)

    assert result["success"] is False
    assert result["executed"] is False
    assert result["decision"] == "BLOCK"

    print()
    print("=" * 60)
    print("MISSING REQUIRED ARGUMENTS SECURITY PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_missing_required_arguments()
