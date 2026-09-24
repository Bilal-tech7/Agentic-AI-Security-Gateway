from src.protected_tools import execute_protected_tool


def main():

    print()
    print("=" * 60)
    print("ADVERSARIAL DOCUMENT TEST")
    print("=" * 60)

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim_documents",
        arguments={
            "claim_id": 1
        },
    )

    print()
    print("=" * 60)
    print("PROTECTED TOOL RESULT")
    print("=" * 60)

    print(result)


if __name__ == "__main__":
    main()
