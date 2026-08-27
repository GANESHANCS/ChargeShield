"""
API v1 Router for ChargeShield Phase 9 Real-Time Event Intelligence & Simulation.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional

from backend.schemas.simulation import (
    SimulationEvent,
    SimulationStatus,
    StartSimulationRequest,
    SimulationTransactionRequest,
    SimulationScenarioDetail
)
from backend.services.simulation_engine import simulation_engine, SCENARIO_PROFILES
from backend.services.event_service import event_service

router = APIRouter(prefix="/api/v1/simulation", tags=["Real-Time Simulation Engine"])

@router.post("/start", response_model=SimulationStatus, summary="Start Simulation Mode")
async def start_simulation(payload: StartSimulationRequest):
    """
    Starts or reconfigures deterministic simulation mode with specified scenario profile.
    """
    try:
        return simulation_engine.start_simulation(payload.scenario)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start simulation: {str(e)}"
        )

@router.post("/stop", response_model=SimulationStatus, summary="Stop Simulation Mode")
async def stop_simulation():
    """
    Deactivates active simulation mode.
    """
    try:
        return simulation_engine.stop_simulation()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop simulation: {str(e)}"
        )

@router.get("/status", response_model=SimulationStatus, summary="Get Simulation Status")
async def get_simulation_status():
    """
    Returns live engine status, active scenario, event counter, and data state governor.
    """
    try:
        return simulation_engine.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve simulation status: {str(e)}"
        )

@router.post("/transaction", summary="Generate Simulated Transaction")
async def generate_simulation_transaction(payload: Optional[SimulationTransactionRequest] = None):
    """
    Generates ONE controlled simulated transaction and pushes it through the full risk & decision pipeline.
    """
    try:
        scenario_override = payload.scenario if payload else None
        return simulation_engine.generate_transaction(scenario_override)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate simulated transaction: {str(e)}"
        )

@router.get("/events", response_model=List[SimulationEvent], summary="Get Live Event Stream")
async def get_simulation_events(
    limit: int = Query(50, ge=1, le=500),
    data_state: Optional[str] = Query(None),
    dispute_id: Optional[str] = Query(None)
):
    """
    Returns chronological stream of lifecycle events with explicit data state labeling.
    """
    try:
        return event_service.get_events(limit=limit, data_state=data_state, dispute_id=dispute_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve event stream: {str(e)}"
        )

@router.get("/scenarios", response_model=List[SimulationScenarioDetail], summary="Get Scenario Profiles")
async def get_simulation_scenarios():
    """
    Returns available deterministic scenario profiles.
    """
    try:
        return [
            SimulationScenarioDetail(
                scenario_id=p["scenario_id"],
                name=p["name"],
                description=p["description"],
                target_risk_tier=p["priority"],
                target_recommendation="CONTEST" if p["win_probability"] >= 0.29 else "DO_NOT_CONTEST"
            )
            for p in SCENARIO_PROFILES.values()
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scenarios: {str(e)}"
        )
