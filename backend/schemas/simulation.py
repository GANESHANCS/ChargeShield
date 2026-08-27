"""
Pydantic Schemas for ChargeShield Phase 9 Simulation & Real-Time Events.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SimulationEvent(BaseModel):
    event_id: str = Field(..., description="Unique event ID")
    event_type: str = Field(..., description="Lifecycle event type e.g., TRANSACTION_RECEIVED")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    dispute_id: Optional[str] = Field(None, description="Associated dispute ID if created")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    source: str = Field("SIMULATION_ENGINE", description="Event source component")
    data_state: str = Field("SIMULATION", description="Data state tag: SIMULATION, HISTORICAL, or PRODUCTION")
    status: str = Field("COMPLETED", description="Event execution status")
    message: str = Field(..., description="Human-readable event log entry")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured event payload context")

class SimulationStatus(BaseModel):
    running: bool = Field(..., description="Whether simulation mode is active")
    scenario: str = Field(..., description="Current selected scenario profile")
    events_processed: int = Field(0, description="Total events generated in session")
    transactions_processed: int = Field(0, description="Total transactions processed")
    cases_created: int = Field(0, description="Total cases generated into review queue")
    last_event_time: Optional[str] = Field(None, description="ISO timestamp of most recent event")
    data_state: str = Field("SIMULATION", description="Explicit state governor tag")

class StartSimulationRequest(BaseModel):
    scenario: str = Field("NORMAL_TRANSACTION", description="Scenario profile to initialize")

class SimulationTransactionRequest(BaseModel):
    scenario: Optional[str] = Field(None, description="Override scenario profile for single transaction injection")

class SimulationScenarioDetail(BaseModel):
    scenario_id: str
    name: str
    description: str
    target_risk_tier: str
    target_recommendation: str
