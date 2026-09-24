from src.protected_tools import execute_protected_tool


def test_allowed_assigned_claim():

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 1
        },
    )

    print()
    print("=" * 60)
    print("TEST 1 - ASSIGNED CLAIM")
    print("=" * 60)

    print(result)

    assert result["success"] is True
    assert result["executed"] is True
    assert result["decision"] == "ALLOW"


def test_blocked_unassigned_claim():

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=999,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 50
        },
    )

    print()
    print("=" * 60)
    print("TEST 2 - UNASSIGNED CLAIM")
    print("=" * 60)

    print(result)

    assert result["success"] is False
    assert result["executed"] is False
    assert result["decision"] == "BLOCK"


def test_blocked_tool():

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="delete_claim",
        arguments={
            "claim_id": 1
        },
    )

    print()
    print("=" * 60)
    print("TEST 3 - UNAUTHORIZED TOOL")
    print("=" * 60)

    print(result)

    assert result["success"] is False
    assert result["executed"] is False
    assert result["decision"] == "BLOCK"


def test_human_review_tool():
    """
    Verify that an authorized claims officer receives
    HUMAN_REVIEW for an eligible settlement request.

    The test dynamically searches for a claim that:
        1. is assigned to a claims officer
        2. is in SETTLEMENT_REVIEW status
    """
    from src.database import SessionLocal
    from src.models import Claim, User, ClaimAssignment

    db = SessionLocal()

    try:
        officer = (
            db.query(User)
            .filter(User.role == "CLAIMS_OFFICER")
            .first()
        )

        if officer is None:
            raise AssertionError(
                "No CLAIMS_OFFICER found in database."
            )

        assignment = (
            db.query(ClaimAssignment)
            .join(
                Claim,
                Claim.claim_id == ClaimAssignment.claim_id
            )
            .filter(
                ClaimAssignment.user_id == officer.user_id,
                ClaimAssignment.active.is_(True),
                Claim.status == "SETTLEMENT_REVIEW"
            )
            .first()
        )

        if assignment is None:
            raise AssertionError(
                "No SETTLEMENT_REVIEW claim is assigned "
                "to the CLAIMS_OFFICER."
            )

        claim_id = assignment.claim_id

    finally:
        db.close()

    result = execute_protected_tool(
        agent_id="claims-agent-01",
        user_id=officer.user_id,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": claim_id
        }
    )

    print("\n============================================================")
    print("TEST 4 - HUMAN REVIEW")
    print("============================================================")
    print(result)

    assert result["decision"] == "HUMAN_REVIEW"
    assert result["executed"] is False

    print(
        f"PASS: claim {claim_id} requires human review."
    )

if __name__ == "__main__":
    test_allowed_assigned_claim()
    test_blocked_unassigned_claim()
    test_blocked_tool()
    test_human_review_tool()