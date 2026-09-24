from src.database import SessionLocal
from src.models import Claim, User
from src.security_gateway import (
    SecurityRequest,
    evaluate_request,
    Decision,
)


def find_assigned_officer_claim():
    """
    Find a claim assigned to a claims officer.

    We do not hard-code a claim ID because the seed data
    can contain different claim states.
    """

    db = SessionLocal()

    try:
        officer = db.query(User).filter(
            User.role == "CLAIMS_OFFICER"
        ).first()

        if officer is None:
            raise RuntimeError(
                "No CLAIMS_OFFICER exists in the database."
            )

        from src.models import ClaimAssignment

        assignment = db.query(ClaimAssignment).filter(
            ClaimAssignment.user_id == officer.user_id,
            ClaimAssignment.active == True
        ).first()

        if assignment is None:
            raise RuntimeError(
                "No active claim assignment found for officer."
            )

        claim = db.query(Claim).filter(
            Claim.claim_id == assignment.claim_id
        ).first()

        return officer, claim

    finally:
        db.close()


def test_unassigned_settlement_request_is_blocked():

    officer, claim = find_assigned_officer_claim()

    # Pick a claim that is NOT assigned to this officer.
    db = SessionLocal()

    try:
        from src.models import ClaimAssignment

        assigned_claim_ids = {
            row.claim_id
            for row in db.query(ClaimAssignment).filter(
                ClaimAssignment.user_id == officer.user_id,
                ClaimAssignment.active == True
            ).all()
        }

        unassigned_claim = db.query(Claim).filter(
            ~Claim.claim_id.in_(assigned_claim_ids)
        ).first()

    finally:
        db.close()

    if unassigned_claim is None:
        print(
            "SKIP: no unassigned claim available "
            "for this officer."
        )
        return

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=officer.user_id,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": unassigned_claim.claim_id
        },
        reason="Testing resource authorization."
    )

    decision = evaluate_request(request)

    assert decision.decision == Decision.BLOCK

    print(
        "PASS: unassigned settlement request blocked."
    )


def test_settlement_requires_valid_claim_state():

    officer, claim = find_assigned_officer_claim()

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=officer.user_id,
        user_role="CLAIMS_OFFICER",
        tool_name="approve_settlement",
        arguments={
            "claim_id": claim.claim_id
        },
        reason="Testing settlement business-state validation."
    )

    decision = evaluate_request(request)

    if claim.status == "SETTLEMENT_REVIEW":
        assert decision.decision == Decision.HUMAN_REVIEW

        print(
            f"PASS: claim {claim.claim_id} is eligible "
            "and requires human review."
        )

    else:
        assert decision.decision == Decision.BLOCK

        print(
            f"PASS: claim {claim.claim_id} is in "
            f"'{claim.status}' and settlement was blocked."
        )