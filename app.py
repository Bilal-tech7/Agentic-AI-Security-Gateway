"""
Aurelia Web Application
=======================

Interactive web interface for the Aurelia Secure Agentic AI Gateway.

Security principle:

    AI proposes
        ->
    Security Gateway authorizes
        ->
    Protected Tool executes
"""

import streamlit as st
import json
import os


from src.database import SessionLocal
from src.models import Claim

from src.approval import (
    get_pending_approvals,
    approve_request,
    reject_request,
    execute_approved_request,
)

from src.audit import verify_audit_log

from src.ollama_agent import (
    run_agent,
    DEFAULT_MODEL,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Aurelia",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DATA HELPERS
# ============================================================

def get_claim_statistics():
    """
    Read current claim statistics from the Aurelia database.
    """

    db = SessionLocal()

    try:
        claims = db.query(Claim).all()

        stats = {
            "total": len(claims),
            "LODGED": 0,
            "DOCUMENTS_REQUIRED": 0,
            "UNDER_REVIEW": 0,
            "ASSESSMENT_REQUIRED": 0,
            "ASSESSMENT_COMPLETE": 0,
            "SETTLEMENT_REVIEW": 0,
            "SETTLEMENT_APPROVED": 0,
            "SETTLED": 0,
        }

        for claim in claims:

            if claim.status in stats:
                stats[claim.status] += 1

        return stats

    finally:
        db.close()


def get_recent_claims(limit=10):
    """
    Return recent claims from the database.
    """

    db = SessionLocal()

    try:
        claims = (
            db.query(Claim)
            .order_by(Claim.claim_id.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "Claim ID": claim.claim_id,
                "Event": claim.event_type,
                "Status": claim.status,
                "Priority": claim.priority,
                "Estimated Damage": claim.estimated_damage,
            }
            for claim in claims
        ]

    finally:
        db.close()


def get_claim_status(claim_id):
    """
    Return the current database status for one claim.
    """

    if claim_id is None:
        return None

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


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🛡️ Aurelia")

    st.caption(
        "Secure Agentic AI Gateway"
    )

    st.divider()

    NAV_PAGES = [
        "Dashboard",
        "AI Agent",
        "Claims",
        "Approvals",
        "Security Audit",
    ]

    # Keep application navigation separate from widget state.
    # This lets buttons elsewhere in the app navigate safely.
    if "app_page" not in st.session_state:
        st.session_state["app_page"] = "Dashboard"

    pending_page = st.session_state.pop(
        "pending_navigation",
        None,
    )

    if pending_page in NAV_PAGES:
        st.session_state["app_page"] = pending_page

    for nav_page in NAV_PAGES:
        is_current = (
            st.session_state["app_page"] == nav_page
        )

        if st.button(
            nav_page,
            key=f"nav_{nav_page}",
            use_container_width=True,
            type=(
                "primary"
                if is_current
                else "secondary"
            ),
            disabled=is_current,
        ):
            st.session_state["app_page"] = nav_page
            st.rerun()

    page = st.session_state["app_page"]

    st.divider()

    st.caption(
        "AI proposes → Security authorizes → Tool executes"
    )


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title(
        "Aurelia Security Dashboard"
    )

    st.caption(
        "Live operational view of the secure "
        "agentic insurance environment."
    )

    st.divider()

    claim_stats = get_claim_statistics()

    pending_approvals = (
        get_pending_approvals()
    )

    audit_result = (
        verify_audit_log()
    )

    audit_valid = audit_result.get(
        "valid",
        False,
    )

    audit_event_count = (
        audit_result.get(
            "event_count",
            0,
        )
    )

    # --------------------------------------------------------
    # MAIN METRICS
    # --------------------------------------------------------

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Total Claims",
            claim_stats["total"],
        )

    with col2:

        st.metric(
            "Pending Approvals",
            len(pending_approvals),
        )

    with col3:

        st.metric(
            "Security Events",
            audit_event_count,
        )

    with col4:

        st.metric(
            "Audit Integrity",
            (
                "VALID"
                if audit_valid
                else "INVALID"
            ),
        )

    st.divider()

    # --------------------------------------------------------
    # CLAIM STATUS
    # --------------------------------------------------------

    st.subheader(
        "Claims Overview"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Under Review",
            claim_stats[
                "UNDER_REVIEW"
            ],
        )

    with col2:

        st.metric(
            "Assessment Required",
            claim_stats[
                "ASSESSMENT_REQUIRED"
            ],
        )

    with col3:

        st.metric(
            "Settlement Review",
            claim_stats[
                "SETTLEMENT_REVIEW"
            ],
        )

    with col4:

        st.metric(
            "Settlement Approved",
            claim_stats[
                "SETTLEMENT_APPROVED"
            ],
        )

    col5, col6, col7, col8 = (
        st.columns(4)
    )

    with col5:

        st.metric(
            "Lodged",
            claim_stats[
                "LODGED"
            ],
        )

    with col6:

        st.metric(
            "Documents Required",
            claim_stats[
                "DOCUMENTS_REQUIRED"
            ],
        )

    with col7:

        st.metric(
            "Assessment Complete",
            claim_stats[
                "ASSESSMENT_COMPLETE"
            ],
        )

    with col8:

        st.metric(
            "Settled",
            claim_stats[
                "SETTLED"
            ],
        )

    st.divider()

    # --------------------------------------------------------
    # RECENT CLAIMS
    # --------------------------------------------------------

    st.subheader(
        "Recent Claims"
    )

    recent_claims = (
        get_recent_claims()
    )

    if recent_claims:

        st.dataframe(
            recent_claims,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No claims are currently available."
        )

    st.divider()

    # --------------------------------------------------------
    # ARCHITECTURE
    # --------------------------------------------------------

    st.subheader(
        "Security Architecture"
    )

    architecture_col1, architecture_col2 = (
        st.columns([2, 1])
    )

    with architecture_col1:

        st.info(
            """
**AI Agent**

↓

**Secure Agent Layer**

↓

**Hybrid Security Gateway**

↓

**ALLOW / HUMAN_REVIEW / BLOCK**

↓

**Protected Tool Execution**
            """
        )

    with architecture_col2:

        st.success(
            """
**Security Principle**

The AI proposes actions.

The security gateway independently
authorizes those actions.

Protected tools execute only when
authorization permits them.
            """
        )

    if audit_valid:

        st.success(
            f"Audit hash chain verified "
            f"successfully across "
            f"{audit_event_count} "
            f"security events."
        )

    else:

        st.error(
            "Audit integrity verification failed."
        )


