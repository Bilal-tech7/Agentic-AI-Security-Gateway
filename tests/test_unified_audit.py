import json
import os

from src.audit import (
    AUDIT_FILE,
    verify_audit_log,
)

from src.secure_agent import execute_agent_action

from src.approval import (
    approve_request,
    execute_approved_request,
)

from src.database import SessionLocal

from src.models import (
    Claim,
    User,
    ClaimAssignment,
)


def read_audit_events():
    if not os.path.exists(AUDIT_FILE):
        return []

    with open(
        AUDIT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def find_settlement_review_claim():
    db = SessionLocal()

    try:
        officer = (
            db.query(User)
            .filter(
                User.role == "CLAIMS_OFFICER"
            )
            .first()
        )

        if officer is None:
            raise AssertionError(
                "No CLAIMS_OFFICER found."
            )

        assignment = (
            db.query(ClaimAssignment)
            .join(
                Claim,
                Claim.claim_id
                == ClaimAssignment.claim_id,
            )
            .filter(
                ClaimAssignment.user_id
                == officer.user_id,

                ClaimAssignment.active.is_(True),

                Claim.status
                == "SETTLEMENT_REVIEW",
            )
            .first()
        )

        if assignment is None:
            raise AssertionError(
                "No eligible SETTLEMENT_REVIEW "
                "claim found."
            )

        return (
            officer.user_id,
            assignment.claim_id,
        )

    finally:
        db.close()


def test_unified_agent_audit():

    print()
    print("=" * 70)
    print("STAGE E.3 - UNIFIED SECURITY AUDIT")
    print("=" * 70)

    # Start with clean audit log.
    if os.path.exists(AUDIT_FILE):
        os.remove(AUDIT_FILE)

    # ========================================================
    # TEST 1 - ALLOW
    # ========================================================

    print()
    print("-" * 70)
    print("TEST 1 - AUDIT ALLOWED AGENT ACTION")
    print("-" * 70)

    allowed = execute_agent_action(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 1,
        },
    )

    print(allowed)

    assert allowed["decision"] == "ALLOW"
    assert allowed["executed"] is True

    # ========================================================
    # TEST 2 - BLOCK
    # ========================================================

    print()
    print("-" * 70)
    print("TEST 2 - AUDIT BLOCKED AGENT ACTION")
    print("-" * 70)

    blocked = execute_agent_action(
        agent_id="claims-agent-01",
        user_id=2,
        user_role="CLAIMS_ASSISTANT",
        tool_name="delete_claim",
        arguments={
            "claim_id": 1,
        },
    )

    print(blocked)

    assert blocked["decision"] == "BLOCK"
    assert blocked["executed"] is False

    # ========================================================
    # TEST 3 - HUMAN REVIEW
    # ========================================================

    officer_id, claim_id = (
        find_settlement_review_claim()
    )

    print()
    print("-" * 70)
    print("TEST 3 - AUDIT HUMAN REVIEW")
    print("-" * 70)

    review = execute_agent_action(
        agent_id="claims-agent-01",
        user_id=officer_id,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": claim_id,
        },
    )

    print(review)

    assert review["decision"] == "HUMAN_REVIEW"
    assert review["executed"] is False
    assert review["approval_id"]

    approval_id = review["approval_id"]

    # ========================================================
    # TEST 4 - APPROVED EXECUTION
    # ========================================================

    print()
    print("-" * 70)
    print("TEST 4 - AUDIT APPROVED EXECUTION")
    print("-" * 70)

    approved = approve_request(
        approval_id
    )

    assert approved["success"] is True

    execution = execute_approved_request(
        approval_id
    )

    print(execution)

    assert execution["success"] is True
    assert execution["status"] == "EXECUTED"

    # ========================================================
    # VERIFY EVENTS
    # ========================================================

    events = read_audit_events()

    print()
    print("-" * 70)
    print("AUDIT EVENTS")
    print("-" * 70)

    for event in events:
        print()
        print(
            event["event_type"],
            "|",
            event["decision"],
            "|",
            event["tool_name"],
            "| executed =",
            event["executed"],
        )

    assert len(events) == 4

    assert events[0]["event_type"] == (
        "AGENT_SECURITY_DECISION"
    )
    assert events[0]["decision"] == "ALLOW"
    assert events[0]["executed"] is True

    assert events[1]["event_type"] == (
        "AGENT_SECURITY_DECISION"
    )
    assert events[1]["decision"] == "BLOCK"
    assert events[1]["executed"] is False

    assert events[2]["event_type"] == (
        "AGENT_SECURITY_DECISION"
    )
    assert events[2]["decision"] == "HUMAN_REVIEW"
    assert events[2]["executed"] is False
    assert events[2]["approval_id"] == approval_id

    assert events[3]["event_type"] == (
        "APPROVED_EXECUTION"
    )
    assert events[3]["decision"] == "ALLOW"
    assert events[3]["executed"] is True
    assert events[3]["approval_id"] == approval_id

    # ========================================================
    # VERIFY HASH CHAIN
    # ========================================================

    print()
    print("-" * 70)
    print("VERIFYING TAMPER-EVIDENT HASH CHAIN")
    print("-" * 70)

    verification = verify_audit_log()

    print(verification)

    assert verification["success"] is True
    assert verification["valid"] is True
    assert verification["event_count"] == 4

    print()
    print("=" * 70)
    print("UNIFIED SECURITY AUDIT PASSED")
    print("=" * 70)


if __name__ == "__main__":
    test_unified_agent_audit()