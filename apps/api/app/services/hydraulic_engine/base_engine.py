"""
Abstract Base Interface for Hydraulic Simulation Engines (Task 10)
Defines uniform contract for hydraulic solvers (WNTR, EPANET, Todini Global Gradient).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult


class HydraulicEngineBase(ABC):
    """
    Abstract base class for all hydraulic network simulation engines.
    Ensures interchangeable solver backends with identical input/output contracts.
    """

    @abstractmethod
    def build_network(self, network_data: Dict[str, Any]) -> None:
        """
        Constructs the internal network topology from standard network definition
        (nodes, links, pumps, valves, tanks, reservoirs).
        """
        pass

    @abstractmethod
    def apply_overrides(self, overrides: Dict[str, Any]) -> None:
        """
        Applies what-if scenario perturbations (leaks, bursts, demand multipliers,
        equipment status, valve settings).
        """
        pass

    @abstractmethod
    def run_simulation(
        self,
        duration_hours: int = 24,
        timestep_minutes: int = 60,
        demand_model: str = "PDA"
    ) -> HydraulicSimulationResult:
        """
        Executes the hydraulic simulation over the requested time horizon.
        """
        pass