# ============================================================
# AI AGENT
# ============================================================

elif page == "AI Agent":

    st.title(
        "Aurelia AI Claims Agent"
    )

    st.caption(
        "Local LLM reasoning protected by the "
        "Aurelia Hybrid Security Gateway."
    )

    approval_flash = st.session_state.pop("approval_flash", None)
    if approval_flash:
        st.success(approval_flash)

    st.divider()

    # --------------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------------

    config1, config2, config3 = (
        st.columns(3)
    )

    with config1:

        user_id = st.number_input(
            "User ID",
            min_value=1,
            value=3,
            step=1,
        )

    with config2:

        user_role = st.selectbox(
            "User Role",
            [
                "CLAIMS_ASSISTANT",
                "CLAIMS_OFFICER",
            ],
        )

    with config3:

        st.text_input(
            "Local Model",
            value=DEFAULT_MODEL,
            disabled=True,
        )

    st.caption(
        "Agent identity: claims-agent-01"
    )

    st.info(
        "The language model can propose actions, "
        "but it cannot authorize or directly "
        "execute protected tools."
    )

    st.divider()

    # --------------------------------------------------------
    # CHAT STATE
    # --------------------------------------------------------

    if (
        "agent_messages"
        not in st.session_state
    ):

        st.session_state[
            "agent_messages"
        ] = [
            {
                "role": "assistant",
                "content": (
                    "Hello. I'm Aurelia, the "
                    "claims assistant. Ask me "
                    "about an insurance claim."
                ),
            }
        ]

    # --------------------------------------------------------
    # DISPLAY CHAT HISTORY
    # --------------------------------------------------------

    for message in (
        st.session_state[
            "agent_messages"
        ]
    ):

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    # --------------------------------------------------------
    # USER PROMPT
    # --------------------------------------------------------

    prompt = st.chat_input(
        "Ask Aurelia naturally about a claim..."
    )

    if prompt:

        st.session_state[
            "agent_messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message(
            "user"
        ):

            st.write(
                prompt
            )

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Aurelia is reasoning and "
                "checking authorization..."
            ):

                try:

                    result = run_agent(
                        prompt,
                        agent_id=(
                            "claims-agent-01"
                        ),
                        user_id=int(
                            user_id
                        ),
                        user_role=(
                            user_role
                        ),
                        model=DEFAULT_MODEL,
                    )

                except Exception as error:

                    st.error(
                        "Unable to contact the "
                        "local Aurelia/Ollama "
                        "agent."
                    )

                    st.code(
                        str(error)
                    )

                    result = None

            # =================================================
            # NORMAL MODEL MESSAGE
            # =================================================

            if result is not None:

                if (
                    result["type"]
                    == "MESSAGE"
                ):

                    response_text = (
                        result.get(
                            "model_response",
                            (
                                "No response "
                                "was returned."
                            ),
                        )
                    )

                    st.write(
                        response_text
                    )

                    st.session_state[
                        "agent_messages"
                    ].append(
                        {
                            "role": (
                                "assistant"
                            ),
                            "content": (
                                response_text
                            ),
                        }
                    )

                # =============================================
                # TOOL REQUEST
                # =============================================

                elif (
                    result["type"]
                    == "TOOL_REQUEST"
                ):

                    proposed_tool = (
                        result.get(
                            "proposed_tool",
                            {},
                        )
                    )

                    security = (
                        result.get(
                            "security_result",
                            {},
                        )
                    )

                    tool_name = (
                        proposed_tool.get(
                            "tool_name",
                            "Unknown",
                        )
                    )

                    arguments = (
                        proposed_tool.get(
                            "arguments",
                            {},
                        )
                    )

                    decision = (
                        security.get(
                            "decision",
                            "UNKNOWN",
                        )
                    )

                    risk_level = (
                        security.get(
                            "risk_level",
                            "UNKNOWN",
                        )
                    )

                    # -----------------------------------------
                    # 1. LLM PROPOSAL
                    # -----------------------------------------

                    st.subheader(
                        "1. LLM Proposal"
                    )

                    proposal1, proposal2 = (
                        st.columns(2)
                    )

                    with proposal1:

                        st.write(
                            "**Requested Tool**"
                        )

                        st.code(
                            tool_name
                        )

                    with proposal2:

                        st.write(
                            "**Arguments**"
                        )

                        st.json(
                            arguments
                        )

                    # -----------------------------------------
                    # 2. SECURITY GATEWAY
                    # -----------------------------------------

                    st.subheader(
                        "2. Hybrid Security Gateway"
                    )

                    decision1, decision2, decision3 = (
                        st.columns(3)
                    )

                    with decision1:

                        st.metric(
                            "Decision",
                            decision,
                        )

                    with decision2:

                        st.metric(
                            "Risk Level",
                            risk_level,
                        )

                    ml_probability = (
                        security.get(
                            "ml_risk_probability"
                        )
                    )

                    ml_band = (
                        security.get(
                            "ml_risk_band"
                        )
                    )

                    with decision3:

                        if (
                            ml_probability
                            is not None
                        ):

                            st.metric(
                                "ML Risk",
                                (
                                    f"{ml_probability:.3f}"
                                ),
                            )

                        else:

                            st.metric(
                                "ML Risk",
                                "N/A",
                            )

                    if ml_band:

                        st.caption(
                            f"ML risk band: "
                            f"{ml_band}"
                        )

                    # -----------------------------------------
                    # ALLOW
                    # -----------------------------------------

                    if (
                        decision
                        == "ALLOW"
                    ):

                        st.subheader(
                            "3. Execution"
                        )

                        if security.get(
                            "executed",
                            False,
                        ):

                            st.success(
                                "AUTHORIZED — the "
                                "protected tool executed."
                            )

                            tool_result = (
                                security.get(
                                    "result"
                                )
                            )

                            if (
                                tool_result
                                is not None
                            ):

                                st.write(
                                    "**Protected "
                                    "Tool Result**"
                                )

                                st.json(
                                    tool_result
                                )

                            summary = (
                                f"Authorized "
                                f"`{tool_name}` with "
                                f"risk level "
                                f"`{risk_level}`. "
                                f"The protected tool "
                                f"executed."
                            )

                        else:

                            st.warning(
                                "The gateway authorized "
                                "the request, but tool "
                                "execution did not "
                                "complete."
                            )

                            summary = (
                                f"`{tool_name}` was "
                                f"authorized but did "
                                f"not execute "
                                f"successfully."
                            )

                    # -----------------------------------------
                    # HUMAN REVIEW
                    # -----------------------------------------

                    elif (
                        decision
                        == "HUMAN_REVIEW"
                    ):

                        st.subheader(
                            "3. Human Authorization"
                        )

                        st.warning(
                            "HUMAN REVIEW REQUIRED — "
                            "the protected action has "
                            "NOT been executed."
                        )

                        approval_id = (
                            security.get(
                                "approval_id"
                            )
                        )

                        # IMPORTANT:
                        # Remember the exact approval
                        # created by this AI interaction.
                        if approval_id:

                            st.session_state[
                                "latest_approval_id"
                            ] = approval_id

                            st.write(
                                "**Approval Request ID**"
                            )

                            st.code(
                                approval_id
                            )

                        st.info(
                            "This action requires a human decision. "
                            "Review the exact request before anything executes."
                        )

                        if approval_id:
                            if st.button(
                                "Review Approval →",
                                key=f"review_approval_{approval_id}",
                                type="primary",
                                use_container_width=True,
                            ):
                                st.session_state["app_page"] = "Approvals"
                                st.rerun()

                        summary = (
                            f"`{tool_name}` requires "
                            f"human approval. Risk "
                            f"level: `{risk_level}`. "
                            f"No protected action "
                            f"was executed."
                        )

                    # -----------------------------------------
                    # BLOCK
                    # -----------------------------------------

                    elif (
                        decision
                        == "BLOCK"
                    ):

                        st.subheader(
                            "3. Enforcement"
                        )

                        st.error(
                            "BLOCKED — Aurelia "
                            "prevented the requested "
                            "action from executing."
                        )

                        reason = (
                            security.get(
                                "error"
                            )
                        )

                        if reason:

                            st.write(
                                "**Security reason:**"
                            )

                            st.write(
                                reason
                            )

                        summary = (
                            f"`{tool_name}` was "
                            f"blocked by the "
                            f"security gateway. "
                            f"No protected action "
                            f"was executed."
                        )

                    else:

                        st.error(
                            "Unexpected security "
                            "decision."
                        )

                        summary = (
                            "The security gateway "
                            "returned an unexpected "
                            "result."
                        )

                    st.session_state[
                        "agent_messages"
                    ].append(
                        {
                            "role": (
                                "assistant"
                            ),
                            "content": summary,
                        }
                    )


