from src.approval import create_approval_request
from src.audit import log_security_event
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


TOOL_REGISTRY = {
    "get_customer": get_customer,
    "get_policy": get_policy,
    "get_claim": get_claim,
    "get_claim_documents": get_claim_documents,
    "get_claim_history": get_claim_history,
    "approve_settlement": approve_settlement,
}


def execute_protected_tool(
    agent_id: str,
    user_id: int | None,
    user_role: str,
    tool_name: str,
    arguments: dict,
):
    """
    Execute an agent-requested tool only after
    the security gateway approves the request.
    """

    # -------------------------------------------------
    # 1. Build security request
    # -------------------------------------------------

    request = SecurityRequest(
        agent_id=agent_id,
        user_id=user_id,
        user_role=user_role,
        tool_name=tool_name,
        arguments=arguments,
    )

    # -------------------------------------------------
    # 2. Ask security gateway
    # -------------------------------------------------

    decision = evaluate_request(request)

    print()
    print("=" * 60)
    print("SECURITY GATEWAY")
    print("=" * 60)

    print(f"Tool:       {tool_name}")
    print(f"Role:       {user_role}")
    print(f"Decision:   {decision.decision.value}")
    print(f"Risk:       {decision.risk_level.value}")
    print(f"Reason:     {decision.reason}")

    # -------------------------------------------------
    # 3. BLOCK
    # -------------------------------------------------

    if decision.decision == Decision.BLOCK:

        log_security_event(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision=decision.decision.value,
            risk_level=decision.risk_level.value,
            reason=decision.reason,
            executed=False,
        )

        return {
            "success": False,
            "executed": False,
            "decision": decision.decision.value,
            "risk_level": decision.risk_level.value,
            "error": decision.reason,
        }

    # -------------------------------------------------
    # 4. HUMAN REVIEW
    # -------------------------------------------------

    if decision.decision == Decision.HUMAN_REVIEW:

        approval = create_approval_request(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            reason=decision.reason,
        )

        log_security_event(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision=decision.decision.value,
            risk_level=decision.risk_level.value,
            reason=decision.reason,
            executed=False,
        )

        return {
            "success": False,
            "executed": False,
            "decision": decision.decision.value,
            "risk_level": decision.risk_level.value,
            "requires_human_approval": True,
            "approval_id": approval["approval_id"],
            "message": (
                "The requested action requires "
                "human approval before execution."
            ),
        }

    # -------------------------------------------------
    # 5. ALLOW
    # -------------------------------------------------

    if tool_name not in TOOL_REGISTRY:

        reason = f"Unknown tool: {tool_name}"

        log_security_event(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision="BLOCK",
            risk_level="HIGH",
            reason=reason,
            executed=False,
        )

        return {
            "success": False,
            "executed": False,
            "decision": "BLOCK",
            "risk_level": "HIGH",
            "error": reason,
        }

    tool_function = TOOL_REGISTRY[tool_name]

    # -------------------------------------------------
    # 6. Execute approved tool
    # -------------------------------------------------

    try:

        result = tool_function(**arguments)

        log_security_event(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision=decision.decision.value,
            risk_level=decision.risk_level.value,
            reason=decision.reason,
            executed=True,
        )

        return {
            "success": True,
            "executed": True,
            "decision": decision.decision.value,
            "risk_level": decision.risk_level.value,
            "result": result,
        }

    # -------------------------------------------------
    # 7. Tool execution error
    # -------------------------------------------------

    except Exception as error:

        log_security_event(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision=decision.decision.value,
            risk_level=decision.risk_level.value,
            reason=str(error),
            executed=False,
        )

        return {
            "success": False,
            "executed": False,
            "decision": decision.decision.value,
            "risk_level": decision.risk_level.value,
            "error": str(error),
        }
