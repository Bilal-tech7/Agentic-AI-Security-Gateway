from datetime import datetime
import hashlib
import json
import os
import uuid


AUDIT_FILE = "data/security_audit.jsonl"


def _calculate_integrity_hash(event):
    """
    Calculate a SHA-256 integrity hash for an audit event.

    The integrity hash is calculated from the event contents,
    excluding the integrity_hash field itself.
    """

    data = {
        key: value
        for key, value in event.items()
        if key != "integrity_hash"
    }

    canonical_data = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()


def _get_previous_hash():
    """
    Return the integrity hash of the most recent audit event.

    The first event in the chain uses None as its previous hash.
    """

    if not os.path.exists(AUDIT_FILE):
        return None

    last_event = None

    with open(
        AUDIT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            if not line.strip():
                continue

            last_event = json.loads(line)

    if last_event is None:
        return None

    return last_event.get("integrity_hash")


def log_security_event(
    agent_id,
    user_id,
    user_role,
    tool_name,
    arguments,
    decision,
    risk_level,
    reason,
    executed,
    ml_risk_probability=None,
    ml_risk_band=None,
    ml_escalated=None,
    approval_id=None,
    event_type="SECURITY_DECISION",
):
    """
    Record a tamper-evident security event.

    Supports both deterministic gateway events and
    hybrid ML-assisted security events.

    Optional metadata:
        - ML risk probability
        - ML risk band
        - ML escalation status
        - approval ID
        - event type

    Every event is linked to the previous event using
    a SHA-256 hash chain.
    """

    os.makedirs("data", exist_ok=True)

    previous_hash = _get_previous_hash()

    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "agent_id": agent_id,
        "user_id": user_id,
        "user_role": user_role,
        "tool_name": tool_name,
        "arguments": arguments,
        "decision": decision,
        "risk_level": risk_level,
        "reason": reason,
        "executed": executed,
        "previous_hash": previous_hash,
    }

    # Add hybrid-security metadata only when supplied.
    if ml_risk_probability is not None:
        event["ml_risk_probability"] = ml_risk_probability

    if ml_risk_band is not None:
        event["ml_risk_band"] = ml_risk_band

    if ml_escalated is not None:
        event["ml_escalated"] = ml_escalated

    if approval_id is not None:
        event["approval_id"] = approval_id

    event["integrity_hash"] = _calculate_integrity_hash(
        event
    )

    with open(
        AUDIT_FILE,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(event) + "\n"
        )

    return event

def verify_audit_log():
    """
    Verify the integrity of the complete audit log.

    Returns a security result describing whether the
    audit chain is intact.
    """

    if not os.path.exists(AUDIT_FILE):
        return {
            "success": True,
            "valid": True,
            "event_count": 0,
            "message": "Audit log does not exist or is empty.",
        }

    previous_hash = None
    event_count = 0

    with open(
        AUDIT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1
        ):

            if not line.strip():
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "valid": False,
                    "event_count": event_count,
                    "error": (
                        f"Invalid JSON at audit log "
                        f"line {line_number}."
                    ),
                }

            stored_hash = event.get(
                "integrity_hash"
            )

            calculated_hash = _calculate_integrity_hash(
                event
            )

            if stored_hash != calculated_hash:
                return {
                    "success": True,
                    "valid": False,
                    "event_count": event_count,
                    "error": (
                        "Audit event integrity verification "
                        f"failed at line {line_number}."
                    ),
                }

            if event.get("previous_hash") != previous_hash:
                return {
                    "success": True,
                    "valid": False,
                    "event_count": event_count,
                    "error": (
                        "Audit hash chain verification "
                        f"failed at line {line_number}."
                    ),
                }

            previous_hash = stored_hash
            event_count += 1

    return {
        "success": True,
        "valid": True,
        "event_count": event_count,
        "message": (
            "Audit log integrity verification passed."
        ),
    }