# ============================================================
# CLAIMS
# ============================================================

elif page == "Claims":

    st.title(
        "Claims"
    )

    st.caption(
        "Current claims in the Aurelia "
        "insurance environment."
    )

    st.divider()

    claims = get_recent_claims(
        limit=100
    )

    if claims:

        st.dataframe(
            claims,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No claims are currently available."
        )


# ============================================================
# APPROVALS
# ============================================================

elif page == "Approvals":

    st.title(
        "Human Approval Console"
    )

    st.caption(
        "Review high-risk actions requested "
        "by AI agents."
    )

    st.divider()

    st.info(
        "Human approval does not bypass Aurelia. "
        "The original request is integrity-checked "
        "and re-authorized before protected execution."
    )

    # ========================================================
    # APPROVAL OUTCOME / SAFETY INTERLOCK
    # ========================================================

    approval_outcome = (
        st.session_state.get(
            "approval_outcome"
        )
    )

    if approval_outcome:

        outcome_type = (
            approval_outcome.get(
                "type"
            )
        )

        # ----------------------------------------------------
        # APPROVED + EXECUTED
        # ----------------------------------------------------

        if (
            outcome_type
            == "approved"
        ):

            st.success(
                "✓ HIGH-RISK ACTION EXECUTED SUCCESSFULLY"
            )

            st.subheader(
                "Approval Result"
            )

            result1, result2 = (
                st.columns(2)
            )

            with result1:

                st.metric(
                    "Human Approval",
                    "VERIFIED",
                )

                st.metric(
                    "Gateway Re-Authorization",
                    "PASSED",
                )

            with result2:

                st.metric(
                    "Protected Tool",
                    "EXECUTED",
                )

                st.metric(
                    "Approval Status",
                    "EXECUTED",
                )

            tool_name = (
                approval_outcome.get(
                    "tool_name",
                    "Unknown",
                )
            )

            claim_id = (
                approval_outcome.get(
                    "claim_id"
                )
            )

            approval_id = (
                approval_outcome.get(
                    "approval_id"
                )
            )

            st.divider()

            st.write(
                "**Requested Action:**",
                tool_name,
            )

            if claim_id is not None:

                st.write(
                    "**Claim:**",
                    f"#{claim_id}",
                )

            if approval_id:

                st.write(
                    "**Approval ID:**"
                )

                st.code(
                    approval_id
                )

            # -----------------------------------------------
            # Verify actual DB state
            # -----------------------------------------------

            final_claim_status = (
                get_claim_status(
                    claim_id
                )
            )

            if final_claim_status:

                st.success(
                    f"Final claim status: "
                    f"{final_claim_status}"
                )

            execution = (
                approval_outcome.get(
                    "execution"
                )
            )

            if execution:

                with st.expander(
                    "Technical Execution Details"
                ):

                    st.json(
                        execution
                    )

            st.warning(
                "Safety interlock active: no other "
                "approval can be performed from this "
                "screen until you explicitly continue."
            )

            if st.button(
                "Continue to Approvals",
                type="primary",
                use_container_width=True,
            ):

                st.session_state.pop(
                    "approval_outcome",
                    None,
                )

                st.session_state.pop(
                    "latest_approval_id",
                    None,
                )

                st.rerun()

        # ----------------------------------------------------
        # REJECTED
        # ----------------------------------------------------

        elif (
            outcome_type
            == "rejected"
        ):

            st.warning(
                "✕ REQUEST REJECTED"
            )

            st.subheader(
                "Rejection Result"
            )

            result1, result2 = (
                st.columns(2)
            )

            with result1:

                st.metric(
                    "Approval Status",
                    "REJECTED",
                )

            with result2:

                st.metric(
                    "Protected Tool",
                    "NOT EXECUTED",
                )

            tool_name = (
                approval_outcome.get(
                    "tool_name",
                    "Unknown",
                )
            )

            claim_id = (
                approval_outcome.get(
                    "claim_id"
                )
            )

            approval_id = (
                approval_outcome.get(
                    "approval_id"
                )
            )

            st.divider()

            st.write(
                "**Requested Action:**",
                tool_name,
            )

            if claim_id is not None:

                st.write(
                    "**Claim:**",
                    f"#{claim_id}",
                )

            if approval_id:

                st.write(
                    "**Approval ID:**"
                )

                st.code(
                    approval_id
                )

            current_claim_status = (
                get_claim_status(
                    claim_id
                )
            )

            if current_claim_status:

                st.info(
                    f"Current claim status: "
                    f"{current_claim_status}"
                )

            st.info(
                "The protected action was not "
                "executed by this approval request."
            )

            st.warning(
                "Safety interlock active: continue "
                "before reviewing another request."
            )

            if st.button(
                "Continue to Approvals",
                type="primary",
                use_container_width=True,
            ):

                st.session_state.pop(
                    "approval_outcome",
                    None,
                )

                st.session_state.pop(
                    "latest_approval_id",
                    None,
                )

                st.rerun()

    # ========================================================
    # NORMAL APPROVAL CONSOLE
    # ========================================================

    else:

        approvals = (
            get_pending_approvals()
        )

        latest_approval_id = (
            st.session_state.get(
                "latest_approval_id"
            )
        )

        # ====================================================
        # APPROVAL CARD
        # ====================================================

        def render_approval(
            approval,
            highlighted=False,
        ):

            approval_id = (
                approval[
                    "approval_id"
                ]
            )

            tool_name = (
                approval.get(
                    "tool_name",
                    "Unknown",
                )
            )

            arguments = (
                approval.get(
                    "arguments",
                    {},
                )
            )

            claim_id = (
                arguments.get(
                    "claim_id"
                )
            )

            if highlighted:

                st.success(
                    "🔔 NEW REQUEST FROM AI AGENT"
                )

                st.caption(
                    "This is the exact high-risk "
                    "request created by your latest "
                    "AI interaction."
                )

            with st.container(
                border=True
            ):

                header1, header2 = (
                    st.columns(
                        [3, 1]
                    )
                )

                with header1:

                    if (
                        claim_id
                        is not None
                    ):

                        st.subheader(
                            f"Claim #{claim_id}"
                        )

                    else:

                        st.subheader(
                            tool_name
                        )

                    st.write(
                        f"**Action:** "
                        f"`{tool_name}`"
                    )

                with header2:

                    st.warning(
                        "PENDING"
                    )

                st.divider()

                identity1, identity2 = (
                    st.columns(2)
                )

                with identity1:

                    st.write(
                        "**Requested by Agent**"
                    )

                    st.write(
                        approval.get(
                            "agent_id",
                            "Unknown",
                        )
                    )

                    st.write(
                        "**User ID**"
                    )

                    st.write(
                        approval.get(
                            "user_id",
                            "Unknown",
                        )
                    )

                with identity2:

                    st.write(
                        "**User Role**"
                    )

                    st.write(
                        approval.get(
                            "user_role",
                            "Unknown",
                        )
                    )

                    st.write(
                        "**Created**"
                    )

                    st.write(
                        approval.get(
                            "timestamp",
                            "Unknown",
                        )
                    )

                st.write(
                    "**Why Human Review "
                    "Is Required**"
                )

                st.write(
                    approval.get(
                        "reason",
                        (
                            "No reason "
                            "provided."
                        ),
                    )
                )

                # --------------------------------------------
                # Technical details hidden by default
                # --------------------------------------------

                with st.expander(
                    "Technical Request Details"
                ):

                    st.write(
                        "**Approval ID**"
                    )

                    st.code(
                        approval_id
                    )

                    st.write(
                        "**Arguments**"
                    )

                    st.json(
                        arguments
                    )

                    integrity_hash = (
                        approval.get(
                            "integrity_hash"
                        )
                    )

                    if integrity_hash:

                        st.write(
                            "**Integrity Hash**"
                        )

                        st.code(
                            integrity_hash
                        )

                st.divider()

                reject_col, approve_col = (
                    st.columns(2)
                )

                # ============================================
                # REJECT
                # ============================================

                with reject_col:

                    reject_clicked = (
                        st.button(
                            "Reject Request",
                            key=(
                                f"reject_"
                                f"{approval_id}"
                            ),
                            use_container_width=True,
                        )
                    )

                    if reject_clicked:

                        try:

                            rejection = (
                                reject_request(
                                    approval_id
                                )
                            )

                            if rejection.get(
                                "success",
                                False,
                            ):

                                if "agent_messages" not in st.session_state:
                                    st.session_state["agent_messages"] = []

                                st.session_state["agent_messages"].append(
                                    {
                                        "role": "assistant",
                                        "content": (
                                            f"Human review rejected `{tool_name}` for "
                                            f"Claim #{claim_id}. The protected action "
                                            f"was not executed."
                                        ),
                                    }
                                )
                                st.session_state["approval_flash"] = (
                                    f"Claim #{claim_id}: request rejected. No protected action executed."
                                )
                                st.session_state.pop("latest_approval_id", None)
                                st.session_state["app_page"] = "AI Agent"
                                st.rerun()

                            else:

                                st.error(
                                    "The request could "
                                    "not be rejected."
                                )

                                st.json(
                                    rejection
                                )

                        except Exception as error:

                            st.error(
                                "Approval rejection "
                                "failed."
                            )

                            st.code(
                                str(error)
                            )

                # ============================================
                # APPROVE + EXECUTE
                # ============================================

                with approve_col:

                    approve_clicked = (
                        st.button(
                            "Approve & Execute",
                            key=(
                                f"approve_"
                                f"{approval_id}"
                            ),
                            type="primary",
                            use_container_width=True,
                        )
                    )

                    if approve_clicked:

                        try:

                            # --------------------------------
                            # STEP 1:
                            # Human approval.
                            # --------------------------------

                            approved = (
                                approve_request(
                                    approval_id
                                )
                            )

                            if not approved.get(
                                "success",
                                False,
                            ):

                                st.error(
                                    "Human approval "
                                    "could not be "
                                    "recorded."
                                )

                                st.json(
                                    approved
                                )

                            else:

                                # ----------------------------
                                # STEP 2:
                                # Backend verifies approval,
                                # checks integrity,
                                # re-authorizes the request,
                                # then executes only if still
                                # permitted.
                                # ----------------------------

                                execution = (
                                    execute_approved_request(
                                        approval_id
                                    )
                                )

                                if execution.get(
                                    "success",
                                    False,
                                ):

                                    final_status = get_claim_status(claim_id)

                                    if "agent_messages" not in st.session_state:
                                        st.session_state["agent_messages"] = []

                                    completion = (
                                        f"Human approval completed successfully for "
                                        f"Claim #{claim_id}. The protected action "
                                        f"`{tool_name}` was re-authorized and executed."
                                    )

                                    if final_status:
                                        completion += f" Final claim status: `{final_status}`."

                                    st.session_state["agent_messages"].append(
                                        {"role": "assistant", "content": completion}
                                    )

                                    st.session_state["approval_flash"] = (
                                        f"Claim #{claim_id}: approval verified and action executed."
                                    )
                                    st.session_state.pop("approval_outcome", None)
                                    st.session_state.pop("latest_approval_id", None)
                                    st.session_state["app_page"] = "AI Agent"
                                    st.rerun()

                                else:

                                    st.error(
                                        "Human approval "
                                        "was recorded, but "
                                        "secure execution "
                                        "did not complete."
                                    )

                                    st.json(
                                        execution
                                    )

                        except Exception as error:

                            st.error(
                                "Secure approval "
                                "execution failed."
                            )

                            st.code(
                                str(error)
                            )

        # ====================================================
        # EMPTY STATE
        # ====================================================

        if not approvals:

            st.success(
                "There are currently no "
                "pending approvals."
            )

        else:

            # ------------------------------------------------
            # Locate exact latest AI request
            # ------------------------------------------------

            latest_approval = None
            other_approvals = []

            for approval in approvals:

                if (
                    latest_approval_id
                    and approval.get(
                        "approval_id"
                    )
                    == latest_approval_id
                ):

                    latest_approval = (
                        approval
                    )

                else:

                    other_approvals.append(
                        approval
                    )

            # ------------------------------------------------
            # LATEST REQUEST
            # ------------------------------------------------

            if latest_approval:

                st.subheader(
                    "Latest AI Request"
                )

                render_approval(
                    latest_approval,
                    highlighted=True,
                )

                st.divider()

            elif latest_approval_id:

                st.info(
                    "The latest AI approval request "
                    "is no longer pending."
                )

            # ------------------------------------------------
            # OTHER REQUESTS
            # ------------------------------------------------

            st.subheader(
                "Other Pending Requests"
            )

            if other_approvals:

                st.caption(
                    f"{len(other_approvals)} "
                    f"other request(s) are "
                    f"awaiting human review."
                )

                filter_col1, filter_col2 = (
                    st.columns([1, 2])
                )

                with filter_col1:

                    claim_filter = (
                        st.text_input(
                            "Filter by Claim ID",
                            placeholder="e.g. 23",
                        )
                    )

                filtered_approvals = (
                    other_approvals
                )

                if claim_filter.strip():

                    try:

                        filter_claim_id = (
                            int(
                                claim_filter
                            )
                        )

                        filtered_approvals = [
                            approval
                            for approval
                            in other_approvals
                            if (
                                approval.get(
                                    "arguments",
                                    {},
                                ).get(
                                    "claim_id"
                                )
                                == filter_claim_id
                            )
                        ]

                    except ValueError:

                        st.warning(
                            "Claim ID must be "
                            "a number."
                        )

                        filtered_approvals = []

                if filtered_approvals:

                    for approval in (
                        filtered_approvals
                    ):

                        render_approval(
                            approval
                        )

                else:

                    st.info(
                        "No pending approvals "
                        "match that Claim ID."
                    )

            else:

                st.success(
                    "There are no other pending "
                    "approval requests."
                )


