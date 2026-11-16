"""Task 19: Unified Incidents, Workflow Events, and Approvals schema

Revision ID: d210495f6a3b
Revises: c109384e5f2a
Create Date: 2026-11-16 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd210495f6a3b'
down_revision: Union[str, Sequence[str], None] = 'c109384e5f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. unified_incidents
    op.create_table(
        'unified_incidents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_code', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=False, default="ACOUSTIC_ANOMALY"),
        sa.Column('severity', sa.String(length=32), nullable=False, default="HIGH"),
        sa.Column('priority', sa.String(length=32), nullable=False, default="P1"),
        sa.Column('lifecycle_status', sa.String(length=64), nullable=False, default="DETECTED"),
        sa.Column('pipeline_segment_id', sa.String(length=64), nullable=False),
        sa.Column('dma_zone', sa.String(length=64), nullable=True, default="DMA-CENTRAL-01"),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('detection_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('detection_source', sa.String(length=64), nullable=True, default="TELEMETRY_ACOUSTIC"),
        sa.Column('sensor_ids_json', sa.Text(), nullable=True, default="[]"),
        sa.Column('ai_leak_probability', sa.Float(), nullable=False, default=0.0),
        sa.Column('ai_confidence', sa.Float(), nullable=False, default=0.0),
        sa.Column('evidence_provenance', sa.String(length=32), nullable=False, default="SIMULATED"),
        sa.Column('hydraulic_headloss_delta', sa.Float(), nullable=False, default=0.0),
        sa.Column('estimated_loss_lps', sa.Float(), nullable=False, default=0.0),
        sa.Column('risk_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('inspection_mission_id', sa.String(length=64), nullable=True),
        sa.Column('assigned_rover_id', sa.String(length=64), nullable=True),
        sa.Column('inspection_findings_json', sa.Text(), nullable=True),
        sa.Column('repair_plan_id', sa.String(length=64), nullable=True),
        sa.Column('repair_cost_estimate', sa.Float(), nullable=True),
        sa.Column('repair_urgency', sa.String(length=32), nullable=True),
        sa.Column('simulation_resolution_data_json', sa.Text(), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('is_simulated', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_by', sa.String(length=128), nullable=True, default="SYSTEM_AI_ENGINE"),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_unified_incidents_id'), 'unified_incidents', ['id'], unique=False)
    op.create_index(op.f('ix_unified_incidents_incident_code'), 'unified_incidents', ['incident_code'], unique=True)
    op.create_index(op.f('ix_unified_incidents_category'), 'unified_incidents', ['category'], unique=False)
    op.create_index(op.f('ix_unified_incidents_severity'), 'unified_incidents', ['severity'], unique=False)
    op.create_index(op.f('ix_unified_incidents_priority'), 'unified_incidents', ['priority'], unique=False)
    op.create_index(op.f('ix_unified_incidents_lifecycle_status'), 'unified_incidents', ['lifecycle_status'], unique=False)
    op.create_index(op.f('ix_unified_incidents_pipeline_segment_id'), 'unified_incidents', ['pipeline_segment_id'], unique=False)
    op.create_index(op.f('ix_unified_incidents_dma_zone'), 'unified_incidents', ['dma_zone'], unique=False)
    op.create_index(op.f('ix_unified_incidents_inspection_mission_id'), 'unified_incidents', ['inspection_mission_id'], unique=False)
    op.create_index(op.f('ix_unified_incidents_assigned_rover_id'), 'unified_incidents', ['assigned_rover_id'], unique=False)
    op.create_index(op.f('ix_unified_incidents_repair_plan_id'), 'unified_incidents', ['repair_plan_id'], unique=False)
    op.create_index(op.f('ix_unified_incidents_created_at'), 'unified_incidents', ['created_at'], unique=False)

    # 2. incident_workflow_events
    op.create_table(
        'incident_workflow_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_id', sa.String(length=64), sa.ForeignKey('unified_incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_status', sa.String(length=64), nullable=False),
        sa.Column('to_status', sa.String(length=64), nullable=False),
        sa.Column('stage_number', sa.Integer(), nullable=False, default=1),
        sa.Column('actor_id', sa.String(length=128), nullable=True, default="SYSTEM"),
        sa.Column('actor_role', sa.String(length=64), nullable=True, default="SYSTEM"),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True, default=""),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_incident_workflow_events_id'), 'incident_workflow_events', ['id'], unique=False)
    op.create_index(op.f('ix_incident_workflow_events_incident_id'), 'incident_workflow_events', ['incident_id'], unique=False)
    op.create_index(op.f('ix_incident_workflow_events_timestamp'), 'incident_workflow_events', ['timestamp'], unique=False)

    # 3. incident_approvals
    op.create_table(
        'incident_approvals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_id', sa.String(length=64), sa.ForeignKey('unified_incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('approval_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, default="PENDING"),
        sa.Column('requested_by', sa.String(length=128), nullable=True, default="SYSTEM"),
        sa.Column('approved_by', sa.String(length=128), nullable=True),
        sa.Column('approver_role', sa.String(length=64), nullable=True),
        sa.Column('decision_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True, default=""),
        sa.Column('digital_signature', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_incident_approvals_id'), 'incident_approvals', ['id'], unique=False)
    op.create_index(op.f('ix_incident_approvals_incident_id'), 'incident_approvals', ['incident_id'], unique=False)
    op.create_index(op.f('ix_incident_approvals_approval_type'), 'incident_approvals', ['approval_type'], unique=False)
    op.create_index(op.f('ix_incident_approvals_status'), 'incident_approvals', ['status'], unique=False)
    op.create_index(op.f('ix_incident_approvals_created_at'), 'incident_approvals', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('incident_approvals')
    op.drop_table('incident_workflow_events')
    op.drop_table('unified_incidents')

