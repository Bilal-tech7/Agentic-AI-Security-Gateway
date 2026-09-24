from src.audit import log_security_event
from datetime import datetime
import hashlib
import json
import os
import uuid


APPROVAL_FILE = "data/pending_approvals.jsonl"


def _calculate_integrity_hash(approval):
    """
    Calculate a SHA-256 integrity hash for the
    security-sensitive fields of an approval request.

    The hash covers the identity, role, tool, arguments,
    and reason that were originally approved.
    """

    protected_data = {
        "agent_id": approval["agent_id"],
        "user_id": approval["user_id"],
        "user_role": approval["user_role"],
        "tool_name": approval["tool_name"],
        "arguments": approval["arguments"],
        "reason": approval["reason"],
    }

    serialized = json.dumps(
        protected_data,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def _verify_integrity(approval):
    """
    Verify that an approval request has not been
    modified since its integrity hash was created.
    """

    stored_hash = approval.get("integrity_hash")

    if not stored_hash:
        return False

    calculated_hash = _calculate_integrity_hash(
        approval
    )

    return stored_hash == calculated_hash


def create_approval_request(
    agent_id,
    user_id,
    user_role,
    tool_name,
    arguments,
    reason,
):
    """
    Create a new human approval request.

    The request receives an integrity hash so that
    security-sensitive fields cannot be modified
    without detection.
    """

    os.makedirs("data", exist_ok=True)

    approval = {
        "approval_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": agent_id,
        "user_id": user_id,
        "user_role": user_role,
        "tool_name": tool_name,
        "arguments": arguments,
        "reason": reason,
        "status": "PENDING",
    }

    approval["integrity_hash"] = _calculate_integrity_hash(
        approval
    )

    with open(
        APPROVAL_FILE,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(approval) + "\n"
        )

    return approval


def get_pending_approvals():
    """
    Return all approval requests that are
    currently waiting for human review.
    """

    if not os.path.exists(APPROVAL_FILE):
        return []

    approvals = []

    with open(
        APPROVAL_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if not line.strip():
                continue

            approval = json.loads(line)

            if approval["status"] == "PENDING":
                approvals.append(approval)

    return approvals


def get_approval(approval_id):
    """
    Find a specific approval request.
    """

    if not os.path.exists(APPROVAL_FILE):
        return None

    with open(
        APPROVAL_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if not line.strip():
                continue

            approval = json.loads(line)

            if approval["approval_id"] == approval_id:
                return approval

    return None


def update_approval_status(
    approval_id,
    status,
):
    """
    Update an approval request status.

    The original protected fields remain unchanged.
    The integrity hash therefore continues to describe
    the original approved request.
    """

    if not os.path.exists(APPROVAL_FILE):
        return False

    approvals = []

    with open(
        APPROVAL_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if not line.strip():
                continue

            approval = json.loads(line)

            if approval["approval_id"] == approval_id:

                approval["status"] = status
                approval["updated_at"] = (
                    datetime.utcnow().isoformat()
                )

            approvals.append(approval)

    with open(
        APPROVAL_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        for approval in approvals:

            file.write(
                json.dumps(approval) + "\n"
            )

    return True


def approve_request(approval_id):
    """
    Approve a pending human-review request.

    Integrity is checked before approval so that a
    tampered pending request cannot be approved.
    """

    approval = get_approval(approval_id)

    if approval is None:
        return {
            "success": False,
            "error": "Approval request not found.",
        }

    if not _verify_integrity(approval):
        return {
            "success": False,
            "approval_id": approval_id,
            "status": approval["status"],
            "error": (
                "Approval request integrity verification failed."
            ),
        }

    if approval["status"] != "PENDING":
        return {
            "success": False,
            "error": (
                f"Approval request is already "
                f"{approval['status']}."
            ),
        }

    update_approval_status(
        approval_id,
        "APPROVED",
    )

    return {
        "success": True,
        "approval_id": approval_id,
        "status": "APPROVED",
    }


def reject_request(approval_id):
    """
    Reject a pending human-review request.

    Integrity is checked before rejection.
    """

    approval = get_approval(approval_id)

    if approval is None:
        return {
            "success": False,
            "error": "Approval request not found.",
        }

    if not _verify_integrity(approval):
        return {
            "success": False,
            "approval_id": approval_id,
            "status": approval["status"],
            "error": (
                "Approval request integrity verification failed."
            ),
        }

    if approval["status"] != "PENDING":
        return {
            "success": False,
            "error": (
                f"Approval request is already "
                f"{approval['status']}."
            ),
        }

    update_approval_status(
        approval_id,
        "REJECTED",
    )

    return {
        "success": True,
        "approval_id": approval_id,
        "status": "REJECTED",
    }


def execute_approved_request(approval_id):
    """
    Execute a request only when:

    1. The approval exists.
    2. The approval is APPROVED.
    3. The approval integrity hash is valid.
    4. The tool exists.
    5. The security gateway still authorizes
       the original request.

    The request is marked EXECUTED only after
    successful tool execution.
    """

    approval = get_approval(approval_id)

    if approval is None:
        return {
            "success": False,
            "error": "Approval request not found.",
        }

    if approval["status"] != "APPROVED":
        return {
            "success": False,
            "approval_id": approval_id,
            "status": approval["status"],
            "error": (
                "Approval request has not been approved."
            ),
        }

    if not _verify_integrity(approval):
        return {
            "success": False,
            "approval_id": approval_id,
            "status": approval["status"],
            "error": (
                "Approval request integrity verification failed. "
                "The approved request may have been tampered with."
            ),
        }

    from src.security_gateway import (
        SecurityRequest,
        evaluate_request,
        Decision,
    )

    from src.tools import (
        get_customer,
        get_policy,
        get_claim,
        get_claim_documents,
        get_claim_history,
        approve_settlement,
    )

    tool_registry = {
        "get_customer": get_customer,
        "get_policy": get_policy,
        "get_claim": get_claim,
        "get_claim_documents": get_claim_documents,
        "get_claim_history": get_claim_history,
        "approve_settlement": approve_settlement,
    }

    tool_name = approval["tool_name"]
    arguments = approval["arguments"]

    if tool_name not in tool_registry:
        return {
            "success": False,
            "approval_id": approval_id,
            "status": approval["status"],
            "error": (
                f"Approved tool does not exist: {tool_name}"
            ),
        }

    request = SecurityRequest(
        agent_id=approval["agent_id"],
        user_id=approval["user_id"],
        user_role=approval["user_role"],
        tool_name=tool_name,
        arguments=arguments,
    )

    decision = evaluate_request(
    request,
    human_approved=True
    )

    print()
    print("=" * 60)
    print("SECURITY GATEWAY")
    print("=" * 60)

    print(f"Tool:       {tool_name}")
    print(f"Role:       {approval['user_role']}")
    print(f"Decision:   {decision.decision.value}")
    print(f"Risk:       {decision.risk_level.value}")
    print(f"Reason:     {decision.reason}")

    if decision.decision != Decision.ALLOW:
        return {
            "success": False,
            "approval_id": approval_id,
            "status": approval["status"],
            "error": (
                "Approved request was not authorized "
                "by the security gateway."
            ),
            "decision": decision.decision.value,
            "risk_level": decision.risk_level.value,
            "reason": decision.reason,
        }

    tool_function = tool_registry[tool_name]

    try:
        result = tool_function(**arguments)

    except Exception as error:
        return {
            "success": False,
            "approval_id": approval_id,
            "status": approval["status"],
            "error": "Approved tool execution failed.",
            "result": {
                "success": False,
                "error": str(error),
            },
        }

    if not result.get("success", False):
        return {
            "success": False,
            "approval_id": approval_id,
            "status": approval["status"],
            "error": "Approved tool execution failed.",
            "result": result,
        }

    update_approval_status(
        approval_id,
        "EXECUTED",
    )

    log_security_event(
        agent_id=approval["agent_id"],
        user_id=approval["user_id"],
        user_role=approval["user_role"],
        tool_name=tool_name,
        arguments=arguments,
        decision="ALLOW",
        risk_level=decision.risk_level.value,
        reason=(
            "Human-approved high-risk action executed "
            "after security gateway re-authorization."
        ),
        executed=True,
        approval_id=approval_id,
        event_type="APPROVED_EXECUTION",
    )

    return {
        "success": True,
        "approval_id": approval_id,
        "status": "EXECUTED",
        "tool_name": tool_name,
        "result": result,
    }
