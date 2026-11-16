"""Task 18: IoT device ecosystem, credentials, calibrations, and telemetry

Revision ID: c109384e5f2a
Revises: b098296b862e
Create Date: 2026-11-16 19:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c109384e5f2a'
down_revision: Union[str, Sequence[str], None] = 'b098296b862e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. iot_devices
    op.create_table(
        'iot_devices',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('device_type', sa.String(length=64), nullable=False),
        sa.Column('manufacturer', sa.String(length=128), default="AQUA CREW Lab / Nordic"),
        sa.Column('hardware_model', sa.String(length=64), default="ESP32-S3-WROOM"),
        sa.Column('firmware_version', sa.String(length=32), default="v1.4.0-sim"),
        sa.Column('hardware_revision', sa.String(length=32), default="revB.2"),
        sa.Column('installation_location', sa.String(length=255), default=""),
        sa.Column('pipeline_segment_id', sa.String(length=64), nullable=True),
        sa.Column('dma_zone', sa.String(length=64), default="DMA-METRO-CENTRAL"),
        sa.Column('latitude', sa.Float(), nullable=False, default=40.7128),
        sa.Column('longitude', sa.Float(), nullable=False, default=-74.0060),
        sa.Column('elevation_m', sa.Float(), default=12.5),
        sa.Column('supported_sensor_types', sa.JSON(), default=list),
        sa.Column('communication_protocol', sa.String(length=32), default="MQTT"),
        sa.Column('status', sa.String(length=32), default="REGISTERED"),
        sa.Column('last_communication_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calibration_status', sa.String(length=32), default="CALIBRATED"),
        sa.Column('calibration_metadata', sa.JSON(), default=dict),
        sa.Column('maintenance_history', sa.JSON(), default=list),
        sa.Column('auth_status', sa.String(length=32), default="AUTHENTICATED"),
        sa.Column('is_simulated', sa.Boolean(), nullable=False, default=True),
        sa.Column('owner_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_iot_devices_id'), 'iot_devices', ['id'], unique=False)
    op.create_index(op.f('ix_iot_devices_device_type'), 'iot_devices', ['device_type'], unique=False)
    op.create_index(op.f('ix_iot_devices_pipeline_segment_id'), 'iot_devices', ['pipeline_segment_id'], unique=False)
    op.create_index(op.f('ix_iot_devices_dma_zone'), 'iot_devices', ['dma_zone'], unique=False)
    op.create_index(op.f('ix_iot_devices_status'), 'iot_devices', ['status'], unique=False)
    op.create_index(op.f('ix_iot_devices_calibration_status'), 'iot_devices', ['calibration_status'], unique=False)

    # 2. device_credentials
    op.create_table(
        'device_credentials',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('device_id', sa.String(length=64), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('credential_type', sa.String(length=32), default="API_KEY"),
        sa.Column('key_prefix', sa.String(length=32), nullable=False),
        sa.Column('hashed_secret', sa.String(length=255), nullable=False),
        sa.Column('allowed_topics', sa.JSON(), default=list),
        sa.Column('revoked', sa.Boolean(), default=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.String(length=255), nullable=True),
        sa.Column('last_rotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_device_credentials_id'), 'device_credentials', ['id'], unique=False)
    op.create_index(op.f('ix_device_credentials_device_id'), 'device_credentials', ['device_id'], unique=False)

    # 3. sensors
    op.create_table(
        'sensors',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('device_id', sa.String(length=64), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sensor_type', sa.String(length=32), nullable=False),
        sa.Column('measurement_unit', sa.String(length=16), nullable=False),
        sa.Column('min_range', sa.Float(), default=0.0),
        sa.Column('max_range', sa.Float(), default=100.0),
        sa.Column('accuracy_tolerance', sa.Float(), default=0.05),
        sa.Column('sampling_rate_hz', sa.Float(), default=1.0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('latest_reading_value', sa.Float(), nullable=True),
        sa.Column('latest_reading_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_sensors_id'), 'sensors', ['id'], unique=False)
    op.create_index(op.f('ix_sensors_device_id'), 'sensors', ['device_id'], unique=False)
    op.create_index(op.f('ix_sensors_sensor_type'), 'sensors', ['sensor_type'], unique=False)

    # 4. sensor_calibrations
    op.create_table(
        'sensor_calibrations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('sensor_id', sa.String(length=64), nullable=False),
        sa.Column('device_id', sa.String(length=64), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('calibration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_calibration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('calibration_method', sa.String(length=64), default="HYDRAULIC_REFERENCE_COMPARISON"),
        sa.Column('calibration_reference', sa.String(length=128), default="STD-REF-FLOW-A109"),
        sa.Column('calibration_result', sa.String(length=32), default="PASS"),
        sa.Column('accuracy_tolerance', sa.Float(), default=0.05),
        sa.Column('technician', sa.String(length=128), default="Chief Hydraulic Calibration Technician"),
        sa.Column('certificate_reference', sa.String(length=128), default="ISO-17025-AQUA-8819"),
        sa.Column('calibration_status', sa.String(length=32), default="CALIBRATED"),
        sa.Column('notes', sa.Text(), default=""),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_sensor_calibrations_id'), 'sensor_calibrations', ['id'], unique=False)
    op.create_index(op.f('ix_sensor_calibrations_sensor_id'), 'sensor_calibrations', ['sensor_id'], unique=False)
    op.create_index(op.f('ix_sensor_calibrations_device_id'), 'sensor_calibrations', ['device_id'], unique=False)
    op.create_index(op.f('ix_sensor_calibrations_next_due_date'), 'sensor_calibrations', ['next_due_date'], unique=False)

    # 5. device_telemetries
    op.create_table(
        'device_telemetries',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('device_id', sa.String(length=64), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sensor_id', sa.String(length=64), nullable=False),
        sa.Column('sensor_type', sa.String(length=32), nullable=False),
        sa.Column('measurement_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=16), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), default=1),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=32), default="VALID"),
        sa.Column('provenance', sa.String(length=32), default="MEASURED"),
        sa.Column('firmware_version', sa.String(length=32), default=""),
        sa.Column('calibration_reference', sa.String(length=128), default=""),
        sa.Column('pipeline_segment_id', sa.String(length=64), default=""),
        sa.Column('is_simulated', sa.Boolean(), default=True),
    )
    op.create_index(op.f('ix_device_telemetries_id'), 'device_telemetries', ['id'], unique=False)
    op.create_index(op.f('ix_device_telemetries_device_id'), 'device_telemetries', ['device_id'], unique=False)
    op.create_index(op.f('ix_device_telemetries_timestamp'), 'device_telemetries', ['timestamp'], unique=False)
    op.create_index(op.f('ix_device_telemetries_data_quality'), 'device_telemetries', ['data_quality'], unique=False)

    # 6. device_events
    op.create_table(
        'device_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('device_id', sa.String(length=64), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=16), default="INFO"),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('details', sa.JSON(), default=dict),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_device_events_id'), 'device_events', ['id'], unique=False)
    op.create_index(op.f('ix_device_events_device_id'), 'device_events', ['device_id'], unique=False)

    # 7. device_connections
    op.create_table(
        'device_connections',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('device_id', sa.String(length=64), sa.ForeignKey('iot_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('protocol', sa.String(length=32), default="MQTT"),
        sa.Column('ip_address', sa.String(length=45), default="127.0.0.1"),
        sa.Column('connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('messages_received', sa.Integer(), default=0),
        sa.Column('messages_sent', sa.Integer(), default=0),
        sa.Column('bytes_received', sa.Integer(), default=0),
        sa.Column('status', sa.String(length=32), default="CONNECTED"),
        sa.Column('disconnect_reason', sa.String(length=255), nullable=True),
    )
    op.create_index(op.f('ix_device_connections_id'), 'device_connections', ['id'], unique=False)
    op.create_index(op.f('ix_device_connections_device_id'), 'device_connections', ['device_id'], unique=False)

    # 8. device_audit_logs
    op.create_table(
        'device_audit_logs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('device_id', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('actor', sa.String(length=128), default="system"),
        sa.Column('status', sa.String(length=32), default="SUCCESS"),
        sa.Column('ip_address', sa.String(length=45), default="127.0.0.1"),
        sa.Column('details', sa.JSON(), default=dict),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_device_audit_logs_id'), 'device_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_device_audit_logs_device_id'), 'device_audit_logs', ['device_id'], unique=False)

    # 9. telemetry_processing_results
    op.create_table(
        'telemetry_processing_results',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('batch_id', sa.String(length=64), default=""),
        sa.Column('device_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), default="ACCEPTED"),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('processing_latency_ms', sa.Float(), default=0.0),
        sa.Column('routed_to_ai_leak', sa.Boolean(), default=False),
        sa.Column('routed_to_digital_twin', sa.Boolean(), default=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_telemetry_processing_results_id'), 'telemetry_processing_results', ['id'], unique=False)
    op.create_index(op.f('ix_telemetry_processing_results_device_id'), 'telemetry_processing_results', ['device_id'], unique=False)


def downgrade() -> None:
    op.drop_table('telemetry_processing_results')
    op.drop_table('device_audit_logs')
    op.drop_table('device_connections')
    op.drop_table('device_events')
    op.drop_table('device_telemetries')
    op.drop_table('sensor_calibrations')
    op.drop_table('sensors')
    op.drop_table('device_credentials')
    op.drop_table('iot_devices')

