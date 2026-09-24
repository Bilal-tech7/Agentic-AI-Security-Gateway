import json

from src.approval import (
    APPROVAL_FILE,
    create_approval_request,
    approve_request,
    get_approval,
)


def test_approval_identity_tampering():
    print()
    print("=" * 60)
    print("TEST 15 - APPROVAL IDENTITY TAMPERING PROTECTION")
    print("=" * 60)

    # Create an approval belonging to the legitimate claims officer.
    approval = create_approval_request(
        agent_id="claims-agent-01",
        user_id=3,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": 5
        },
        reason="Test approval identity tampering protection.",
    )

    approval_id = approval["approval_id"]

    print()
    print("Created approval:")
    print(approval)

    assert approval_id is not None
    assert approval["user_id"] == 3
    assert approval["user_role"] == "CLAIMS_OFFICER"
    assert approval["status"] == "PENDING"
    assert "integrity_hash" in approval

    # Tamper with the actual persisted approval record.
    with open(
        APPROVAL_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        records = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

    for record in records:
        if record["approval_id"] == approval_id:
            record["user_id"] = 999
            record["user_role"] = "CLAIMS_ASSISTANT"
            break
    else:
        raise AssertionError(
            "Created approval was not found in approval storage."
        )

    with open(
        APPROVAL_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                json.dumps(record)
                + "\n"
            )

    tampered = get_approval(approval_id)

    print()
    print("Tampered approval:")
    print(tampered)

    assert tampered["user_id"] == 999
    assert tampered["user_role"] == "CLAIMS_ASSISTANT"
    assert tampered["status"] == "PENDING"

    # Attempt to approve the tampered request.
    approval_attempt = approve_request(approval_id)

    print()
    print("Approval attempt after identity tampering:")
    print(approval_attempt)

    assert approval_attempt["success"] is False
    assert (
        "integrity"
        in approval_attempt["error"].lower()
    )

    # Verify that the request remains pending.
    final_approval = get_approval(approval_id)

    print()
    print("Final approval record:")
    print(final_approval)

    assert final_approval["status"] == "PENDING"

    print()
    print("=" * 60)
    print("APPROVAL IDENTITY TAMPERING PROTECTION PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_approval_identity_tampering()
