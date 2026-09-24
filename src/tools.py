from .database import SessionLocal
from .models import (
    Customer,
    Policy,
    Claim,
    Document
)


# ============================================================
# TOOL 1: GET CUSTOMER
# ============================================================

def get_customer(customer_id):
    """
    Retrieve basic information about a customer.
    """

    session = SessionLocal()

    try:

        customer = (
            session.query(Customer)
            .filter(
                Customer.customer_id == customer_id
            )
            .first()
        )

        if not customer:
            return {
                "success": False,
                "error": "Customer not found"
            }

        return {
            "success": True,
            "customer": {
                "customer_id": customer.customer_id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "address": customer.address,
                "date_of_birth": customer.date_of_birth
            }
        }

    finally:
        session.close()


# ============================================================
# TOOL 2: GET POLICY
# ============================================================

def get_policy(policy_id):
    """
    Retrieve information about an insurance policy.
    """

    session = SessionLocal()

    try:

        policy = (
            session.query(Policy)
            .filter(
                Policy.policy_id == policy_id
            )
            .first()
        )

        if not policy:
            return {
                "success": False,
                "error": "Policy not found"
            }

        return {
            "success": True,
            "policy": {
                "policy_id": policy.policy_id,
                "customer_id": policy.customer_id,
                "policy_type": policy.policy_type,
                "status": policy.status,
                "coverage": policy.coverage,
                "excess": policy.excess,
                "coverage_limit": policy.coverage_limit,
                "start_date": policy.start_date,
                "end_date": policy.end_date
            }
        }

    finally:
        session.close()


# ============================================================
# TOOL 3: GET CLAIM
# ============================================================

def get_claim(claim_id):
    """
    Retrieve information about an insurance claim.
    """

    session = SessionLocal()

    try:

        claim = (
            session.query(Claim)
            .filter(
                Claim.claim_id == claim_id
            )
            .first()
        )

        if not claim:
            return {
                "success": False,
                "error": "Claim not found"
            }

        return {
            "success": True,
            "claim": {
                "claim_id": claim.claim_id,
                "customer_id": claim.customer_id,
                "policy_id": claim.policy_id,
                "event_type": claim.event_type,
                "event_date": claim.event_date,
                "description": claim.description,
                "estimated_damage": claim.estimated_damage,
                "status": claim.status,
                "priority": claim.priority,
                "created_at": (
                    claim.created_at.isoformat()
                    if claim.created_at
                    else None
                )
            }
        }

    finally:
        session.close()


# ============================================================
# TOOL 4: GET CLAIM DOCUMENTS
# ============================================================

def get_claim_documents(claim_id):
    """
    Retrieve documents associated with a claim.
    """

    session = SessionLocal()

    try:

        documents = (
            session.query(Document)
            .filter(
                Document.claim_id == claim_id
            )
            .all()
        )

        results = []

        for document in documents:

            results.append({
                "document_id": document.document_id,
                "claim_id": document.claim_id,
                "document_type": document.document_type,
                "content": document.content,
                "sensitivity": document.sensitivity,
                "trusted_source": document.trusted_source,
                "created_at": (
                    document.created_at.isoformat()
                    if document.created_at
                    else None
                )
            })

        return {
            "success": True,
            "claim_id": claim_id,
            "document_count": len(results),
            "documents": results
        }

    finally:
        session.close()


# ============================================================
# TOOL 5: GET CLAIM HISTORY
# ============================================================

def get_claim_history(customer_id):
    """
    Retrieve all claims associated with a customer.
    """

    session = SessionLocal()

    try:

        claims = (
            session.query(Claim)
            .filter(
                Claim.customer_id == customer_id
            )
            .all()
        )

        results = []

        for claim in claims:

            results.append({
                "claim_id": claim.claim_id,
                "policy_id": claim.policy_id,
                "event_type": claim.event_type,
                "event_date": claim.event_date,
                "estimated_damage": claim.estimated_damage,
                "status": claim.status,
                "priority": claim.priority
            })

        return {
            "success": True,
            "customer_id": customer_id,
            "claim_count": len(results),
            "claims": results
        }

    finally:
        session.close()

# ============================================================
# TOOL 6: APPROVE SETTLEMENT
# ============================================================

def approve_settlement(claim_id):
    """
    Approve settlement for a claim.

    This function performs business validation in addition
    to the security gateway authorization.

    Security authorization should still happen BEFORE this
    function is called.
    """

    db = SessionLocal()

    try:
        claim = db.query(Claim).filter(
            Claim.claim_id == claim_id
        ).first()

        if claim is None:
            return {
                "success": False,
                "error": f"Claim {claim_id} not found."
            }

        # Prevent duplicate settlement approval
        if claim.status == "SETTLEMENT_APPROVED":
            return {
                "success": False,
                "error": (
                    f"Claim {claim_id} has already been "
                    "approved for settlement."
                )
            }

        # Settlement approval is only valid from settlement review
        if claim.status != "SETTLEMENT_REVIEW":
            return {
                "success": False,
                "error": (
                    f"Claim {claim_id} cannot be approved for "
                    f"settlement from status '{claim.status}'."
                )
            }

        # Perform state transition
        claim.status = "SETTLEMENT_APPROVED"

        db.commit()
        db.refresh(claim)

        return {
            "success": True,
            "claim_id": claim.claim_id,
            "status": claim.status,
            "message": (
                f"Claim {claim_id} approved for settlement."
            )
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close()