from src.security_gateway import (
    SecurityRequest,
    evaluate_request,
)

from src.database import SessionLocal
from src.models import (
    User,
    Claim,
    ClaimAssignment,
)


def get_user_id_by_role(role):
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.role == role)
            .first()
        )

        if user is None:
            raise AssertionError(
                f"No user found for role '{role}'."
            )

        return user.user_id

    finally:
        db.close()


def get_assigned_claim_id(user_id):
    db = SessionLocal()

    try:
        assignment = (
            db.query(ClaimAssignment)
            .filter(
                ClaimAssignment.user_id == user_id,
                ClaimAssignment.active.is_(True),
            )
            .first()
        )

        if assignment is None:
            raise AssertionError(
                f"No active claim assignment found "
                f"for user {user_id}."
            )

        return assignment.claim_id

    finally:
        db.close()


def prepare_officer_claim():
    """
    Select an actively assigned claim for a claims officer
    and temporarily place it into SETTLEMENT_REVIEW.

    Returns:
        officer_id
        claim_id
        original_status
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
                "No CLAIMS_OFFICER found."
            )

        assignment = (
            db.query(ClaimAssignment)
            .filter(
                ClaimAssignment.user_id == officer.user_id,
                ClaimAssignment.active.is_(True),
            )
            .first()
        )

        if assignment is None:
            raise AssertionError(
                "No active claim assignment found "
                "for the CLAIMS_OFFICER."
            )

        claim = (
            db.query(Claim)
            .filter(
                Claim.claim_id == assignment.claim_id
            )
            .first()
        )

        if claim is None:
            raise AssertionError(
                "Assigned claim does not exist."
            )

        original_status = claim.status

        claim.status = "SETTLEMENT_REVIEW"

        db.commit()

        return (
            officer.user_id,
            claim.claim_id,
            original_status,
        )

    finally:
        db.close()


def restore_claim_status(
    claim_id,
    original_status,
):
    """
    Restore the claim to the state it had before the test.
    """

    db = SessionLocal()

    try:
        claim = (
            db.query(Claim)
            .filter(Claim.claim_id == claim_id)
            .first()
        )

        if claim is not None:
            claim.status = original_status
            db.commit()

    finally:
        db.close()


def test_allowed_claim_access():
    print("=" * 60)
    print("TEST 1 - LEGITIMATE CLAIM ACCESS")
    print("=" * 60)

    user_id = get_user_id_by_role(
        "CLAIMS_ASSISTANT"
    )

    claim_id = get_assigned_claim_id(
        user_id
    )

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=user_id,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": claim_id,
        },
    )

    decision = evaluate_request(request)

    print(decision)

    assert decision.decision.value == "ALLOW"
    assert decision.risk_level.value == "LOW"

    print(
        "PASS: legitimate assigned claim access allowed."
    )


def test_blocked_tool():
    print("=" * 60)
    print("TEST 2 - UNAUTHORIZED TOOL")
    print("=" * 60)

    user_id = get_user_id_by_role(
        "CLAIMS_ASSISTANT"
    )

    claim_id = get_assigned_claim_id(
        user_id
    )

    request = SecurityRequest(
        agent_id="claims-agent-01",
        user_id=user_id,
        user_role="CLAIMS_ASSISTANT",
        tool_name="delete_claim",
        arguments={
            "claim_id": claim_id,
        },
    )

    decision = evaluate_request(request)

    print(decision)

    assert decision.decision.value == "BLOCK"
    assert decision.risk_level.value == "HIGH"

    print(
        "PASS: unauthorized tool blocked."
    )


def test_human_review():
    print("=" * 60)
    print("TEST 3 - HIGH-RISK ACTION")
    print("=" * 60)

    (
        user_id,
        claim_id,
        original_status,
    ) = prepare_officer_claim()

    try:
        request = SecurityRequest(
            agent_id="claims-agent-01",
            user_id=user_id,
            user_role="CLAIMS_OFFICER",
            tool_name="approve_settlement",
            arguments={
                "claim_id": claim_id,
            },
        )

        decision = evaluate_request(request)

        print(decision)

        assert (
            decision.decision.value
            == "HUMAN_REVIEW"
        )

        assert (
            decision.risk_level.value
            == "CRITICAL"
        )

        print(
            f"PASS: claim {claim_id} "
            "requires human review."
        )

    finally:
        restore_claim_status(
            claim_id,
            original_status,
        )


if __name__ == "__main__":
    test_allowed_claim_access()
    test_blocked_tool()
    test_human_review()