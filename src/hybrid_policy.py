from dataclasses import dataclass

from .security_gateway import (
    Decision,
    RiskLevel,
    SecurityDecision,
)


@dataclass
class HybridSecurityDecision:
    decision: Decision
    risk_level: RiskLevel
    reason: str

    deterministic_decision: str
    deterministic_risk_level: str

    ml_risk_probability: float | None = None
    ml_risk_band: str | None = None
    ml_available: bool = False
    ml_escalated: bool = False


def apply_ml_enforcement(
    deterministic_decision: SecurityDecision,
    ml_result: dict | None,
) -> HybridSecurityDecision:
    """
    Combine deterministic authorization with ML risk.

    Security principles:

    1. ML can NEVER downgrade a deterministic BLOCK.
    2. ML can NEVER bypass HUMAN_REVIEW.
    3. ML may escalate an otherwise ALLOW request.
    4. HIGH ML risk escalates ALLOW -> HUMAN_REVIEW.
    5. CRITICAL ML risk escalates ALLOW -> BLOCK.
    6. If ML is unavailable, deterministic security remains active.
    """

    original_decision = deterministic_decision.decision
    original_risk = deterministic_decision.risk_level

    # ---------------------------------------------------------
    # Deterministic BLOCK always wins
    # ---------------------------------------------------------

    if original_decision == Decision.BLOCK:
        return HybridSecurityDecision(
            decision=Decision.BLOCK,
            risk_level=original_risk,
            reason=deterministic_decision.reason,
            deterministic_decision=original_decision.value,
            deterministic_risk_level=original_risk.value,
            ml_risk_probability=(
                ml_result.get("risk_probability")
                if ml_result
                else None
            ),
            ml_risk_band=(
                ml_result.get("risk_band")
                if ml_result
                else None
            ),
            ml_available=ml_result is not None,
            ml_escalated=False,
        )

    # ---------------------------------------------------------
    # Deterministic HUMAN_REVIEW also remains authoritative
    # ---------------------------------------------------------

    if original_decision == Decision.HUMAN_REVIEW:
        return HybridSecurityDecision(
            decision=Decision.HUMAN_REVIEW,
            risk_level=original_risk,
            reason=deterministic_decision.reason,
            deterministic_decision=original_decision.value,
            deterministic_risk_level=original_risk.value,
            ml_risk_probability=(
                ml_result.get("risk_probability")
                if ml_result
                else None
            ),
            ml_risk_band=(
                ml_result.get("risk_band")
                if ml_result
                else None
            ),
            ml_available=ml_result is not None,
            ml_escalated=False,
        )

    # ---------------------------------------------------------
    # ML unavailable -> fail safely to deterministic controls
    # ---------------------------------------------------------

    if not ml_result:
        return HybridSecurityDecision(
            decision=original_decision,
            risk_level=original_risk,
            reason=(
                deterministic_decision.reason
                + " ML risk analysis was unavailable; "
                  "deterministic security remained active."
            ),
            deterministic_decision=original_decision.value,
            deterministic_risk_level=original_risk.value,
            ml_available=False,
            ml_escalated=False,
        )

    probability = ml_result.get("risk_probability")
    band = ml_result.get("risk_band")

    # ---------------------------------------------------------
    # CRITICAL ML risk -> BLOCK
    # ---------------------------------------------------------

    if band == "CRITICAL":
        return HybridSecurityDecision(
            decision=Decision.BLOCK,
            risk_level=RiskLevel.CRITICAL,
            reason=(
                "Deterministic controls permitted the request, "
                "but ML detected CRITICAL security risk. "
                "The request was blocked by hybrid enforcement."
            ),
            deterministic_decision=original_decision.value,
            deterministic_risk_level=original_risk.value,
            ml_risk_probability=probability,
            ml_risk_band=band,
            ml_available=True,
            ml_escalated=True,
        )

    # ---------------------------------------------------------
    # HIGH ML risk -> HUMAN_REVIEW
    # ---------------------------------------------------------

    if band == "HIGH":
        return HybridSecurityDecision(
            decision=Decision.HUMAN_REVIEW,
            risk_level=RiskLevel.HIGH,
            reason=(
                "Deterministic controls permitted the request, "
                "but ML detected HIGH security risk. "
                "Human review is required."
            ),
            deterministic_decision=original_decision.value,
            deterministic_risk_level=original_risk.value,
            ml_risk_probability=probability,
            ml_risk_band=band,
            ml_available=True,
            ml_escalated=True,
        )

    # ---------------------------------------------------------
    # LOW/MEDIUM -> keep deterministic ALLOW
    # ---------------------------------------------------------

    return HybridSecurityDecision(
        decision=original_decision,
        risk_level=original_risk,
        reason=deterministic_decision.reason,
        deterministic_decision=original_decision.value,
        deterministic_risk_level=original_risk.value,
        ml_risk_probability=probability,
        ml_risk_band=band,
        ml_available=True,
        ml_escalated=False,
    )