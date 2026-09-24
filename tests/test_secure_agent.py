"""
Stage E.1
Secure Agent -> Hybrid Gateway -> Tool Execution Tests
"""

from src.secure_agent import execute_agent_action

from src.database import SessionLocal
from src.models import (
    Claim,
    User,
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
                f"No active claim assignment "
                f"for user {user_id}."
            )

        return assignment.claim_id

    finally:
        db.close()


def prepare_officer_claim():
    """
    Prepare a repeatable high-risk settlement fixture.

    The original claim status is returned so the test
    can restore the database afterwards.
    """

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
                "No CLAIMS_OFFICER exists."
            )

        assignment = (
            db.query(ClaimAssignment)
            .filter(
                ClaimAssignment.user_id
                == officer.user_id,
                ClaimAssignment.active.is_(True),
            )
            .first()
        )

        if assignment is None:
            raise AssertionError(
                "No active claim assignment exists "
                "for the claims officer."
            )

        claim = (
            db.query(Claim)
            .filter(
                Claim.claim_id
                == assignment.claim_id
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
    db = SessionLocal()

    try:
        claim = (
            db.query(Claim)
            .filter(
                Claim.claim_id == claim_id
            )
            .first()
        )

        if claim is not None:
            claim.status = original_status
            db.commit()

    finally:
        db.close()


# ============================================================
# TEST 1
# ============================================================

def test_normal_agent_request():
    print()
    print("=" * 60)
    print("E.1 TEST 1 - NORMAL AGENT REQUEST")
    print("=" * 60)

    user_id = get_user_id_by_role(
        "CLAIMS_ASSISTANT"
    )

    claim_id = get_assigned_claim_id(
        user_id
    )

    result = execute_agent_action(
        agent_id="claims-agent-01",
        user_id=user_id,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": claim_id,
        },
    )

    print()
    print(result)

    assert result["success"] is True
    assert result["executed"] is True
    assert result["decision"] == "ALLOW"

    print(
        "PASS: normal agent request executed."
    )


# ============================================================
# TEST 2
# ============================================================

def test_prompt_injection_blocked():
    print()
    print("=" * 60)
    print("E.1 TEST 2 - PROMPT INJECTION")
    print("=" * 60)

    user_id = get_user_id_by_role(
        "CLAIMS_ASSISTANT"
    )

    claim_id = get_assigned_claim_id(
        user_id
    )

    result = execute_agent_action(
        agent_id="claims-agent-01",
        user_id=user_id,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": claim_id,
        },
        sensitive_document=True,
        prompt_injection_signal=True,
    )

    print()
    print(result)

    assert result["success"] is False
    assert result["executed"] is False
    assert result["decision"] == "BLOCK"

    print(
        "PASS: ML security prevented "
        "agent execution."
    )


# ============================================================
# TEST 3
# ============================================================

def test_unassigned_resource_blocked():
    print()
    print("=" * 60)
    print("E.1 TEST 3 - UNASSIGNED RESOURCE")
    print("=" * 60)

    result = execute_agent_action(
        agent_id="claims-agent-01",
        user_id=999,
        user_role="CLAIMS_ASSISTANT",
        tool_name="get_claim",
        arguments={
            "claim_id": 50,
        },
    )

    print()
    print(result)

    assert result["success"] is False
    assert result["executed"] is False
    assert result["decision"] == "BLOCK"

    print(
        "PASS: deterministic resource "
        "authorization blocked agent."
    )


# ============================================================
# TEST 4
# ============================================================

def test_unknown_tool_blocked():
    print()
    print("=" * 60)
    print("E.1 TEST 4 - UNKNOWN TOOL")
    print("=" * 60)

    result = execute_agent_action(
        agent_id="claims-agent-01",
        user_id=3,
        user_role="CLAIMS_ASSISTANT",
        tool_name="evil_unknown_tool",
        arguments={},
    )

    print()
    print(result)

    assert result["success"] is False
    assert result["executed"] is False
    assert result["decision"] == "BLOCK"

    print(
        "PASS: unknown tool blocked."
    )


# ============================================================
# TEST 5
# ============================================================

def test_high_risk_action_requires_human():
    print()
    print("=" * 60)
    print("E.1 TEST 5 - HIGH-RISK AGENT ACTION")
    print("=" * 60)

    (
        officer_id,
        claim_id,
        original_status,
    ) = prepare_officer_claim()

    print(f"Officer: {officer_id}")
    print(f"Claim:   {claim_id}")

    try:
        result = execute_agent_action(
            agent_id="claims-agent-01",
            user_id=officer_id,
            user_role="CLAIMS_OFFICER",
            tool_name="approve_settlement",
            arguments={
                "claim_id": claim_id,
            },
        )

        print()
        print(result)

        assert result["success"] is False
        assert result["executed"] is False

        assert (
            result["decision"]
            == "HUMAN_REVIEW"
        )

        assert (
            result["requires_human_approval"]
            is True
        )

        assert result.get("approval_id")

        # ----------------------------------------------------
        # Critical security assertion:
        # requesting human approval must NOT execute
        # the settlement.
        # ----------------------------------------------------

        db = SessionLocal()

        try:
            claim = (
                db.query(Claim)
                .filter(
                    Claim.claim_id == claim_id
                )
                .first()
            )

            assert claim is not None

            assert (
                claim.status
                == "SETTLEMENT_REVIEW"
            )

        finally:
            db.close()

        print(
            "PASS: high-risk agent action "
            "stopped before execution and "
            "created approval."
        )

    finally:
        restore_claim_status(
            claim_id,
            original_status,
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    test_normal_agent_request()
    test_prompt_injection_blocked()
    test_unassigned_resource_blocked()
    test_unknown_tool_blocked()
    test_high_risk_action_requires_human()

    print()
    print("=" * 60)
    print(
        "ALL STAGE E.1 SECURE AGENT "
        "TESTS PASSED"
    )
    print("=" * 60)