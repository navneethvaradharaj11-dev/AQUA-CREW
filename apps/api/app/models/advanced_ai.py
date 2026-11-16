"""
SQLAlchemy Persistent Models for Advanced AI & Decision Intelligence (Task 13)
Stores conversation sessions, message exchanges with grounded evidence references,
and tamper-evident interaction audits.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from datetime import datetime, timezone
import uuid

from app.database.session import Base


class AIConversationModel(Base):
    __tablename__ = "ai_conversations"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    user_id = Column(String(128), default="OPERATOR-SUPERVISOR-01", index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class AIMessageModel(Base):
    __tablename__ = "ai_messages"

    id = Column(String(64), primary_key=True, index=True)
    conversation_id = Column(String(64), ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False, index=True)  # user, assistant, system
    content = Column(Text, nullable=False)
    intent = Column(String(64), nullable=True, index=True)
    
    # Model & provider provenance
    model_used = Column(String(128), default="deterministic-grounded-engine", nullable=False)
    provider_used = Column(String(64), default="DETERMINISTIC", nullable=False)
    
    # Grounding & safety validation
    evidence_references_json = Column(Text, default="[]", nullable=False)  # List of evidence IDs cited
    validation_status = Column(String(32), default="VALIDATED", index=True)  # VALIDATED, UNVALIDATED, FLAGGED
    uncertainty_description = Column(String(256), nullable=True)
    token_usage_json = Column(Text, nullable=True)

    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class AIResponseEvidenceModel(Base):
    __tablename__ = "ai_response_evidences"

    id = Column(String(64), primary_key=True, index=True)
    message_id = Column(String(64), ForeignKey("ai_messages.id"), nullable=False, index=True)
    evidence_id = Column(String(64), nullable=False, index=True)
    source_module = Column(String(64), nullable=False)  # TASK_07, TASK_09, TASK_10, TASK_11, TASK_12, TASK_05
    source_table = Column(String(64), nullable=False)
    source_record_id = Column(String(64), nullable=False, index=True)
    evidence_type = Column(String(64), nullable=False)
    evidence_classification = Column(String(32), nullable=False)  # MEASURED, SIMULATED, DERIVED, PREDICTED, OPERATOR_ENTERED, UNKNOWN
    claim_supported = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.85)

    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class AIInteractionAuditModel(Base):
    __tablename__ = "ai_interaction_audits"

    id = Column(String(64), primary_key=True, index=True)
    conversation_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(128), default="OPERATOR-SUPERVISOR-01", index=True)
    query_text = Column(Text, nullable=False)
    response_summary = Column(Text, nullable=False)
    retrieved_record_count = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    provider_status = Column(String(64), default="DETERMINISTIC_OK")
    prompt_injection_flag = Column(Boolean, default=False, nullable=False, index=True)
    
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)

