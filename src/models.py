from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text
)

from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    address = Column(String)
    date_of_birth = Column(String)


class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    policy_type = Column(String)
    status = Column(String)
    coverage = Column(String)
    excess = Column(Float)
    coverage_limit = Column(Float)
    start_date = Column(String)
    end_date = Column(String)


class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    policy_id = Column(Integer, ForeignKey("policies.policy_id"))

    event_type = Column(String)
    event_date = Column(String)

    description = Column(Text)

    estimated_damage = Column(Float)

    status = Column(String)
    priority = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
class ClaimAssignment(Base):
    __tablename__ = "claim_assignments"

    assignment_id = Column(
        Integer,
        primary_key=True
    )

    claim_id = Column(
        Integer,
        ForeignKey("claims.claim_id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False
    )

    assigned_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    active = Column(
        Boolean,
        default=True
    )




class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True)

    claim_id = Column(
        Integer,
        ForeignKey("claims.claim_id")
    )

    document_type = Column(String)

    content = Column(Text)

    sensitivity = Column(String)

    trusted_source = Column(Boolean, default=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)

    role = Column(String)

    department = Column(String)

    status = Column(String)


class AgentAction(Base):
    __tablename__ = "agent_actions"

    action_id = Column(Integer, primary_key=True)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    agent_id = Column(String)

    user_id = Column(Integer)

    claim_id = Column(Integer)

    action_type = Column(String)

    target = Column(String)

    risk_score = Column(Float)

    decision = Column(String)

    reason = Column(Text)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    event_id = Column(Integer, primary_key=True)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    event_type = Column(String)

    severity = Column(String)

    description = Column(Text)

    action_id = Column(Integer)

    resolved = Column(Boolean, default=False)