"""
Stage E.2
Complete End-to-End Secure Agent Workflow

Tests:

Agent
  -> Secure Agent
  -> Hybrid Gateway
  -> Human Review
  -> Approval
  -> Approved Execution
  -> Replay Protection
  -> Database State Verification
"""

from src.secure_agent import execute_agent_action
from src.approval import (
    approve_request,
    execute_approved_request,
    get_approval,
)
from src.database import SessionLocal
from src.models import Claim, User, ClaimAssignment


def find_eligible_settlement_claim():
    """
    Dynamically find a CLAIMS_OFFICER with an actively assigned
    claim currently in SETTLEMENT_REVIEW.
    """

    db = SessionLocal()

    try:
        officer = (
            db.query(User)
            .filter(User.role == "CLAIMS_OFFICER")
            .first()
        )

        if officer is None:
            raise AssertionError(
                "No CLAIMS_OFFICER exists in the database."
            )

        assignment = (
            db.query(ClaimAssignment)
            .join(
                Claim,
                Claim.claim_id == ClaimAssignment.claim_id,
            )
            .filter(
                ClaimAssignment.user_id == officer.user_id,
                ClaimAssignment.active.is_(True),
                Claim.status == "SETTLEMENT_REVIEW",
            )
            .first()
        )

        if assignment is None:
            raise AssertionError(
                "No SETTLEMENT_REVIEW claim is currently "
                "assigned to the claims officer."
            )

        return officer.user_id, assignment.claim_id

    finally:
        db.close()


def get_claim_status(claim_id):
    """
    Read the current claim status directly from the database.
    """

    db = SessionLocal()

    try:
        claim = (
            db.query(Claim)
            .filter(Claim.claim_id == claim_id)
            .first()
        )

        if claim is None:
            raise AssertionError(
                f"Claim {claim_id} does not exist."
            )

        return claim.status

    finally:
        db.close()


def test_complete_secure_workflow():

    print()
    print("=" * 70)
    print("STAGE E.2 - COMPLETE END-TO-END SECURE WORKFLOW")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Find eligible high-risk resource
    # --------------------------------------------------------

    officer_id, claim_id = find_eligible_settlement_claim()

    print()
    print(f"Selected officer: {officer_id}")
    print(f"Selected claim:   {claim_id}")

    initial_status = get_claim_status(claim_id)

    print(f"Initial status:   {initial_status}")

    assert initial_status == "SETTLEMENT_REVIEW"

    # --------------------------------------------------------
    # 2. Agent requests high-risk action
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("STEP 1 - AGENT REQUESTS SETTLEMENT APPROVAL")
    print("-" * 70)

    agent_result = execute_agent_action(
        agent_id="claims-agent-01",
        user_id=officer_id,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": claim_id,
        },
    )

    print()
    print("Agent result:")
    print(agent_result)

    assert agent_result["success"] is False
    assert agent_result["executed"] is False
    assert agent_result["decision"] == "HUMAN_REVIEW"
    assert agent_result["requires_human_approval"] is True
    assert agent_result.get("approval_id")

    approval_id = agent_result["approval_id"]

    # --------------------------------------------------------
    # 3. Verify tool was NOT executed before approval
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("STEP 2 - VERIFY NO PREMATURE EXECUTION")
    print("-" * 70)

    status_before_approval = get_claim_status(claim_id)

    print(
        "Claim status before human approval:",
        status_before_approval,
    )

    assert status_before_approval == "SETTLEMENT_REVIEW"

    print(
        "PASS: gateway stopped the high-risk action "
        "before execution."
    )

    # --------------------------------------------------------
    # 4. Human approves request
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("STEP 3 - HUMAN APPROVES REQUEST")
    print("-" * 70)

    approval_result = approve_request(
        approval_id
    )

    print()
    print("Approval result:")
    print(approval_result)

    assert approval_result["success"] is True
    assert approval_result["status"] == "APPROVED"

    stored_approval = get_approval(
        approval_id
    )

    assert stored_approval is not None
    assert stored_approval["status"] == "APPROVED"

    # --------------------------------------------------------
    # 5. Execute approved request
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("STEP 4 - EXECUTE HUMAN-APPROVED ACTION")
    print("-" * 70)

    execution_result = execute_approved_request(
        approval_id
    )

    print()
    print("Execution result:")
    print(execution_result)

    assert execution_result["success"] is True
    assert execution_result["status"] == "EXECUTED"
    assert execution_result["tool_name"] == "approve_settlement"

    # --------------------------------------------------------
    # 6. Verify database changed
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("STEP 5 - VERIFY DATABASE STATE")
    print("-" * 70)

    final_claim_status = get_claim_status(
        claim_id
    )

    print(
        "Claim status after approved execution:",
        final_claim_status,
    )

    assert final_claim_status == "SETTLEMENT_APPROVED"

    print(
        "PASS: protected tool executed only after "
        "human approval."
    )

    # --------------------------------------------------------
    # 7. Verify approval state
    # --------------------------------------------------------

    final_approval = get_approval(
        approval_id
    )

    print()
    print("Final approval:")
    print(final_approval)

    assert final_approval is not None
    assert final_approval["status"] == "EXECUTED"

    # --------------------------------------------------------
    # 8. Replay attack
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("STEP 6 - ATTEMPT APPROVAL REPLAY")
    print("-" * 70)

    replay_result = execute_approved_request(
        approval_id
    )

    print()
    print("Replay result:")
    print(replay_result)

    assert replay_result["success"] is False
    assert replay_result["status"] == "EXECUTED"

    # Database must remain correctly approved.
    replay_claim_status = get_claim_status(
        claim_id
    )

    assert replay_claim_status == "SETTLEMENT_APPROVED"

    print(
        "PASS: executed approval cannot be replayed."
    )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("END-TO-END SECURE WORKFLOW PASSED")
    print("=" * 70)

    print()
    print("Verified architecture:")
    print()
    print("Agent")
    print("  |")
    print("  v")
    print("Secure Agent")
    print("  |")
    print("  v")
    print("Hybrid Security Gateway")
    print("  |")
    print("  +--> Deterministic Authorization")
    print("  |")
    print("  +--> ML Risk Analysis")
    print("  |")
    print("  v")
    print("HUMAN_REVIEW")
    print("  |")
    print("  v")
    print("Human Approval")
    print("  |")
    print("  v")
    print("Gateway Re-Authorization")
    print("  |")
    print("  v")
    print("Protected Tool Execution")
    print("  |")
    print("  v")
    print("Replay Protection")


if __name__ == "__main__":
    test_complete_secure_workflow()