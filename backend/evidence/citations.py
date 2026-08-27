"""
Source Citation and Reference Generator for Evidence Engine.
Formats machine-readable SourceReference and human-readable citation labels.
"""

from typing import Optional, Tuple
from backend.evidence.schemas import SourceReference

def generate_citation(source_type: str, source_id: str, field: Optional[str] = None) -> Tuple[SourceReference, str]:
    """
    Returns (SourceReference, human_readable_citation_label).
    Example citation label: "Delivery DEL_002528 -> delivery_status"
    """
    ref = SourceReference(
        entity_type=source_type.upper(),
        entity_id=source_id,
        field=field
    )
    
    type_title = source_type.capitalize()
    if field:
        label = f"{type_title} {source_id} \u2192 {field}"
    else:
        label = f"{type_title} {source_id}"
        
    return ref, label
