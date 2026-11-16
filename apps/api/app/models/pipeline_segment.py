"""
SQLAlchemy Pipeline Segment Model
Stores pipeline route metadata and GeoJSON coordinates (PostGIS ready).
"""
from sqlalchemy import Column, String, Float, Integer, Text, Boolean

from app.database.session import Base


class PipelineSegmentModel(Base):
    __tablename__ = "pipeline_segments"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    category_label = Column(String(128), default="")
    material = Column(String(128), default="")
    diameter_mm = Column(Integer, default=300)
    length_m = Column(Float, default=1000.0)
    operational_status = Column(String(64), default="Active - Pressurized")
    inspection_status = Column(String(64), default="Operational")
    pressure_zone_id = Column(String(64), default="PZ-01", index=True)
    pressure_zone_name = Column(String(128), default="")
    nominal_pressure_psi = Column(Float, default=60.0)

    # Serialized JSON of coordinates [[lon, lat], ...]
    coordinates_json = Column(Text, nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)