# ============================================================
# SECURITY AUDIT
# ============================================================

elif page == "Security Audit":

    st.title("Security Audit")
    st.caption(
        "Tamper-evident record of Aurelia security decisions."
    )
    st.divider()

    audit_result = verify_audit_log()

    # Load the same JSONL file used by src.audit without changing
    # the security backend or the hash-chain implementation.
    audit_file = "data/security_audit.jsonl"
    audit_events = []

    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r", encoding="utf-8") as file:
                for line in file:
                    if not line.strip():
                        continue
                    try:
                        audit_events.append(json.loads(line))
                    except json.JSONDecodeError:
                        # verify_audit_log() will report corruption.
                        pass
        except OSError as error:
            st.error(f"Unable to read the security audit log: {error}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Audit Chain",
            "VALID" if audit_result.get("valid", False) else "INVALID",
        )

    with col2:
        st.metric(
            "Security Events",
            audit_result.get("event_count", 0),
        )

    with col3:
        st.metric(
            "Blocked",
            sum(1 for event in audit_events if event.get("decision") == "BLOCK"),
        )

    with col4:
        st.metric(
            "Human Review",
            sum(
                1
                for event in audit_events
                if event.get("decision") == "HUMAN_REVIEW"
            ),
        )

    if audit_result.get("valid", False):
        st.success(
            "SHA-256 audit hash-chain verification passed across "
            f"{audit_result.get('event_count', 0)} event(s)."
        )
    else:
        st.error(
            audit_result.get(
                "error",
                "Audit integrity verification failed.",
            )
        )

    st.divider()
    st.subheader("Security Event Explorer")

    if not audit_events:
        st.info("No security events have been recorded yet.")

    else:
        # Newest first for investigation convenience.
        events_newest = list(reversed(audit_events))

        decision_values = sorted(
            {str(event.get("decision")) for event in audit_events if event.get("decision")}
        )
        risk_values = sorted(
            {str(event.get("risk_level")) for event in audit_events if event.get("risk_level")}
        )
        tool_values = sorted(
            {str(event.get("tool_name")) for event in audit_events if event.get("tool_name")}
        )

        filter1, filter2, filter3, filter4 = st.columns(4)

        with filter1:
            decision_filter = st.selectbox(
                "Decision",
                ["All"] + decision_values,
                key="audit_decision_filter",
            )

        with filter2:
            risk_filter = st.selectbox(
                "Risk Level",
                ["All"] + risk_values,
                key="audit_risk_filter",
            )

        with filter3:
            tool_filter = st.selectbox(
                "Tool",
                ["All"] + tool_values,
                key="audit_tool_filter",
            )

        with filter4:
            claim_filter = st.text_input(
                "Claim ID",
                placeholder="e.g. 28",
                key="audit_claim_filter",
            )

        filtered_events = []
        invalid_claim_filter = False
        wanted_claim_id = None

        if claim_filter.strip():
            try:
                wanted_claim_id = int(claim_filter.strip())
            except ValueError:
                invalid_claim_filter = True
                st.warning("Claim ID must be a number.")

        if not invalid_claim_filter:
            for event in events_newest:
                if decision_filter != "All" and event.get("decision") != decision_filter:
                    continue
                if risk_filter != "All" and event.get("risk_level") != risk_filter:
                    continue
                if tool_filter != "All" and event.get("tool_name") != tool_filter:
                    continue

                event_claim_id = (event.get("arguments") or {}).get("claim_id")
                if wanted_claim_id is not None and event_claim_id != wanted_claim_id:
                    continue

                filtered_events.append(event)

        st.caption(
            f"Showing {len(filtered_events)} of {len(audit_events)} loaded event(s). "
            "Newest events appear first."
        )

        table_rows = []
        for event in filtered_events:
            arguments = event.get("arguments") or {}
            table_rows.append(
                {
                    "Time": event.get("timestamp"),
                    "Event": event.get("event_type"),
                    "Decision": event.get("decision"),
                    "Risk": event.get("risk_level"),
                    "Tool": event.get("tool_name"),
                    "Claim": arguments.get("claim_id"),
                    "User": event.get("user_id"),
                    "Role": event.get("user_role"),
                    "Executed": event.get("executed"),
                    "ML Risk": event.get("ml_risk_probability"),
                    "ML Band": event.get("ml_risk_band"),
                }
            )

        if table_rows:
            st.dataframe(
                table_rows,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No security events match the selected filters.")

        st.divider()
        st.subheader("Event Details")
        st.caption(
            "Expand an event to inspect the authorization reason, arguments, "
            "ML metadata, approval linkage and hash-chain evidence."
        )

        for index, event in enumerate(filtered_events):
            arguments = event.get("arguments") or {}
            claim_id = arguments.get("claim_id")
            claim_label = f"Claim #{claim_id}" if claim_id is not None else "No claim"
            label = (
                f"{event.get('decision', 'UNKNOWN')} · "
                f"{event.get('tool_name', 'Unknown')} · "
                f"{claim_label} · {event.get('timestamp', 'Unknown time')}"
            )

            with st.expander(label):
                detail1, detail2 = st.columns(2)

                with detail1:
                    st.write("**Event Type:**", event.get("event_type", "Unknown"))
                    st.write("**Decision:**", event.get("decision", "Unknown"))
                    st.write("**Risk Level:**", event.get("risk_level", "Unknown"))
                    st.write("**Executed:**", event.get("executed", False))
                    st.write("**Tool:**", event.get("tool_name", "Unknown"))
                    st.write("**Agent:**", event.get("agent_id", "Unknown"))

                with detail2:
                    st.write("**User ID:**", event.get("user_id", "Unknown"))
                    st.write("**User Role:**", event.get("user_role", "Unknown"))
                    st.write("**ML Risk:**", event.get("ml_risk_probability", "N/A"))
                    st.write("**ML Band:**", event.get("ml_risk_band", "N/A"))
                    st.write("**ML Escalated:**", event.get("ml_escalated", "N/A"))
                    st.write("**Approval ID:**", event.get("approval_id", "N/A"))

                st.write("**Authorization Reason**")
                st.write(event.get("reason", "No reason recorded."))

                st.write("**Arguments**")
                st.json(arguments)

                st.write("**Event ID**")
                st.code(event.get("event_id", "N/A"))

                st.write("**Previous Hash**")
                st.code(event.get("previous_hash") or "GENESIS / NONE")

                st.write("**Integrity Hash**")
                st.code(event.get("integrity_hash", "N/A"))
