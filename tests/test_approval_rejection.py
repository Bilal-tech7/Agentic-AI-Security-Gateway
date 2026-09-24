from src.approval import (
    create_approval_request,
    reject_request,
    execute_approved_request,
    get_approval,
)


def test_approval_rejection_security():
    print()
    print("=" * 60)
    print("TEST 6 - APPROVAL REJECTION SECURITY")
    print("=" * 60)

    # Use a claim that is not already settlement approved.
    claim_id = 3

    # Create approval request
    approval = create_approval_request(
        agent_id="claims-agent-01",
        user_id=3,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": claim_id
        },
        reason="Test approval rejection security.",
    )

    approval_id = approval["approval_id"]

    print("Created approval:")
    print(approval)

    assert approval["status"] == "PENDING"

    # Human rejects the request
    rejected = reject_request(approval_id)

    print()
    print("Rejected:")
    print(rejected)

    assert rejected["success"] is True
    assert rejected["status"] == "REJECTED"

    # Attempt to execute the rejected approval
    execution = execute_approved_request(
        approval_id
    )

    print()
    print("Execution attempt after rejection:")
    print(execution)

    assert execution["success"] is False

    # Verify the approval remains REJECTED
    final_approval = get_approval(
        approval_id
    )

    print()
    print("Final approval record:")
    print(final_approval)

    assert final_approval["status"] == "REJECTED"

    print()
    print("=" * 60)
    print("APPROVAL REJECTION SECURITY PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_approval_rejection_security()
