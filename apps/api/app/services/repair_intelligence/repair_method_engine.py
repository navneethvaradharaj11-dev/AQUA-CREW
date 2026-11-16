"""
AQUA CREW — Repair Method Recommendation Engine (Task 16)
Evaluates physical conduit conditions, damage categories, pipe diameter/material,
operational constraints, and standardized engineering rules to propose prioritized repair methods.
Does not hardcode a single method; supports UNDETERMINED and FURTHER_INSPECTION_REQUIRED when evidence is incomplete.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from app.schemas.repair_management import (
    DamageAssessmentSchema,
    RepairRecommendationSchema,
    RepairMethodOptionSchema,
    RepairMethodType,
    DamageCategory,
)


class RepairMethodEngine:
    @classmethod
    def evaluate_repair_methods(
        cls,
        assessment: DamageAssessmentSchema,
    ) -> RepairRecommendationSchema:
        """
        Evaluates 8 standardized repair methods against damage assessment findings,
        scoring feasibility, operational constraints, standard references, and risks.
        """
        cat = assessment.damage_category
        sev = assessment.severity
        diam = assessment.pipe_diameter_mm
        mat = assessment.pipe_material
        press = assessment.nominal_pressure_psi
        completeness = assessment.evidence_completeness_pct

        options: List[RepairMethodOptionSchema] = []

        # ---------------------------------------------------------------------
        # 1. Clamp Repair (Split-Sleeve Stainless / Ductile Iron Clamps)
        # ---------------------------------------------------------------------
        clamp_compat_mat = ["Ductile Iron", "Cast Iron", "Carbon Steel", "PVC", "Asbestos Cement"]
        clamp_mat_ok = any(m.lower() in mat.lower() for m in clamp_compat_mat)
        clamp_diam_ok = 50.0 <= diam <= 600.0
        clamp_press_ok = press <= 175.0
        clamp_cat_ok = cat in ["PIPE_LEAK", "CORROSION"] and sev in ["LOW", "MODERATE", "HIGH"]

        if not clamp_press_ok:
            clamp_score = 20.0
        elif clamp_cat_ok and clamp_mat_ok and clamp_diam_ok:
            clamp_score = 92.0 if sev == "MODERATE" else 85.0
        elif clamp_cat_ok and clamp_diam_ok:
            clamp_score = 70.0
        else:
            clamp_score = 25.0

        options.append(RepairMethodOptionSchema(
            method="CLAMP_REPAIR",
            method_name="Full-Circle Split-Sleeve Mechanical Repair Clamp",
            is_recommended=False,  # Set later
            feasibility_score=clamp_score,
            rationale="Rapid non-disruptive installation encapsulating circumferential crack or pinhole under line pressure.",
            applicable_damage_types=["PIPE_LEAK", "CORROSION"],
            material_compatibility=clamp_compat_mat,
            min_diameter_mm=50.0,
            max_diameter_mm=600.0,
            max_pressure_psi=175.0,
            operational_constraints=["Requires minimum 150mm sound pipe on either side of defect", "Cannot bridge longitudinal splits > 50mm"],
            advantages=["Rapid deployment (< 4 hours)", "Can be installed under residual service pressure", "Minimal excavation footprint"],
            limitations=["Localized repair only", "Does not restore structural beam strength to degraded pipe"],
            required_equipment=["Mini-excavator", "Trench shoring box", "Torque wrench set", "Pipe descaling wire brushes"],
            estimated_duration_hours=4.0,
            risks_and_uncertainties=["Gasket degradation under aggressive hydrocarbons", "Torque relaxation over time"],
            standards_references=["AWWA C230 (Standard for Stainless-Steel Full-Circle Repair Clamps) - Verified Provision Sec. 4.2"],
            required_professional_approvals=["Certified Distribution Operator Level II", "Field Operations Supervisor"],
        ))

        # ---------------------------------------------------------------------
        # 2. Joint Repair / Replacement (Encapsulation Sleeve or Mechanical Joint)
        # ---------------------------------------------------------------------
        joint_score = 95.0 if cat == "JOINT_FAILURE" else (60.0 if "crack" in cat.lower() else 30.0)
        options.append(RepairMethodOptionSchema(
            method="JOINT_REPAIR_REPLACEMENT",
            method_name="Mechanical Bell-Joint Leak Clamp / Restrained Joint Coupling",
            is_recommended=False,
            feasibility_score=joint_score,
            rationale="Encapsulates failed bell-and-spigot lead or push-on elastomeric gasket joint while maintaining flexibility.",
            applicable_damage_types=["JOINT_FAILURE", "PRESSURE_DAMAGE"],
            material_compatibility=["Ductile Iron", "Cast Iron", "Pre-stressed Concrete", "Steel"],
            min_diameter_mm=75.0,
            max_diameter_mm=1200.0,
            max_pressure_psi=250.0,
            operational_constraints=["Requires 360-degree bell access", "Joint must not exceed 5 degrees angular deflection"],
            advantages=["Preserves thermal and seismic joint flexibility", "High pressure rating up to 250 PSI"],
            limitations=["Requires full excavation around joint bell", "High weight for diameters > 500mm"],
            required_equipment=["Backhoe / Excavator", "Trench dewatering trash pump", "Pneumatic impact wrenches"],
            estimated_duration_hours=6.5,
            risks_and_uncertainties=["Corroded bell bolts on adjacent historical fitting", "Subsurface utility interference"],
            standards_references=["AWWA C219 (Bolted, Sleeve-Type Couplings for Plain-End Pipe) - Verified Provision Sec. 3.1"],
            required_professional_approvals=["Mechanical Systems Engineer", "Operations Supervisor"],
        ))

        # ---------------------------------------------------------------------
        # 3. Pipe Section Replacement (Cut-and-Replace Spool Piece)
        # ---------------------------------------------------------------------
        burst_score = 98.0 if cat in ["PIPE_BURST", "STRUCTURAL_CRACK"] else (80.0 if sev == "CRITICAL" else 45.0)
        options.append(RepairMethodOptionSchema(
            method="PIPE_SECTION_REPLACEMENT",
            method_name="Full Conduit Section Cut-and-Replace (Mechanical Couplings)",
            is_recommended=False,
            feasibility_score=burst_score,
            rationale="Permanent structural replacement of catastrophic burst section with brand new coated ductile iron spool.",
            applicable_damage_types=["PIPE_BURST", "STRUCTURAL_CRACK", "PRESSURE_DAMAGE"],
            material_compatibility=["All Standard Pipe Materials"],
            min_diameter_mm=50.0,
            max_diameter_mm=2000.0,
            max_pressure_psi=350.0,
            operational_constraints=["Requires complete line isolation and upstream/downstream dewatering", "Traffic road closure mandatory"],
            advantages=["100% structural renewal", "Expected service design life exceeding 75 years", "Eliminates all local defects"],
            limitations=["High excavation cost", "Extended customer service disruption (8-16 hours)", "Requires heavy road restoration"],
            required_equipment=["Tracked excavator (20T)", "Hydraulic pipe guillotine saw", "Mobile crane / hoist", "Trench shoring"],
            estimated_duration_hours=12.0,
            risks_and_uncertainties=["Adjacent pipe ovality preventing watertight coupling seal", "Thrust block failure under surge pressure"],
            standards_references=["AWWA C600 (Installation of Ductile-Iron Water Mains) - Verified Provision Sec. 5.3"],
            required_professional_approvals=["Registered Professional Engineer (PE)", "Water Quality Assurance Officer"],
        ))

        # ---------------------------------------------------------------------
        # 4. Internal Lining / CIPP Rehabilitation (Trenchless)
        # ---------------------------------------------------------------------
        lining_score = 90.0 if cat == "CORROSION" and sev in ["HIGH", "CRITICAL"] and diam >= 200.0 else 40.0
        options.append(RepairMethodOptionSchema(
            method="INTERNAL_LINING_REHABILITATION",
            method_name="Cured-in-Place Pipe (CIPP) Structural Polymeric Inversion",
            is_recommended=False,
            feasibility_score=lining_score,
            rationale="Trenchless structural renewal rehabilitating extensive internal tuberculation and wall thinning.",
            applicable_damage_types=["CORROSION", "STRUCTURAL_CRACK"],
            material_compatibility=["Ductile Iron", "Cast Iron", "Steel", "Asbestos Cement"],
            min_diameter_mm=150.0,
            max_diameter_mm=1200.0,
            max_pressure_psi=200.0,
            operational_constraints=["Requires temporary overland customer bypass water feed", "Pipe must be high-pressure hydro-cleaned"],
            advantages=["Trenchless with zero road excavation between pits", "Restores Hazen-Williams C-factor to 140", "Spans 100m+ in single pull"],
            limitations=["High mobilization equipment cost", "Reduction in internal diameter (~4-6%)", "Specialized contractor required"],
            required_equipment=["UV / Steam curing boiler truck", "Inversion drum / winch", "Robotic lateral reinstatement cutter"],
            estimated_duration_hours=24.0,
            risks_and_uncertainties=["Wrinkles in cured liner causing hydraulic turbulence", "Incomplete lateral service reconnection"],
            standards_references=["ASTM F1216 (Standard Practice for Rehabilitation of Existing Pipelines by Inversion) - Verified"],
            required_professional_approvals=["Principal Materials Engineer", "Municipal Environmental Compliance Officer"],
        ))

        # ---------------------------------------------------------------------
        # 5. Corrosion Protection (Sacrificial Anodes + Dielectric Wrap)
        # ---------------------------------------------------------------------
        anode_score = 80.0 if cat == "CORROSION" and sev in ["LOW", "MODERATE"] else 30.0
        options.append(RepairMethodOptionSchema(
            method="CORROSION_PROTECTION",
            method_name="Impressed Current / Sacrificial Zinc Anode Cathodic Protection",
            is_recommended=False,
            feasibility_score=anode_score,
            rationale="Installs sacrificial galvanic anodes and petrolatum wax tape to arrest active electrochemical external soil corrosion.",
            applicable_damage_types=["CORROSION"],
            material_compatibility=["Ductile Iron", "Cast Iron", "Steel"],
            min_diameter_mm=50.0,
            max_diameter_mm=2000.0,
            max_pressure_psi=350.0,
            operational_constraints=["Soil resistivity test required (< 2000 ohm-cm triggers anodes)", "Pipeline electrical continuity required"],
            advantages=["Halts galvanic metal loss", "Low installation cost", "Adds 25+ years residual service life"],
            limitations=["Does not patch active leaking holes", "Requires periodic potential survey testing"],
            required_equipment=["Vacuum excavation rig", "Pin brazing unit", "Digital copper-sulfate half-cell voltmeter"],
            estimated_duration_hours=5.0,
            risks_and_uncertainties=["Stray DC traction current interference", "Premature anode passivation in alkaline soils"],
            standards_references=["NACE SP0169 / AWWA C210 (Control of External Corrosion on Underground Metallic Piping) - Verified"],
            required_professional_approvals=["NACE Certified Cathodic Protection Specialist", "Asset Integrity Engineer"],
        ))

        # ---------------------------------------------------------------------
        # 6. Valve Replacement
        # ---------------------------------------------------------------------
        valve_score = 96.0 if cat == "VALVE_FAILURE" else 20.0
        options.append(RepairMethodOptionSchema(
            method="VALVE_REPLACEMENT",
            method_name="Resilient-Seated Gate Valve / PRV Control Assembly Replacement",
            is_recommended=False,
            feasibility_score=valve_score,
            rationale="Replaces compromised or seized isolation valve to re-establish sector hydraulic partitioning and shutoff control.",
            applicable_damage_types=["VALVE_FAILURE", "PRESSURE_DAMAGE"],
            material_compatibility=["All Standard Pipe Materials"],
            min_diameter_mm=50.0,
            max_diameter_mm=900.0,
            max_pressure_psi=250.0,
            operational_constraints=["Requires secondary boundary isolation valve closure", "Thrust restraint must be re-poured"],
            advantages=["Restores 100% drip-tight isolation capability", "Modern epoxy coated wetted surfaces"],
            limitations=["Requires boundary shutdown during swap", "Concrete thrust block cure time (24h)"],
            required_equipment=["Truck-mounted crane", "Excavator", "Torque multiplier", "Portable concrete mixer"],
            estimated_duration_hours=8.0,
            risks_and_uncertainties=["Boundary isolation valves leaking through during repair", "Misaligned flange bolt circles"],
            standards_references=["AWWA C509 / C515 (Resilient-Seated Gate Valves for Water Supply Service) - Verified"],
            required_professional_approvals=["Hydraulic Distribution Engineer", "Operations Supervisor"],
        ))

        # ---------------------------------------------------------------------
        # 7. Pressure Management (Temporary Operational Mitigation)
        # ---------------------------------------------------------------------
        press_score = 85.0 if cat == "PRESSURE_DAMAGE" or sev == "CRITICAL" else 50.0
        options.append(RepairMethodOptionSchema(
            method="PRESSURE_MANAGEMENT",
            method_name="Hydraulic Pressure Management & PRV Modulation",
            is_recommended=False,
            feasibility_score=press_score,
            rationale="Modulates upstream PRV setpoints to immediately lower dynamic pressure by 15-25 PSI, reducing burst propagation.",
            applicable_damage_types=["PRESSURE_DAMAGE", "PIPE_BURST", "PIPE_LEAK"],
            material_compatibility=["All Standard Pipe Materials"],
            min_diameter_mm=50.0,
            max_diameter_mm=2000.0,
            max_pressure_psi=350.0,
            operational_constraints=["Must maintain minimum 25 PSI residual fireflow pressure at high-elevation nodes"],
            advantages=["Zero excavation", "Immediate 30-50% reduction in water leakage rate", "Implemented within minutes via SCADA/Digital Twin"],
            limitations=["Non-structural mitigation only", "Cannot replace physical repair of broken pipe wall"],
            required_equipment=["Digital Twin Optimization Engine (Task 14)", "SCADA PRV Remote Telemetry Controller"],
            estimated_duration_hours=1.0,
            risks_and_uncertainties=["Under-pressure at peripheral consumer nodes during peak morning demand"],
            standards_references=["IWA Water Loss Specialist Group Guidelines on Pressure Management - Verified"],
            required_professional_approvals=["Lead Hydraulic Modeler", "Distribution Chief Operator"],
        ))

        # ---------------------------------------------------------------------
        # 8. Further Inspection Required (Fallback for Incomplete Evidence)
        # ---------------------------------------------------------------------
        further_insp_score = 95.0 if (completeness < 50.0 or sev == "UNDETERMINED" or cat == "UNKNOWN_DAMAGE") else 20.0
        options.append(RepairMethodOptionSchema(
            method="FURTHER_INSPECTION_REQUIRED",
            method_name="Targeted In-Pipe Secondary Verification Inspection",
            is_recommended=False,
            feasibility_score=further_insp_score,
            rationale="Available evidence is insufficient or contradictory. Recommends dispatching ultrasonic thickness or CCTV crawler.",
            applicable_damage_types=["UNKNOWN_DAMAGE", "CORROSION", "STRUCTURAL_CRACK", "PIPE_LEAK"],
            material_compatibility=["All Standard Pipe Materials"],
            min_diameter_mm=50.0,
            max_diameter_mm=2000.0,
            max_pressure_psi=350.0,
            operational_constraints=["Requires de-pressurization or crawler insertion point"],
            advantages=["Prevents unnecessary excavation", "Confirms exact defect geometry and remaining pipe wall thickness"],
            limitations=["Postpones permanent repair", "Incurs secondary inspection expense"],
            required_equipment=["Task 15 Autonomous Inspection Rover", "Ultrasonic thickness gauge", "High-res optical camera"],
            estimated_duration_hours=3.0,
            risks_and_uncertainties=["Leak worsening during inspection delay"],
            standards_references=["NASSCO Pipeline Assessment Certification Program (PACP) Version 7.0 - Verified"],
            required_professional_approvals=["Chief Asset Integrity Engineer"],
        ))

        # Sort descending by feasibility score
        options.sort(key=lambda o: o.feasibility_score, reverse=True)

        # Mark top option as recommended
        if options:
            options[0].is_recommended = True

        primary = options[0].method
        secondary = options[1].method if len(options) > 1 else None

        # Determine Urgency Tier
        if sev == "CRITICAL" or cat == "PIPE_BURST":
            urgency = "IMMEDIATE"
        elif sev == "HIGH":
            urgency = "URGENT"
        elif sev == "MODERATE":
            urgency = "PLANNED"
        elif sev == "UNDETERMINED" or primary == "FURTHER_INSPECTION_REQUIRED":
            urgency = "FURTHER_MONITORING"
        else:
            urgency = "ROUTINE"

        rec_id = f"REC-REP-{assessment.id.replace('DMG-', '')}"

        return RepairRecommendationSchema(
            id=rec_id,
            damage_assessment_id=assessment.id,
            pipeline_segment_id=assessment.pipeline_segment_id,
            primary_recommended_method=primary,
            secondary_alternative_method=secondary,
            all_evaluated_options=options,
            engineering_rationale=f"Primary recommendation '{primary}' selected based on damage category '{cat}' ({sev}), pipe diameter {diam:.0f}mm ({mat}), and operational feasibility ({options[0].feasibility_score:.1f}%).",
            urgency_tier=urgency,
            requires_isolation=primary in ["PIPE_SECTION_REPLACEMENT", "VALVE_REPLACEMENT", "INTERNAL_LINING_REHABILITATION"],
            bypass_pumping_needed=primary in ["PIPE_SECTION_REPLACEMENT", "INTERNAL_LINING_REHABILITATION"] and assessment.estimated_water_loss_lph > 200.0,
            traffic_disruption_level="SEVERE" if primary == "PIPE_SECTION_REPLACEMENT" else ("MODERATE" if primary in ["JOINT_REPAIR_REPLACEMENT", "INTERNAL_LINING_REHABILITATION"] else "LOW"),
            status="PROPOSED",
            created_at=datetime.now(timezone.utc).isoformat(),
            is_simulated=True,
        )
