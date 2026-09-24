from src.approval import (
    create_approval_request,
    approve_request,
    execute_approved_request,
    get_approval,
)

from src.database import SessionLocal

from src.models import (
    User,
    Claim,
    ClaimAssignment,
)


def prepare_eligible_claim():
    """
    Prepare an actively assigned claims-officer claim
    for settlement approval testing.

    The original status is returned so the database
    can always be restored after the test.
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
                "No CLAIMS_OFFICER found "
                "in database."
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
                "No active claim assignment "
                "exists for the CLAIMS_OFFICER."
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
    """
    Restore database state even if the test fails.
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

        if claim is not None:
            claim.status = original_status
            db.commit()

    finally:
        db.close()


def get_claim_status(claim_id):
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


def test_approval_replay_protection():
    print()
    print("=" * 60)
    print("TEST 5 - APPROVAL REPLAY PROTECTION")
    print("=" * 60)

    (
        user_id,
        claim_id,
        original_status,
    ) = prepare_eligible_claim()

    print()
    print(f"Selected officer: {user_id}")
    print(f"Selected claim:   {claim_id}")
    print(f"Original status:  {original_status}")

    try:
        # -----------------------------------------------------
        # Create approval request
        # -----------------------------------------------------

        approval = create_approval_request(
            agent_id="claims-agent-01",
            user_id=user_id,
            user_role="CLAIMS_OFFICER",
            tool_name="approve_settlement",
            arguments={
                "claim_id": claim_id,
            },
            reason=(
                "Test approval replay protection."
            ),
        )

        approval_id = approval["approval_id"]

        print()
        print("Created approval:")
        print(approval)

        assert approval["status"] == "PENDING"

        # -----------------------------------------------------
        # Human approves request
        # -----------------------------------------------------

        approved = approve_request(
            approval_id
        )

        print()
        print("Approved:")
        print(approved)

        assert approved["success"] is True
        assert approved["status"] == "APPROVED"

        # -----------------------------------------------------
        # First execution
        # -----------------------------------------------------

        first_execution = (
            execute_approved_request(
                approval_id
            )
        )

        print()
        print("First execution:")
        print(first_execution)

        assert (
            first_execution["success"]
            is True
        )

        assert (
            first_execution["status"]
            == "EXECUTED"
        )

        # Verify the protected operation actually happened.

        status_after_execution = (
            get_claim_status(claim_id)
        )

        print()
        print(
            "Claim status after execution:",
            status_after_execution,
        )

        assert (
            status_after_execution
            == "SETTLEMENT_APPROVED"
        )

        # -----------------------------------------------------
        # Replay attempt
        # -----------------------------------------------------

        second_execution = (
            execute_approved_request(
                approval_id
            )
        )

        print()
        print("Replay attempt:")
        print(second_execution)

        assert (
            second_execution["success"]
            is False
        )

        # -----------------------------------------------------
        # Verify approval remains EXECUTED
        # -----------------------------------------------------

        final_approval = get_approval(
            approval_id
        )

        print()
        print("Final approval record:")
        print(final_approval)

        assert (
            final_approval["status"]
            == "EXECUTED"
        )

        print()
        print("=" * 60)
        print(
            "APPROVAL REPLAY "
            "PROTECTION PASSED"
        )
        print("=" * 60)

    finally:
        # -----------------------------------------------------
        # TEST ISOLATION
        #
        # Whatever happens above, return the database to
        # exactly the claim status it had before this test.
        # -----------------------------------------------------

        restore_claim_status(
            claim_id,
            original_status,
        )

        restored_status = (
            get_claim_status(claim_id)
        )

        print()
        print(
            "Restored claim status:",
            restored_status,
        )

        assert (
            restored_status
            == original_status
        )
if __name__ == "__main__":
    test_approval_replay_protection()