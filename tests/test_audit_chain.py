import json
import os

from src.audit import (
    AUDIT_FILE,
    log_security_event,
    verify_audit_log,
)


def test_audit_hash_chain_continuity():
    print()
    print("=" * 60)
    print("TEST 13 - AUDIT HASH-CHAIN CONTINUITY")
    print("=" * 60)

    os.makedirs("data", exist_ok=True)

    # --------------------------------------------------------
    # Preserve the real audit log before destructive testing.
    # --------------------------------------------------------

    original_audit_data = None

    if os.path.exists(AUDIT_FILE):
        with open(
            AUDIT_FILE,
            "rb",
        ) as file:
            original_audit_data = file.read()

    try:
        # Start the test with an isolated clean audit log.
        if os.path.exists(AUDIT_FILE):
            os.remove(AUDIT_FILE)

        # ----------------------------------------------------
        # Create first audit event.
        # ----------------------------------------------------

        first_event = log_security_event(
            agent_id="claims-agent-01",
            user_id=3,
            user_role="CLAIMS_ASSISTANT",
            tool_name="get_claim",
            arguments={
                "claim_id": 1
            },
            decision="ALLOW",
            risk_level="LOW",
            reason=(
                "Tool and resource are permitted "
                "for this user."
            ),
            executed=True,
        )

        # ----------------------------------------------------
        # Create second audit event.
        # ----------------------------------------------------

        second_event = log_security_event(
            agent_id="claims-agent-01",
            user_id=3,
            user_role="CLAIMS_ASSISTANT",
            tool_name="get_claim_documents",
            arguments={
                "claim_id": 1
            },
            decision="ALLOW",
            risk_level="LOW",
            reason=(
                "Tool and resource are permitted "
                "for this user."
            ),
            executed=True,
        )

        print()
        print("First event:")
        print(first_event)

        print()
        print("Second event:")
        print(second_event)

        # ----------------------------------------------------
        # Verify normal hash-chain relationship.
        # ----------------------------------------------------

        assert second_event["previous_hash"] == (
            first_event["integrity_hash"]
        )

        verification_before = verify_audit_log()

        print()
        print("Verification before chain tampering:")
        print(verification_before)

        assert verification_before["success"] is True
        assert verification_before["valid"] is True
        assert verification_before["event_count"] == 2

        # ----------------------------------------------------
        # Load test audit events.
        # ----------------------------------------------------

        with open(
            AUDIT_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            events = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        # ----------------------------------------------------
        # Simulate hash-chain tampering.
        # ----------------------------------------------------

        events[1]["previous_hash"] = (
            "ATTACKER_MODIFIED_HASH"
        )

        print()
        print("Tampered second event:")
        print(events[1])

        with open(
            AUDIT_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            for event in events:
                file.write(
                    json.dumps(event) + "\n"
                )

        # ----------------------------------------------------
        # Tampering must now be detected.
        # ----------------------------------------------------

        verification_after = verify_audit_log()

        print()
        print("Verification after chain tampering:")
        print(verification_after)

        assert verification_after["success"] is True
        assert verification_after["valid"] is False

        print()
        print("=" * 60)
        print("AUDIT HASH-CHAIN CONTINUITY PASSED")
        print("=" * 60)

    finally:
        # ----------------------------------------------------
        # Always restore the real audit log.
        # ----------------------------------------------------

        if original_audit_data is None:
            if os.path.exists(AUDIT_FILE):
                os.remove(AUDIT_FILE)
        else:
            with open(
                AUDIT_FILE,
                "wb",
            ) as file:
                file.write(original_audit_data)


if __name__ == "__main__":
    test_audit_hash_chain_continuity()