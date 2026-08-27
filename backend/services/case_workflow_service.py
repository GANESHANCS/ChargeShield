"""
Case Workflow Service for ChargeShield.

Handles case work assignment, workflow state transitions, review notes,
and full action lineage activity logging for institutional governance.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

VALID_CASE_STATES = {
    "NEW",
    "IN_REVIEW",
    "ESCALATED",
    "DECISION_PENDING",
    "RESOLVED",
    "CLOSED"
}

ALLOWED_TRANSITIONS = {
    "NEW": {"IN_REVIEW", "ESCALATED", "DECISION_PENDING"},
    "IN_REVIEW": {"DECISION_PENDING", "ESCALATED", "RESOLVED", "CLOSED"},
    "ESCALATED": {"IN_REVIEW", "DECISION_PENDING", "RESOLVED", "CLOSED"},
    "DECISION_PENDING": {"RESOLVED", "CLOSED", "ESCALATED", "IN_REVIEW"},
    "RESOLVED": {"CLOSED", "IN_REVIEW"},
    "CLOSED": {"IN_REVIEW"}  # Allow reopening if justified
}

class CaseWorkflowService:
    """In-memory audit-ready case work management service."""

    def __init__(self):
        self._assignments: Dict[str, str] = {}  # dispute_id -> reviewer_id
        self._statuses: Dict[str, str] = {}     # dispute_id -> status
        self._notes: Dict[str, List[Dict[str, Any]]] = {}     # dispute_id -> notes list
        self._activities: Dict[str, List[Dict[str, Any]]] = {} # dispute_id -> activity lineage

    def get_case_state(self, dispute_id: str) -> Dict[str, Any]:
        """Returns current workflow assignment, status, notes count, and last activity."""
        status = self._statuses.get(dispute_id, "NEW")
        reviewer_id = self._assignments.get(dispute_id, "UNASSIGNED")
        notes = self._notes.get(dispute_id, [])
        activities = self._activities.get(dispute_id, [])
        
        last_activity = activities[-1]["timestamp"] if activities else datetime.now(timezone.utc).isoformat()

        return {
            "dispute_id": dispute_id,
            "status": status,
            "assigned_reviewer_id": reviewer_id,
            "notes_count": len(notes),
            "last_activity_at": last_activity,
            "data_state": "PRODUCTION"
        }

    def assign_case(self, dispute_id: str, reviewer_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        """Assigns a reviewer to a dispute and logs lineage."""
        prev_reviewer = self._assignments.get(dispute_id, "UNASSIGNED")
        self._assignments[dispute_id] = reviewer_id
        
        # If case is NEW, automatically transition to IN_REVIEW upon assignment
        current_status = self._statuses.get(dispute_id, "NEW")
        if current_status == "NEW":
            self._statuses[dispute_id] = "IN_REVIEW"

        actor = actor_id or reviewer_id
        activity = self.log_activity(
            dispute_id=dispute_id,
            event_type="CASE_ASSIGNMENT",
            actor=actor,
            action=f"Assigned case to {reviewer_id}",
            previous_state=f"Assignee: {prev_reviewer}",
            new_state=f"Assignee: {reviewer_id}",
            reason=f"Ownership assigned to {reviewer_id}"
        )

        return {
            "dispute_id": dispute_id,
            "assigned_reviewer_id": reviewer_id,
            "status": self._statuses.get(dispute_id, "IN_REVIEW"),
            "activity": activity
        }

    def update_status(
        self,
        dispute_id: str,
        new_status: str,
        actor_id: str = "SYSTEM",
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Updates case workflow status with transition validation."""
        upper_status = new_status.upper()
        if upper_status not in VALID_CASE_STATES:
            raise ValueError(f"Invalid case status: {new_status}. Valid states: {VALID_CASE_STATES}")

        current_status = self._statuses.get(dispute_id, "NEW")
        
        # Validate state transition if current status exists
        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if upper_status != current_status and upper_status not in allowed:
            # Allow administrative override with explicit reason
            if not reason:
                raise ValueError(
                    f"Invalid status transition from {current_status} to {upper_status}. Allowed: {allowed}"
                )

        self._statuses[dispute_id] = upper_status

        activity = self.log_activity(
            dispute_id=dispute_id,
            event_type="STATUS_CHANGE",
            actor=actor_id,
            action=f"Changed status from {current_status} to {upper_status}",
            previous_state=current_status,
            new_state=upper_status,
            reason=reason or f"Workflow transition to {upper_status}"
        )

        return {
            "dispute_id": dispute_id,
            "previous_status": current_status,
            "status": upper_status,
            "activity": activity
        }

    def add_note(self, dispute_id: str, author_id: str, note_text: str) -> Dict[str, Any]:
        """Adds a timestamped review note and logs lineage."""
        if not note_text or not note_text.strip():
            raise ValueError("Note text cannot be empty.")

        timestamp = datetime.now(timezone.utc).isoformat()
        note_entry = {
            "note_id": f"NOTE_{int(datetime.now().timestamp() * 1000)}",
            "dispute_id": dispute_id,
            "author_id": author_id,
            "note_text": note_text.strip(),
            "timestamp": timestamp
        }

        if dispute_id not in self._notes:
            self._notes[dispute_id] = []
        self._notes[dispute_id].append(note_entry)

        activity = self.log_activity(
            dispute_id=dispute_id,
            event_type="NOTE_ADDED",
            actor=author_id,
            action="Added review note",
            previous_state=f"Notes: {len(self._notes[dispute_id]) - 1}",
            new_state=f"Notes: {len(self._notes[dispute_id])}",
            reason=note_text.strip()[:60] + ("..." if len(note_text.strip()) > 60 else "")
        )

        return {
            "note": note_entry,
            "activity": activity
        }

    def get_notes(self, dispute_id: str) -> List[Dict[str, Any]]:
        """Returns all review notes for a case."""
        return self._notes.get(dispute_id, [])

    def log_activity(
        self,
        dispute_id: str,
        event_type: str,
        actor: str,
        action: str,
        previous_state: str,
        new_state: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Appends an activity item to the dispute's action lineage trace."""
        activity_item = {
            "activity_id": f"ACT_{int(datetime.now().timestamp() * 1000)}",
            "dispute_id": dispute_id,
            "event_type": event_type,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "previous_state": previous_state,
            "new_state": new_state,
            "reason": reason or action
        }

        if dispute_id not in self._activities:
            self._activities[dispute_id] = []
        self._activities[dispute_id].append(activity_item)
        return activity_item

    def get_activity_trace(self, dispute_id: str) -> List[Dict[str, Any]]:
        """Returns complete action lineage trace for a dispute."""
        return self._activities.get(dispute_id, [])

case_workflow_service = CaseWorkflowService()
