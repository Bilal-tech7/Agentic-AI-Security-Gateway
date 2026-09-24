"""
=======================================================================
AURELIA
Secure Agentic AI Gateway - Final Demonstration
=======================================================================

Demonstrates:

1. Legitimate agent access
2. Resource authorization enforcement
3. Prompt-injection / ML risk protection
4. Human-in-the-loop approval
5. Approved high-risk execution
6. Approval replay protection
7. Tamper-evident audit verification

Security principle:

    The LLM proposes actions.
    The security gateway authorizes actions.
    Protected tools execute only after authorization.
"""

from src.secure_agent import execute_agent_action

from src.approval import (
    approve_request,
    execute_approved_request,
)

from src.audit import verify_audit_log

from src.database import SessionLocal

from src.models import (
    Claim,
    ClaimAssignment,
    User,
)


AGENT_ID = "claims-agent-01"


# =====================================================================
# DISPLAY HELPERS
# =====================================================================

def banner(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def scenario(title):
    print()
    print("-" * 72)
    print(title)
    print("-" * 72)


# =====================================================================
# DATABASE HELPERS
# =====================================================================

def find_claims_officer():
    """
    Find a claims officer in the database.
    """

    db = SessionLocal()

    try:
        return (
            db.query(User)
            .filter(
                User.role == "CLAIMS_OFFICER"
            )
            .first()
        )

    finally:
        db.close()


def find_settlement_review_claim(user_id):
    """
    Find an assigned claim that is currently eligible
    for settlement approval.
    """

    db = SessionLocal()

    try:
        assignment = (
            db.query(ClaimAssignment)
            .join(
                Claim,
                Claim.claim_id
                == ClaimAssignment.claim_id,
            )
            .filter(
                ClaimAssignment.user_id == user_id,
                ClaimAssignment.active.is_(True),
                Claim.status == "SETTLEMENT_REVIEW",
            )
            .first()
        )

        if assignment is None:
            return None

        return assignment.claim_id

    finally:
        db.close()


def get_claim_status(claim_id):
    """
    Return the current status of a claim.
    """

    db = SessionLocal()

    try:
        claim = (
            db.query(Claim)
            .filter(
                Claim.claim_id == claim_id
            )
            .first()
        )

        if claim is None:
            return None

        return claim.status

    finally:
        db.close()


# =====================================================================
# FINAL DEMONSTRATION
# =====================================================================

def main():

    banner(
        "AURELIA - SECURE AGENTIC AI GATEWAY"
    )

    print()
    print(
        "Security model:"
    )
    print(
        "LLM proposes -> Gateway authorizes -> "
        "Protected tool executes"
    )

    # =================================================================
    # SCENARIO 1
    # =================================================================

    scenario(
        "SCENARIO 1 - LEGITIMATE AUTHORIZED ACCESS"
    )

    result = execute_agent_action(
        agent_id=AGENT_ID,
        user_id=3,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 1
        },
    )

    print()
    print("Result:")
    print(result)

    assert result["decision"] == "ALLOW"
    assert result["executed"] is True

    print()
    print(
        "PASS: authorized request executed."
    )

    # =================================================================
    # SCENARIO 2
    # =================================================================

    scenario(
        "SCENARIO 2 - UNAUTHORIZED RESOURCE ACCESS"
    )

    result = execute_agent_action(
        agent_id=AGENT_ID,
        user_id=999,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 50
        },
    )

    print()
    print("Result:")
    print(result)

    assert result["decision"] == "BLOCK"
    assert result["executed"] is False

    print()
    print(
        "PASS: unauthorized resource access blocked."
    )

    # =================================================================
    # SCENARIO 3
    # =================================================================

    scenario(
        "SCENARIO 3 - PROMPT-INJECTION / ML RISK"
    )

    result = execute_agent_action(
        agent_id=AGENT_ID,
        user_id=3,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 1
        },
        sensitive_document=True,
        prompt_injection_signal=True,
    )

    print()
    print("Result:")
    print(result)

    assert result["decision"] == "BLOCK"
    assert result["executed"] is False
    assert result["ml_escalated"] is True

    print()
    print(
        "PASS: ML-assisted hybrid enforcement "
        "blocked the risky action."
    )

    # =================================================================
    # SCENARIO 4
    # =================================================================

    scenario(
        "SCENARIO 4 - HIGH-RISK HUMAN APPROVAL"
    )

    officer = find_claims_officer()

    if officer is None:
        raise RuntimeError(
            "No CLAIMS_OFFICER exists in database."
        )

    claim_id = find_settlement_review_claim(
        officer.user_id
    )

    if claim_id is None:
        raise RuntimeError(
            "No assigned SETTLEMENT_REVIEW claim "
            "is available for the final demo."
        )

    print()
    print(f"Claims officer: {officer.user_id}")
    print(f"Selected claim: {claim_id}")
    print(
        "Initial status: "
        f"{get_claim_status(claim_id)}"
    )

    result = execute_agent_action(
        agent_id=AGENT_ID,
        user_id=officer.user_id,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": claim_id
        },
    )

    print()
    print("Gateway result:")
    print(result)

    assert result["decision"] == "HUMAN_REVIEW"
    assert result["executed"] is False

    approval_id = result["approval_id"]

    print()
    print(
        "PASS: high-risk action stopped before "
        "execution."
    )

    # =================================================================
    # SCENARIO 5
    # =================================================================

    scenario(
        "SCENARIO 5 - HUMAN APPROVAL AND EXECUTION"
    )

    approval = approve_request(
        approval_id
    )

    print()
    print("Human approval:")
    print(approval)

    assert approval["success"] is True
    assert approval["status"] == "APPROVED"

    execution = execute_approved_request(
        approval_id
    )

    print()
    print("Approved execution:")
    print(execution)

    assert execution["success"] is True
    assert execution["status"] == "EXECUTED"

    final_status = get_claim_status(
        claim_id
    )

    print()
    print(
        f"Claim status after execution: "
        f"{final_status}"
    )

    assert final_status == (
        "SETTLEMENT_APPROVED"
    )

    print()
    print(
        "PASS: protected action executed only "
        "after human approval."
    )

    # =================================================================
    # SCENARIO 6
    # =================================================================

    scenario(
        "SCENARIO 6 - APPROVAL REPLAY ATTACK"
    )

    replay = execute_approved_request(
        approval_id
    )

    print()
    print("Replay result:")
    print(replay)

    assert replay["success"] is False
    assert replay["status"] == "EXECUTED"

    print()
    print(
        "PASS: approval replay attack prevented."
    )

    # =================================================================
    # SCENARIO 7
    # =================================================================

    scenario(
        "SCENARIO 7 - AUDIT LOG INTEGRITY"
    )

    audit = verify_audit_log()

    print()
    print("Audit verification:")
    print(audit)

    assert audit["success"] is True
    assert audit["valid"] is True

    print()
    print(
        "PASS: tamper-evident audit chain is valid."
    )

    # =================================================================
    # COMPLETE
    # =================================================================

    banner(
        "AURELIA FINAL SECURITY DEMONSTRATION PASSED"
    )

    print()
    print("Demonstrated controls:")
    print("  [PASS] Role-based authorization")
    print("  [PASS] Resource-level authorization")
    print("  [PASS] Deterministic security rules")
    print("  [PASS] ML-assisted risk detection")
    print("  [PASS] Prompt-injection risk enforcement")
    print("  [PASS] Human-in-the-loop approval")
    print("  [PASS] Gateway re-authorization")
    print("  [PASS] Approval integrity protection")
    print("  [PASS] Replay protection")
    print("  [PASS] Tamper-evident audit logging")

    print()
    print(
        "Core principle:"
    )
    print(
        "  The AI agent proposes actions; "
        "the security gateway controls execution."
    )

    print()


if __name__ == "__main__":
    main()