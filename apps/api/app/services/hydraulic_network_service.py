"""
Hydraulic Network Service (Task 10)
Manages hydraulic networks, nodes, and links, seeding default municipal networks
and mapping GIS pipeline segments to hydraulic simulation topologies.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timezone

from app.models.digital_twin import (
    HydraulicNetworkModel,
    HydraulicNodeModel,
    HydraulicLinkModel,
)
from app.services.hydraulic_engine.network_adapter import NetworkAdapter


DEFAULT_NETWORK_ID = "NET-METRO-01"

DEFAULT_NODES = [
    {
        "id": "NODE-RES-01",
        "name": "Northern Aqueduct Supply Reservoir R1",
        "node_type": "RESERVOIR",
        "elevation_m": 25.0,
        "base_head_m": 85.0,
        "base_demand_lps": 0.0,
        "emitter_coeff": 0.0,
        "min_pressure_bar": 2.0,
        "nominal_pressure_bar": 5.8,
        "longitude": -74.0060,
        "latitude": 40.7220,
    },
    {
        "id": "NODE-JUNC-01",
        "name": "Central Grand Avenue Spine Junction J1",
        "node_type": "JUNCTION",
        "elevation_m": 16.5,
        "base_demand_lps": 22.0,
        "emitter_coeff": 0.0,
        "min_pressure_bar": 1.5,
        "nominal_pressure_bar": 4.5,
        "longitude": -74.0060,
        "latitude": 40.7128,
    },
    {
        "id": "NODE-JUNC-02",
        "name": "Metro Central Commercial Distribution Node J2",
        "node_type": "JUNCTION",
        "elevation_m": 14.0,
        "base_demand_lps": 18.5,
        "emitter_coeff": 0.0,
        "min_pressure_bar": 1.5,
        "nominal_pressure_bar": 4.2,
        "longitude": -74.0110,
        "latitude": 40.7115,
    },
    {
        "id": "NODE-JUNC-03",
        "name": "Western Harbor Perimeter Junction J3",
        "node_type": "JUNCTION",
        "elevation_m": 8.0,
        "base_demand_lps": 12.0,
        "emitter_coeff": 0.0,
        "min_pressure_bar": 1.5,
        "nominal_pressure_bar": 4.0,
        "longitude": -74.0150,
        "latitude": 40.7100,
    },
    {
        "id": "NODE-JUNC-04",
        "name": "Eastern Industrial Sector Node J4",
        "node_type": "JUNCTION",
        "elevation_m": 18.0,
        "base_demand_lps": 28.0,
        "emitter_coeff": 0.0,
        "min_pressure_bar": 1.5,
        "nominal_pressure_bar": 4.1,
        "longitude": -74.0021,
        "latitude": 40.7145,
    },
    {
        "id": "NODE-TANK-01",
        "name": "Industrial Park Elevated Storage Tank T1",
        "node_type": "TANK",
        "elevation_m": 24.0,
        "base_head_m": None,
        "initial_level_m": 6.5,
        "min_level_m": 1.5,
        "max_level_m": 12.0,
        "diameter_m": 18.0,
        "base_demand_lps": 0.0,
        "emitter_coeff": 0.0,
        "min_pressure_bar": 1.5,
        "nominal_pressure_bar": 3.8,
        "longitude": -73.9980,
        "latitude": 40.7160,
    },
    {
        "id": "NODE-JUNC-05",
        "name": "Harbor Terminal Service Intake J5",
        "node_type": "JUNCTION",
        "elevation_m": 6.5,
        "base_demand_lps": 15.0,
        "emitter_coeff": 0.0,
        "min_pressure_bar": 1.5,
        "nominal_pressure_bar": 3.5,
        "longitude": -74.0060,
        "latitude": 40.7040,
    },
    {
        "id": "NODE-JUNC-06",
        "name": "Pinecrest Residential Node J6",
        "node_type": "JUNCTION",
        "elevation_m": 22.0,
        "base_demand_lps": 14.0,
        "emitter_coeff": 0.0,
        "min_pressure_bar": 1.5,
        "nominal_pressure_bar": 3.9,
        "longitude": -74.0130,
        "latitude": 40.7180,
    },
]

DEFAULT_LINKS = [
    {
        "id": "LINK-PIPE-TRUNK-A",
        "name": "Spine Trunk Line A (Upper)",
        "link_type": "PIPE",
        "start_node_id": "NODE-RES-01",
        "end_node_id": "NODE-JUNC-01",
        "length_m": 1050.0,
        "diameter_mm": 750.0,
        "roughness": 140.0,
        "pipeline_segment_id": "PIPE-SEC-4A-10",
        "initial_status": "OPEN",
        "current_status": "OPEN",
        "coordinates": [
            [-74.0060, 40.7220],
            [-74.0060, 40.7128],
        ],
    },
    {
        "id": "LINK-PIPE-TRUNK-B1",
        "name": "Metro Central Main Trunk Line B (West)",
        "link_type": "PIPE",
        "start_node_id": "NODE-JUNC-01",
        "end_node_id": "NODE-JUNC-02",
        "length_m": 620.0,
        "diameter_mm": 600.0,
        "roughness": 130.0,
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "initial_status": "OPEN",
        "current_status": "OPEN",
        "coordinates": [
            [-74.0060, 40.7128],
            [-74.0110, 40.7115],
        ],
    },
    {
        "id": "LINK-PIPE-TRUNK-B2",
        "name": "Metro Central Main Trunk Line B (Far West)",
        "link_type": "PIPE",
        "start_node_id": "NODE-JUNC-02",
        "end_node_id": "NODE-JUNC-03",
        "length_m": 540.0,
        "diameter_mm": 600.0,
        "roughness": 130.0,
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "initial_status": "OPEN",
        "current_status": "OPEN",
        "coordinates": [
            [-74.0110, 40.7115],
            [-74.0150, 40.7100],
        ],
    },
    {
        "id": "LINK-PIPE-IND-01",
        "name": "Industrial Park Feeder Line 1",
        "link_type": "PIPE",
        "start_node_id": "NODE-JUNC-01",
        "end_node_id": "NODE-JUNC-04",
        "length_m": 820.0,
        "diameter_mm": 400.0,
        "roughness": 150.0,
        "pipeline_segment_id": "PIPE-IND-1A-04",
        "initial_status": "OPEN",
        "current_status": "OPEN",
        "coordinates": [
            [-74.0060, 40.7128],
            [-74.0035, 40.7135],
            [-74.0021, 40.7145],
        ],
    },
    {
        "id": "LINK-PIPE-IND-TANK",
        "name": "Industrial Tank Feed Line",
        "link_type": "PIPE",
        "start_node_id": "NODE-JUNC-04",
        "end_node_id": "NODE-TANK-01",
        "length_m": 350.0,
        "diameter_mm": 350.0,
        "roughness": 140.0,
        "pipeline_segment_id": "PIPE-IND-1A-04",
        "initial_status": "OPEN",
        "current_status": "OPEN",
        "coordinates": [
            [-74.0021, 40.7145],
            [-73.9980, 40.7160],
        ],
    },
    {
        "id": "LINK-PIPE-RES-01",
        "name": "Pinecrest Residential Sub-Branch",
        "link_type": "PIPE",
        "start_node_id": "NODE-RES-01",
        "end_node_id": "NODE-JUNC-06",
        "length_m": 940.0,
        "diameter_mm": 350.0,
        "roughness": 140.0,
        "pipeline_segment_id": "PIPE-RES-3C-11",
        "initial_status": "OPEN",
        "current_status": "OPEN",
        "coordinates": [
            [-74.0060, 40.7220],
            [-74.0089, 40.7198],
            [-74.0130, 40.7180],
        ],
    },
    {
        "id": "LINK-VALVE-HRB-PRV",
        "name": "Harbor Zone Pressure Reducing Valve PRV-01",
        "link_type": "VALVE",
        "start_node_id": "NODE-JUNC-01",
        "end_node_id": "NODE-JUNC-05",
        "length_m": 980.0,
        "diameter_mm": 300.0,
        "roughness": 140.0,
        "valve_type": "PRV",
        "valve_setting": 3.5,  # 3.5 bar target downstream
        "pipeline_segment_id": "PIPE-HRB-02-19",
        "initial_status": "ACTIVE",
        "current_status": "ACTIVE",
        "coordinates": [
            [-74.0060, 40.7128],
            [-74.0060, 40.7040],
        ],
    },
    {
        "id": "LINK-PUMP-BOOSTER-01",
        "name": "Metro Spine Booster Pump Station P1",
        "link_type": "PUMP",
        "start_node_id": "NODE-RES-01",
        "end_node_id": "NODE-JUNC-01",
        "length_m": 20.0,
        "diameter_mm": 600.0,
        "roughness": 150.0,
        "pump_speed": 1.0,
        "pump_power_kw": 45.0,
        "pipeline_segment_id": "PIPE-SEC-4A-10",
        "initial_status": "OPEN",
        "current_status": "OPEN",
        "coordinates": [
            [-74.0060, 40.7220],
            [-74.0060, 40.7180],
        ],
    },
]


class HydraulicNetworkService:
    @staticmethod
    def get_or_create_default_network(db: Session) -> HydraulicNetworkModel:
        net = db.query(HydraulicNetworkModel).filter(HydraulicNetworkModel.id == DEFAULT_NETWORK_ID).first()
        if not net:
            net = HydraulicNetworkModel(
                id=DEFAULT_NETWORK_ID,
                name="Metro Central Water Supply & Hydraulic Distribution Network",
                description="Comprehensive digital twin model of metropolitan water grid including trunk mains, booster pumps, elevated tanks, and pressure zones.",
                headloss_formula="H-W",
                flow_units="LPS",
                demand_model="PDA",
                is_active=True,
                is_simulated=True,
            )
            db.add(net)
            db.flush()

            # Seed Nodes
            for nd in DEFAULT_NODES:
                node_m = HydraulicNodeModel(
                    id=nd["id"],
                    network_id=net.id,
                    node_type=nd["node_type"],
                    name=nd["name"],
                    elevation_m=nd["elevation_m"],
                    base_head_m=nd.get("base_head_m"),
                    base_demand_lps=nd["base_demand_lps"],
                    emitter_coeff=nd.get("emitter_coeff", 0.0),
                    min_pressure_bar=nd.get("min_pressure_bar", 1.5),
                    nominal_pressure_bar=nd.get("nominal_pressure_bar", 4.2),
                    initial_level_m=nd.get("initial_level_m"),
                    min_level_m=nd.get("min_level_m"),
                    max_level_m=nd.get("max_level_m"),
                    diameter_m=nd.get("diameter_m"),
                    longitude=nd["longitude"],
                    latitude=nd["latitude"],
                    is_simulated=True,
                )
                db.add(node_m)

            # Seed Links
            for lk in DEFAULT_LINKS:
                link_m = HydraulicLinkModel(
                    id=lk["id"],
                    network_id=net.id,
                    link_type=lk["link_type"],
                    name=lk["name"],
                    start_node_id=lk["start_node_id"],
                    end_node_id=lk["end_node_id"],
                    length_m=lk["length_m"],
                    diameter_mm=lk["diameter_mm"],
                    roughness=lk["roughness"],
                    pipeline_segment_id=lk.get("pipeline_segment_id"),
                    pump_speed=lk.get("pump_speed", 1.0),
                    pump_power_kw=lk.get("pump_power_kw", 45.0),
                    valve_type=lk.get("valve_type"),
                    valve_setting=lk.get("valve_setting"),
                    initial_status=lk.get("initial_status", "OPEN"),
                    current_status=lk.get("current_status", "OPEN"),
                    coordinates_json=json.dumps(lk["coordinates"]),
                    is_simulated=True,
                )
                db.add(link_m)

            db.commit()
            db.refresh(net)

        return net

    @staticmethod
    def get_network(db: Session, network_id: str) -> Optional[HydraulicNetworkModel]:
        return db.query(HydraulicNetworkModel).filter(HydraulicNetworkModel.id == network_id).first()

    @staticmethod
    def list_networks(db: Session) -> List[HydraulicNetworkModel]:
        HydraulicNetworkService.get_or_create_default_network(db)
        return db.query(HydraulicNetworkModel).all()

    @staticmethod
    def get_nodes(db: Session, network_id: str) -> List[HydraulicNodeModel]:
        return db.query(HydraulicNodeModel).filter(HydraulicNodeModel.network_id == network_id).all()

    @staticmethod
    def get_links(db: Session, network_id: str) -> List[HydraulicLinkModel]:
        return db.query(HydraulicLinkModel).filter(HydraulicLinkModel.network_id == network_id).all()

    @staticmethod
    def get_network_topology(db: Session, network_id: str) -> Dict[str, Any]:
        """
        Returns full GeoJSON network topology and node/link tables for GIS digital twin view.
        """
        net = HydraulicNetworkService.get_network(db, network_id)
        if not net:
            net = HydraulicNetworkService.get_or_create_default_network(db)

        nodes = HydraulicNetworkService.get_nodes(db, net.id)
        links = HydraulicNetworkService.get_links(db, net.id)

        features = []

        # Point features for nodes
        for n in nodes:
            features.append({
                "type": "Feature",
                "id": n.id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [n.longitude, n.latitude],
                },
                "properties": {
                    "feature_type": "NODE",
                    "id": n.id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "elevation_m": n.elevation_m,
                    "base_head_m": n.base_head_m,
                    "base_demand_lps": n.base_demand_lps,
                    "min_pressure_bar": n.min_pressure_bar,
                    "nominal_pressure_bar": n.nominal_pressure_bar,
                    "initial_level_m": n.initial_level_m,
                    "diameter_m": n.diameter_m,
                },
            })

        # LineString features for links
        for l in links:
            coords = []
            try:
                coords = json.loads(l.coordinates_json)
            except Exception:
                pass
            features.append({
                "type": "Feature",
                "id": l.id,
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords,
                },
                "properties": {
                    "feature_type": "LINK",
                    "id": l.id,
                    "name": l.name,
                    "link_type": l.link_type,
                    "start_node_id": l.start_node_id,
                    "end_node_id": l.end_node_id,
                    "length_m": l.length_m,
                    "diameter_mm": l.diameter_mm,
                    "roughness": l.roughness,
                    "current_status": l.current_status,
                    "pipeline_segment_id": l.pipeline_segment_id,
                    "pump_power_kw": l.pump_power_kw,
                    "valve_type": l.valve_type,
                    "valve_setting": l.valve_setting,
                },
            })

        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }

        solver_data = NetworkAdapter.to_solver_dict(net, nodes, links)

        return {
            "network": {
                "id": net.id,
                "name": net.name,
                "description": net.description,
                "headloss_formula": net.headloss_formula,
                "flow_units": net.flow_units,
                "demand_model": net.demand_model,
                "is_active": net.is_active,
            },
            "nodes_count": len(nodes),
            "links_count": len(links),
            "geojson": geojson,
            "solver_data": solver_data,
        }

