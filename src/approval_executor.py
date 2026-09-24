from src.approval import get_approval
from src.protected_tools import execute_protected_tool


def execute_approved_request(
    approval_id: str,
):
    """
    Execute a request only after verifying
    that a human has approved it.
    """

    # -------------------------------------------------
    # 1. Find approval request
    # -------------------------------------------------

    approval = get_approval(approval_id)

    if approval is None:

        return {
            "success": False,
            "executed": False,
            "error": "Approval request not found.",
        }

    # -------------------------------------------------
    # 2. Verify approval status
    # -------------------------------------------------

    if approval["status"] != "APPROVED":

        return {
            "success": False,
            "executed": False,
            "error": (
                "Approval request is not approved."
            ),
        }

    # -------------------------------------------------
    # 3. Execute through the security gateway
    # -------------------------------------------------

    result = execute_protected_tool(
        agent_id=approval["agent_id"],
        user_id=approval["user_id"],
        user_role=approval["user_role"],
        tool_name=approval["tool_name"],
        arguments=approval["arguments"],
    )

    return result
