from src.approval import (
    create_approval_request,
    approve_request,
    get_approval,
)


def test_approval_authorization_security():
    print()
    print("=" * 60)
    print("TEST 14 - APPROVAL AUTHORIZATION SECURITY")
    print("=" * 60)

    # Create an approval request for a CLAIMS_OFFICER.
    approval = create_approval_request(
        agent_id="claims-agent-01",
        user_id=3,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": 4
        },
        reason="Test approval authorization security.",
    )

    approval_id = approval["approval_id"]

    print()
    print("Created approval:")
    print(approval)

    # Verify the approval contains the expected authorization context.
    assert approval_id is not None
    assert approval["agent_id"] == "claims-agent-01"
    assert approval["user_id"] == 3
    assert approval["user_role"] == "CLAIMS_OFFICER"
    assert approval["tool_name"] == "approve_settlement"
    assert approval["arguments"]["claim_id"] == 4
    assert approval["status"] == "PENDING"

    # Retrieve the approval from storage.
    stored = get_approval(approval_id)

    print()
    print("Stored approval:")
    print(stored)

    assert stored is not None
    assert stored["approval_id"] == approval_id
    assert stored["agent_id"] == "claims-agent-01"
    assert stored["user_id"] == 3
    assert stored["user_role"] == "CLAIMS_OFFICER"
    assert stored["tool_name"] == "approve_settlement"
    assert stored["arguments"]["claim_id"] == 4
    assert stored["status"] == "PENDING"

    # Human approval.
    approved = approve_request(approval_id)

    print()
    print("Approved:")
    print(approved)

    assert approved["success"] is True
    assert approved["approval_id"] == approval_id
    assert approved["status"] == "APPROVED"

    # Verify the approved request still contains the original
    # authorization context.
    final_approval = get_approval(approval_id)

    print()
    print("Final approval record:")
    print(final_approval)

    assert final_approval is not None
    assert final_approval["approval_id"] == approval_id
    assert final_approval["agent_id"] == "claims-agent-01"
    assert final_approval["user_id"] == 3
    assert final_approval["user_role"] == "CLAIMS_OFFICER"
    assert final_approval["tool_name"] == "approve_settlement"
    assert final_approval["arguments"]["claim_id"] == 4
    assert final_approval["status"] == "APPROVED"

    print()
    print("=" * 60)
    print("APPROVAL AUTHORIZATION SECURITY PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_approval_authorization_security()
