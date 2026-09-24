from dataclasses import dataclass
from enum import Enum

from .database import SessionLocal
from .models import ClaimAssignment


class Decision(str, Enum):
    ALLOW = "ALLOW"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityRequest:
    agent_id: str
    user_id: int | None
    user_role: str
    tool_name: str
    arguments: dict


@dataclass
class SecurityDecision:
    decision: Decision
    risk_level: RiskLevel
    reason: str

    # Supplementary ML information.
    # These fields never replace deterministic authorization.
    ml_risk_probability: float | None = None
    ml_risk_band: str | None = None
    ml_analysis_available: bool = False


# ============================================================
# ROLE PERMISSIONS
# ============================================================

ROLE_PERMISSIONS = {
    "CUSTOMER": {
        "get_claim",
        "get_policy",
        "get_customer",
    },

    "CLAIMS_ASSISTANT": {
        "get_claim",
        "get_policy",
        "get_customer",
        "get_claim_documents",
        "get_claim_history",
    },

    "CLAIMS_OFFICER": {
        "get_claim",
        "get_policy",
        "get_customer",
        "get_claim_documents",
        "get_claim_history",
        "approve_settlement",
        "reject_claim",
    },

    "CLAIMS_MANAGER": {
        "get_claim",
        "get_policy",
        "get_customer",
        "get_claim_documents",
        "get_claim_history",
        "approve_settlement",
        "reject_claim",
        "change_payment_details",
    },

    "SYSTEM_ADMIN": {
        "get_claim",
        "get_policy",
        "get_customer",
        "get_claim_documents",
        "get_claim_history",
    },
}


# ============================================================
# HIGH-RISK TOOLS
# ============================================================

HIGH_RISK_TOOLS = {
    "change_payment_details",
    "approve_settlement",
    "reject_claim",
    "delete_claim",
    "export_customer_data",
}


# ============================================================
# RESOURCE-SCOPED TOOLS
# ============================================================

# These tools operate on a specific insurance claim.
# They therefore require claim-level authorization.
RESOURCE_SCOPED_TOOLS = {
    "get_claim",
    "get_claim_documents",
    "approve_settlement",
    "reject_claim",
    "change_payment_details",
    "delete_claim",
}


# ============================================================
# BUSINESS RULES
# ============================================================

# A claim must reach settlement review before settlement
# approval can be requested.
VALID_SETTLEMENT_STATES = {
    "SETTLEMENT_REVIEW",
}


# ============================================================
# RESOURCE AUTHORIZATION
# ============================================================

def is_claim_assigned_to_user(
    user_id: int | None,
    claim_id: int
) -> bool:
    """
    Check whether the specified user has an active assignment
    for the specified claim.
    """

    if user_id is None:
        return False

    session = SessionLocal()

    try:
        assignment = (
            session.query(ClaimAssignment)
            .filter(
                ClaimAssignment.user_id == user_id,
                ClaimAssignment.claim_id == claim_id,
                ClaimAssignment.active.is_(True)
            )
            .first()
        )

        return assignment is not None

    finally:
        session.close()


# ============================================================
# CLAIM LOOKUP FOR SECURITY CHECKS
# ============================================================

def get_claim_for_security_check(claim_id):
    """
    Retrieve a claim for authorization and business-rule checks.

    This function is read-only.
    It does not modify the claim.
    """

    from .models import Claim

    db = SessionLocal()

    try:
        return (
            db.query(Claim)
            .filter(Claim.claim_id == claim_id)
            .first()
        )

    finally:
        db.close()


# ============================================================
# SECURITY GATEWAY
# ============================================================

