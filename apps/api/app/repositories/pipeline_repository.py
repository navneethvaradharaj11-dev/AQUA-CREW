"""
Pipeline Segment Repository
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.models.pipeline_segment import PipelineSegmentModel

DEFAULT_PIPELINES = [
    {
        "id": "PIPE-SEC-4B-92",
        "name": "Metro Central Main Trunk Line B",
        "category": "primary",
        "category_label": "Primary Trunk Main",
        "material": "Ductile Iron (Class 54)",
        "diameter_mm": 600,
        "length_m": 1850.0,
        "operational_status": "Active - Pressurized",
        "inspection_status": "Leak Suspected",
        "pressure_zone_id": "PZ-01",
        "pressure_zone_name": "Metro Central High-Pressure",
        "nominal_pressure_psi": 65.0,
        "coordinates": [
            [-74.0150, 40.7100],
            [-74.0110, 40.7115],
            [-74.0060, 40.7128],
            [-74.0010, 40.7140],
            [-73.9960, 40.7155],
        ],
    },
    {
        "id": "PIPE-SEC-4A-10",
        "name": "Grand Avenue Spine Trunk Line A",
        "category": "primary",
        "category_label": "Primary Trunk Main",
        "material": "Pre-stressed Concrete Cylinder",
        "diameter_mm": 750,
        "length_m": 2100.0,
        "operational_status": "Active - Pressurized",
        "inspection_status": "Inspected - Verified",
        "pressure_zone_id": "PZ-01",
        "pressure_zone_name": "Metro Central High-Pressure",
        "nominal_pressure_psi": 68.0,
        "coordinates": [
            [-74.0060, 40.7040],
            [-74.0060, 40.7128],
            [-74.0060, 40.7220],
        ],
    },
    {
        "id": "PIPE-IND-1A-04",
        "name": "Industrial Park Feeder Line 1",
        "category": "secondary",
        "category_label": "Secondary Feeder",
        "material": "High-Density Polyethylene (HDPE)",
        "diameter_mm": 400,
        "length_m": 820.0,
        "operational_status": "Active - Pressurized",
        "inspection_status": "Rover Patrol Active",
        "pressure_zone_id": "PZ-02",
        "pressure_zone_name": "Eastern Industrial Sector",
        "nominal_pressure_psi": 60.0,
        "coordinates": [
            [-74.0060, 40.7128],
            [-74.0035, 40.7135],
            [-74.0021, 40.7145],
            [-73.9980, 40.7160],
        ],
    },
    {
        "id": "PIPE-RES-3C-11",
        "name": "Pinecrest Residential Sub-Branch",
        "category": "secondary",
        "category_label": "Secondary Feeder",
        "material": "Ductile Iron",
        "diameter_mm": 350,
        "length_m": 940.0,
        "operational_status": "Active - Pressurized",
        "inspection_status": "Inspection Due",
        "pressure_zone_id": "PZ-03",
        "pressure_zone_name": "Northern Residential Zone",
        "nominal_pressure_psi": 52.0,
        "coordinates": [
            [-74.0060, 40.7220],
            [-74.0089, 40.7198],
            [-74.0130, 40.7180],
        ],
    },
    {
        "id": "PIPE-HRB-02-19",
        "name": "Harbor Marginal Service Line",
        "category": "distribution",
        "category_label": "Distribution Main",
        "material": "Cast Iron (Epoxy Lined)",
        "diameter_mm": 250,
        "length_m": 780.0,
        "operational_status": "Active - Pressurized",
        "inspection_status": "Inspected - Verified",
        "pressure_zone_id": "PZ-04",
        "pressure_zone_name": "Harbor Utility Terminal",
        "nominal_pressure_psi": 58.0,
        "coordinates": [
            [-74.0060, 40.7040],
            [-74.0100, 40.7065],
            [-74.0115, 40.7091],
            [-74.0140, 40.7110],
        ],
    },
]


class PipelineRepository:
    @staticmethod
    def get_all(db: Session) -> List[PipelineSegmentModel]:
        return db.query(PipelineSegmentModel).all()

    @staticmethod
    def get_by_id(db: Session, segment_id: str) -> Optional[PipelineSegmentModel]:
        return db.query(PipelineSegmentModel).filter(PipelineSegmentModel.id == segment_id).first()

    @staticmethod
    def seed_defaults(db: Session) -> None:
        if db.query(PipelineSegmentModel).count() == 0:
            for p in DEFAULT_PIPELINES:
                model = PipelineSegmentModel(
                    id=p["id"],
                    name=p["name"],
                    category=p["category"],
                    category_label=p["category_label"],
                    material=p["material"],
                    diameter_mm=p["diameter_mm"],
                    length_m=p["length_m"],
                    operational_status=p["operational_status"],
                    inspection_status=p["inspection_status"],
                    pressure_zone_id=p["pressure_zone_id"],
                    pressure_zone_name=p["pressure_zone_name"],
                    nominal_pressure_psi=p["nominal_pressure_psi"],
                    coordinates_json=json.dumps(p["coordinates"]),
                    is_simulated=True,
                )
                db.add(model)
            db.commit()

