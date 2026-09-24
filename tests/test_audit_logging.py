import json
import os

from src.protected_tools import execute_protected_tool


AUDIT_FILE = "data/security_audit.jsonl"


def test_audit_logging():
    print()
    print("=" * 60)
    print("TEST 11 - AUDIT LOGGING SECURITY")
    print("=" * 60)

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=3,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 1
        },
    )

    print()
    print("Security result:")
    print(result)

    assert result["success"] is True
    assert result["executed"] is True

    assert os.path.exists(AUDIT_FILE)

    matching_event = None

    with open(
        AUDIT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if not line.strip():
                continue

            event = json.loads(line)

            if (
                event.get("agent_id") == "claims-agent-01"
                and event.get("user_id") == 3
                and event.get("user_role") == "CLAIMS_ASSISTANT"
                and event.get("tool_name") == "get_claim"
                and event.get("decision") == "ALLOW"
                and event.get("executed") is True
            ):
                matching_event = event

    print()
    print("Matching audit event:")
    print(matching_event)

    assert matching_event is not None

    assert matching_event["agent_id"] == "claims-agent-01"
    assert matching_event["user_id"] == 3
    assert matching_event["user_role"] == "CLAIMS_ASSISTANT"
    assert matching_event["tool_name"] == "get_claim"
    assert matching_event["decision"] == "ALLOW"
    assert matching_event["executed"] is True

    print()
    print("=" * 60)
    print("AUDIT LOGGING SECURITY PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_audit_logging()