def evaluate_request(
    request: SecurityRequest,
    human_approved: bool = False
) -> SecurityDecision:
    """
    Evaluate whether an agent/user is authorized to perform
    a requested tool action.

    Security decisions:
        ALLOW
        HUMAN_REVIEW
        BLOCK

    The gateway evaluates:

        1. User role
        2. Tool permission
        3. Resource authorization
        4. Claim existence
        5. Business-state rules
        6. High-risk action requirements

    The gateway is policy enforcement only.
    Actual tool execution happens elsewhere.
    """

    # ========================================================
    # 1. VALIDATE USER ROLE
    # ========================================================

    if request.user_role not in ROLE_PERMISSIONS:

        return SecurityDecision(
            decision=Decision.BLOCK,
            risk_level=RiskLevel.CRITICAL,
            reason="Unknown or unauthorized user role."
        )

    # ========================================================
    # 2. VALIDATE TOOL PERMISSION
    # ========================================================

    allowed_tools = ROLE_PERMISSIONS[request.user_role]

    if request.tool_name not in allowed_tools:

        return SecurityDecision(
            decision=Decision.BLOCK,
            risk_level=RiskLevel.HIGH,
            reason=(
                f"Tool '{request.tool_name}' is not permitted "
                f"for role '{request.user_role}'."
            )
        )

    # ========================================================
    # 3. RESOURCE-LEVEL AUTHORIZATION
    # ========================================================

    if request.tool_name in RESOURCE_SCOPED_TOOLS:

        # ----------------------------------------------------
        # 3.1 claim_id must exist
        # ----------------------------------------------------

        claim_id = request.arguments.get("claim_id")

        if claim_id is None:

            return SecurityDecision(
                decision=Decision.BLOCK,
                risk_level=RiskLevel.HIGH,
                reason=(
                    "Resource-scoped tool requires claim_id."
                )
            )

        # ----------------------------------------------------
        # 3.2 claim_id must be an integer
        # ----------------------------------------------------

        if not isinstance(claim_id, int):

            return SecurityDecision(
                decision=Decision.BLOCK,
                risk_level=RiskLevel.HIGH,
                reason="claim_id must be an integer."
            )

        # ----------------------------------------------------
        # 3.3 claim must exist
        # ----------------------------------------------------

        claim = get_claim_for_security_check(claim_id)

        if claim is None:

            return SecurityDecision(
                decision=Decision.BLOCK,
                risk_level=RiskLevel.HIGH,
                reason=(
                    f"Claim {claim_id} does not exist."
                )
            )

        # ----------------------------------------------------
        # 3.4 assignment authorization
        # ----------------------------------------------------

        if not is_claim_assigned_to_user(
            request.user_id,
            claim_id
        ):

            return SecurityDecision(
                decision=Decision.BLOCK,
                risk_level=RiskLevel.HIGH,
                reason=(
                    f"User {request.user_id} is not assigned "
                    f"to claim {claim_id}."
                )
            )

        # ----------------------------------------------------
        # 3.5 settlement business rule
        # ----------------------------------------------------

        if request.tool_name == "approve_settlement":

            if claim.status not in VALID_SETTLEMENT_STATES:

                return SecurityDecision(
                    decision=Decision.BLOCK,
                    risk_level=RiskLevel.HIGH,
                    reason=(
                        f"Claim {claim_id} is in status "
                        f"'{claim.status}' and is not eligible "
                        f"for settlement approval."
                    )
                )

    # ========================================================
    # 4. HIGH-RISK ACTIONS REQUIRE HUMAN REVIEW
    # ========================================================

    if request.tool_name in HIGH_RISK_TOOLS:

        if human_approved:
            return SecurityDecision(
                decision=Decision.ALLOW,
                risk_level=RiskLevel.CRITICAL,
                reason=(
                    "Human approval has been verified. "
                    "High-risk action is authorized for execution."
                )
            )

        return SecurityDecision(
            decision=Decision.HUMAN_REVIEW,
            risk_level=RiskLevel.CRITICAL,
            reason=(
                f"Tool '{request.tool_name}' is a high-risk "
                f"action and requires human approval."
            )
        )

    # ========================================================
    # 5. NORMAL PERMITTED ACTION
    # ========================================================

    return SecurityDecision(
        decision=Decision.ALLOW,
        risk_level=RiskLevel.LOW,
        reason=(
            "Tool and resource are permitted for this user."
        )
    )

def evaluate_request_with_ml(
    request,
    *,
    human_approved=False,
    sensitive_document=False,
    prompt_injection_signal=False,
    unusual_access_volume=False,
):
    """
    Hybrid security evaluation.

    Deterministic authorization is performed first.

    ML is supplementary:
        - it cannot convert BLOCK to ALLOW
        - it cannot bypass HUMAN_REVIEW
        - it cannot execute tools
        - failure of the ML component does not remove
          deterministic security controls
    """

    # --------------------------------------------------------
    # 1. Deterministic security decision
    # --------------------------------------------------------

    decision = evaluate_request(
        request,
        human_approved=human_approved,
    )

    # --------------------------------------------------------
    # 2. Determine assignment context for ML
    # --------------------------------------------------------

    is_assigned = True

    if request.tool_name in RESOURCE_SCOPED_TOOLS:

        arguments = request.arguments

        if isinstance(arguments, dict):

            claim_id = arguments.get("claim_id")

            if isinstance(claim_id, int):
                is_assigned = is_claim_assigned_to_user(
                    request.user_id,
                    claim_id,
                )
            else:
                is_assigned = False

        else:
            is_assigned = False

    # --------------------------------------------------------
    # 3. Supplementary ML analysis
    # --------------------------------------------------------

    try:
        from .ml_risk import analyze_request_risk

        allowed_tools = ROLE_PERMISSIONS.get(
            request.user_role,
            set(),
        )

        ml_result = analyze_request_risk(
            request,
            allowed_tools=allowed_tools,
            high_risk_tools=HIGH_RISK_TOOLS,
            resource_scoped_tools=RESOURCE_SCOPED_TOOLS,
            is_assigned=is_assigned,
            sensitive_document=sensitive_document,
            prompt_injection_signal=prompt_injection_signal,
            unusual_access_volume=unusual_access_volume,
        )

        decision.ml_risk_probability = (
            ml_result["risk_probability"]
        )

        decision.ml_risk_band = (
            ml_result["risk_band"]
        )

        decision.ml_analysis_available = True

    except Exception as error:

        # Deterministic authorization remains authoritative.
        # We record that ML analysis was unavailable rather
        # than silently changing the security decision.

        decision.ml_risk_probability = None
        decision.ml_risk_band = "UNAVAILABLE"
        decision.ml_analysis_available = False

        print(
            "ML risk analysis unavailable:",
            str(error),
        )

    return decision