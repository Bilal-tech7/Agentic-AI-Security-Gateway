from src.protected_tools import execute_protected_tool


def main():

    print()
    print("=" * 60)
    print("PROMPT INJECTION GATEWAY DEFENSE TEST")
    print("=" * 60)

    print()
    print("Simulating a malicious document attempting to")
    print("make the agent call export_customer_data.")
    print()

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="export_customer_data",
        arguments={},
    )

    print()
    print("=" * 60)
    print("SECURITY RESULT")
    print("=" * 60)

    print(result)

    assert result["success"] is False
    assert result["executed"] is False
    assert result["decision"] == "BLOCK"

    print()
    print("=" * 60)
    print("PROMPT INJECTION DEFENSE TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
