from .security_gateway import (
    SecurityRequest,
    evaluate_request,
)

from .ml_risk import (
    build_risk_features,
    predict_risk,
)

from .hybrid_policy import apply_ml_enforcement


def evaluate_hybrid_request(
    request: SecurityRequest,
    *,
    sensitive_document=False,
    prompt_injection_signal=False,
    unusual_access_volume=False,
):
    """
    Evaluate a request using:

    1. Deterministic authorization
    2. ML risk estimation
    3. Hybrid enforcement policy

    Deterministic security remains authoritative.
    ML may only increase security restrictions.
    """

    # ---------------------------------------------------------
    # 1. Deterministic security
    # ---------------------------------------------------------

    deterministic = evaluate_request(request)

    # ---------------------------------------------------------
    # 2. Build ML features
    # ---------------------------------------------------------

    try:

        from .security_gateway import (
            HIGH_RISK_TOOLS,
            RESOURCE_SCOPED_TOOLS,
            ROLE_PERMISSIONS,
            is_claim_assigned_to_user,
        )

        is_unknown_tool = not any(
            request.tool_name in tools
            for tools in ROLE_PERMISSIONS.values()
        )

        allowed_tools = ROLE_PERMISSIONS.get(
            request.user_role,
            set(),
        )

        role_tool_mismatch = (
            request.tool_name not in allowed_tools
        )

        is_resource_scoped = (
            request.tool_name in RESOURCE_SCOPED_TOOLS
        )

        claim_id = request.arguments.get("claim_id")

        missing_claim_id = (
            is_resource_scoped
            and claim_id is None
        )

        malformed_arguments = (
            is_resource_scoped
            and claim_id is not None
            and not isinstance(claim_id, int)
        )

        is_assigned = False

        if (
            is_resource_scoped
            and isinstance(claim_id, int)
        ):
            is_assigned = is_claim_assigned_to_user(
                request.user_id,
                claim_id,
            )

        features = build_risk_features(
            is_high_risk_tool=(
                request.tool_name in HIGH_RISK_TOOLS
            ),
            is_unknown_tool=is_unknown_tool,
            is_resource_scoped=is_resource_scoped,
            is_assigned=is_assigned,
            role_tool_mismatch=role_tool_mismatch,
            sensitive_document=sensitive_document,
            prompt_injection_signal=prompt_injection_signal,
            unusual_access_volume=unusual_access_volume,
            missing_claim_id=missing_claim_id,
            malformed_arguments=malformed_arguments,
        )

        ml_result = predict_risk(features)

    except Exception as error:

        ml_result = None

        print()
        print("ML RISK MODEL WARNING:")
        print(
            "ML analysis failed. Deterministic security "
            "remains active."
        )
        print(f"ML error: {error}")

    # ---------------------------------------------------------
    # 3. Hybrid policy
    # ---------------------------------------------------------

    return apply_ml_enforcement(
        deterministic,
        ml_result,
    )