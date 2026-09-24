from src.audit import log_security_event

"""
Secure Agent Execution Layer
============================

Provides the controlled execution path:

    Agent Request
        |
        v
    Hybrid Security Gateway
        |
        v
    ALLOW / HUMAN_REVIEW / BLOCK
        |
        v
    Protected Tool / Approval Workflow

The agent never executes protected tools directly.
"""

from src.security_gateway import (
    SecurityRequest,
    Decision,
)

from src.hybrid_gateway import evaluate_hybrid_request
from src.approval import create_approval_request

from src.tools import (
    get_customer,
    get_policy,
    get_claim,
    get_claim_documents,
    get_claim_history,
    approve_settlement,
)


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOL_REGISTRY = {
    "get_customer": get_customer,
    "get_policy": get_policy,
    "get_claim": get_claim,
    "get_claim_documents": get_claim_documents,
    "get_claim_history": get_claim_history,
    "approve_settlement": approve_settlement,
}


# ============================================================
# AUDIT HELPER
# ============================================================

def _audit_agent_decision(
    agent_id,
    user_id,
    user_role,
    tool_name,
    arguments,
    decision,
    executed=False,
    approval_id=None,
):
    """
    Record the final hybrid security decision made
    for an agent-requested action.

    The audit record includes deterministic and ML
    security information where available.
    """

    return log_security_event(
        agent_id=agent_id,
        user_id=user_id,
        user_role=user_role,
        tool_name=tool_name,
        arguments=arguments,
        decision=decision.decision.value,
        risk_level=decision.risk_level.value,
        reason=decision.reason,
        executed=executed,
        ml_risk_probability=getattr(
            decision,
            "ml_risk_probability",
            None,
        ),
        ml_risk_band=getattr(
            decision,
            "ml_risk_band",
            None,
        ),
        ml_escalated=getattr(
            decision,
            "ml_escalated",
            None,
        ),
        approval_id=approval_id,
        event_type="AGENT_SECURITY_DECISION",
    )


# ============================================================
# SECURE AGENT EXECUTION
# ============================================================

def execute_agent_action(
    *,
    agent_id,
    user_id,
    user_role,
    tool_name,
    arguments,
    sensitive_document=False,
    prompt_injection_signal=False,
    unusual_access_volume=False,
):
    """
    Execute an agent-requested tool through the hybrid
    deterministic + ML security gateway.

    Security architecture:

        Agent request
            -> SecurityRequest
            -> deterministic authorization
            -> ML risk analysis
            -> hybrid enforcement
            -> ALLOW / HUMAN_REVIEW / BLOCK
            -> audit logging
            -> protected execution / approval workflow

    Important:
        The agent does not decide whether a tool is safe.
        Security decisions are made by the gateway.
    """

    # --------------------------------------------------------
    # 1. Build canonical security request
    # --------------------------------------------------------

    request = SecurityRequest(
        agent_id=agent_id,
        user_id=user_id,
        user_role=user_role,
        tool_name=tool_name,
        arguments=arguments,
    )

    # --------------------------------------------------------
    # 2. Hybrid deterministic + ML authorization
    # --------------------------------------------------------

    decision = evaluate_hybrid_request(
        request,
        sensitive_document=sensitive_document,
        prompt_injection_signal=prompt_injection_signal,
        unusual_access_volume=unusual_access_volume,
    )

    print()
    print("=" * 60)
    print("SECURE AGENT GATEWAY")
    print("=" * 60)
    print(f"Agent:      {agent_id}")
    print(f"Tool:       {tool_name}")
    print(f"Role:       {user_role}")
    print(f"Decision:   {decision.decision.value}")
    print(f"Risk:       {decision.risk_level.value}")

    if decision.ml_available:
        print(
            "ML Risk:    "
            f"{decision.ml_risk_probability} "
            f"({decision.ml_risk_band})"
        )
    else:
        print("ML Risk:    unavailable")

    print(f"Reason:     {decision.reason}")

    # --------------------------------------------------------
    # 3. BLOCK
    # --------------------------------------------------------

    if decision.decision == Decision.BLOCK:

        _audit_agent_decision(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision=decision,
            executed=False,
        )

        return {
            "success": False,
            "executed": False,
            "decision": Decision.BLOCK.value,
            "risk_level": decision.risk_level.value,
            "ml_risk_probability": decision.ml_risk_probability,
            "ml_risk_band": decision.ml_risk_band,
            "ml_escalated": decision.ml_escalated,
            "error": decision.reason,
        }

    # --------------------------------------------------------
    # 4. HUMAN REVIEW
    # --------------------------------------------------------

    if decision.decision == Decision.HUMAN_REVIEW:

        approval = create_approval_request(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            reason=decision.reason,
        )

        _audit_agent_decision(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision=decision,
            executed=False,
            approval_id=approval["approval_id"],
        )

        return {
            "success": False,
            "executed": False,
            "decision": Decision.HUMAN_REVIEW.value,
            "risk_level": decision.risk_level.value,
            "ml_risk_probability": decision.ml_risk_probability,
            "ml_risk_band": decision.ml_risk_band,
            "ml_escalated": decision.ml_escalated,
            "requires_human_approval": True,
            "approval_id": approval["approval_id"],
            "message": (
                "Agent action requires human approval "
                "before execution."
            ),
        }

    # --------------------------------------------------------
    # 5. Defensive tool-registry check
    # --------------------------------------------------------

    if tool_name not in TOOL_REGISTRY:

        # This should normally be unreachable because the
        # security gateway should block unauthorized/unknown
        # tools before execution. It remains as defence in depth.

        _audit_agent_decision(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision=decision,
            executed=False,
        )

        return {
            "success": False,
            "executed": False,
            "decision": Decision.BLOCK.value,
            "risk_level": "HIGH",
            "ml_risk_probability": decision.ml_risk_probability,
            "ml_risk_band": decision.ml_risk_band,
            "ml_escalated": decision.ml_escalated,
            "error": (
                f"Tool '{tool_name}' is not registered "
                "for secure execution."
            ),
        }

    # --------------------------------------------------------
    # 6. Execute permitted tool
    # --------------------------------------------------------

    tool_function = TOOL_REGISTRY[tool_name]

    try:

        result = tool_function(**arguments)

    except Exception as error:

        # The gateway authorized the action, but the actual
        # protected tool failed during execution.

        _audit_agent_decision(
            agent_id=agent_id,
            user_id=user_id,
            user_role=user_role,
            tool_name=tool_name,
            arguments=arguments,
            decision=decision,
            executed=False,
        )

        return {
            "success": False,
            "executed": False,
            "decision": Decision.ALLOW.value,
            "risk_level": decision.risk_level.value,
            "ml_risk_probability": decision.ml_risk_probability,
            "ml_risk_band": decision.ml_risk_band,
            "ml_escalated": decision.ml_escalated,
            "error": "Tool execution failed.",
            "details": str(error),
        }

    # --------------------------------------------------------
    # 7. Audit successful execution
    # --------------------------------------------------------

    _audit_agent_decision(
        agent_id=agent_id,
        user_id=user_id,
        user_role=user_role,
        tool_name=tool_name,
        arguments=arguments,
        decision=decision,
        executed=True,
    )

    # --------------------------------------------------------
    # 8. Return execution result
    # --------------------------------------------------------

    return {
        "success": result.get("success", False),
        "executed": True,
        "decision": Decision.ALLOW.value,
        "risk_level": decision.risk_level.value,
        "ml_risk_probability": decision.ml_risk_probability,
        "ml_risk_band": decision.ml_risk_band,
        "ml_escalated": decision.ml_escalated,
        "result": result,
    }