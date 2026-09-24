import json

from src.approval import (
    create_approval_request,
    approve_request,
    execute_approved_request,
    get_approval,
    APPROVAL_FILE,
)


def test_approval_tampering_protection():
    print()
    print("=" * 60)
    print("TEST 10 - APPROVAL TAMPERING PROTECTION")
    print("=" * 60)

    approval = create_approval_request(
        agent_id="claims-agent-01",
        user_id=3,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": 3
        },
        reason="Test approval tampering protection.",
    )

    approval_id = approval["approval_id"]

    print("Created approval:")
    print(approval)

    approved = approve_request(approval_id)

    print()
    print("Approved:")
    print(approved)

    assert approved["success"] is True
    assert approved["status"] == "APPROVED"

    # Tamper with the approved request.
    approvals = []

    with open(
        APPROVAL_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if record["approval_id"] == approval_id:
                record["arguments"]["claim_id"] = 1

            approvals.append(record)

    with open(
        APPROVAL_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        for record in approvals:
            file.write(json.dumps(record) + "\n")

    print()
    print("Tampered approval:")
    print(get_approval(approval_id))

    execution = execute_approved_request(approval_id)

    print()
    print("Execution attempt after tampering:")
    print(execution)

    assert execution["success"] is False
    assert execution["approval_id"] == approval_id

    final_approval = get_approval(approval_id)

    print()
    print("Final approval record:")
    print(final_approval)

    assert final_approval["status"] != "EXECUTED"

    print()
    print("=" * 60)
    print("APPROVAL TAMPERING PROTECTION PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_approval_tampering_protection()
