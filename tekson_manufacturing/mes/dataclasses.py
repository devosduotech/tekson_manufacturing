"""
MES Data Classes

Data classes for Manufacturing Execution System.
Separates evaluation from persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


# =============================================================================
# CONSTANTS
# =============================================================================

class MaterialStatus:
    """Material availability status constants"""
    WAITING = "Waiting for Material"
    AVAILABLE = "Material Available"
    SHORT = "Material Short"


class ReadinessStatus:
    """Job Card readiness status constants"""
    READY = "Ready to Start"
    WAITING_MATERIAL = "Waiting for Material"
    WAITING_PREVIOUS_OP = "Waiting for Previous Operation"
    BLOCKED = "Blocked"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    HOLD = "On Hold"  # Reserved for future: QC Hold, Engineering Hold, etc.


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MaterialResult:
    """
    Result from Material Readiness Engine
    
    Attributes:
        is_ready: True if material is available for production
        status: Material status constant (MaterialStatus)
        available_qty: Quantity available in WIP warehouse
        required_qty: Quantity required for production
        shortage_qty: Shortage quantity (if any)
        shortage_details: List of item-wise shortage details
        warehouse: WIP warehouse name
        message: Human-readable message
        warnings: Non-blocking warnings
        errors: Blocking errors
    """
    is_ready: bool
    status: str
    available_qty: float
    required_qty: float
    shortage_qty: float
    shortage_details: List[Dict[str, Any]]
    warehouse: str
    message: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialResult':
        """Create MaterialResult from dictionary (for backward compatibility)"""
        return cls(
            is_ready=data.get('is_ready', False),
            status=data.get('status', MaterialStatus.WAITING),
            available_qty=data.get('available_qty', 0.0),
            required_qty=data.get('required_qty', 0.0),
            shortage_qty=data.get('shortage_qty', 0.0),
            shortage_details=data.get('shortage_details', []),
            warehouse=data.get('warehouse', ''),
            message=data.get('message', ''),
            warnings=data.get('warnings', []),
            errors=data.get('errors', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for backward compatibility)"""
        return {
            'is_ready': self.is_ready,
            'status': self.status,
            'available_qty': self.available_qty,
            'required_qty': self.required_qty,
            'shortage_qty': self.shortage_qty,
            'shortage_details': self.shortage_details,
            'warehouse': self.warehouse,
            'message': self.message,
            'warnings': self.warnings,
            'errors': self.errors
        }


@dataclass
class DependencyResult:
    """
    Result from Dependency Engine
    
    Attributes:
        can_start: True if all dependencies are met
        previous_complete: True if previous operation is complete
        previous_jc_name: Name of previous Job Card (if blocking)
        reason: Human-readable reason
        diagnostic: Detailed diagnostic message
        warnings: Non-blocking warnings
        errors: Blocking errors
    """
    can_start: bool
    previous_complete: bool
    previous_jc_name: Optional[str]
    reason: str
    diagnostic: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DependencyResult':
        """Create DependencyResult from dictionary (for backward compatibility)"""
        return cls(
            can_start=data.get('can_start', False),
            previous_complete=data.get('previous_complete', False),
            previous_jc_name=data.get('previous_jc_name'),
            reason=data.get('reason', ''),
            diagnostic=data.get('diagnostic', ''),
            warnings=data.get('warnings', []),
            errors=data.get('errors', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for backward compatibility)"""
        return {
            'can_start': self.can_start,
            'previous_complete': self.previous_complete,
            'previous_jc_name': self.previous_jc_name,
            'reason': self.reason,
            'diagnostic': self.diagnostic,
            'warnings': self.warnings,
            'errors': self.errors
        }


@dataclass
class ReadinessResult:
    """
    Result from Job Card Readiness Engine
    
    Combines MaterialResult and DependencyResult into comprehensive readiness status.
    
    Attributes:
        material_status: Material availability status
        readiness_status: Overall readiness status
        can_start: True if Job Card can be started
        blocked_by: Specific reason if blocked
        material_available: Boolean flag for material availability
        previous_operation_complete: Boolean flag for dependency
        last_updated: When this was evaluated
        warnings: Non-blocking warnings
        errors: Blocking errors
        messages: Informational messages
    """
    material_status: str
    readiness_status: str
    can_start: bool
    blocked_by: str
    material_available: bool
    previous_operation_complete: bool
    last_updated: datetime
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    
    @classmethod
    def create_completed(cls, material_status: str) -> 'ReadinessResult':
        """Create ReadinessResult for completed Job Card"""
        return cls(
            material_status=material_status,
            readiness_status=ReadinessStatus.COMPLETED,
            can_start=False,
            blocked_by="",
            material_available=True,
            previous_operation_complete=True,
            last_updated=datetime.now(),
            messages=["Job Card completed"]
        )
    
    @classmethod
    def create_in_progress(cls, material_status: str) -> 'ReadinessResult':
        """Create ReadinessResult for in-progress Job Card"""
        return cls(
            material_status=material_status,
            readiness_status=ReadinessStatus.IN_PROGRESS,
            can_start=False,
            blocked_by="",
            material_available=True,
            previous_operation_complete=True,
            last_updated=datetime.now(),
            messages=["Job Card in progress"]
        )
    
    @classmethod
    def create_ready(cls, material_status: str) -> 'ReadinessResult':
        """Create ReadinessResult for ready-to-start Job Card"""
        return cls(
            material_status=material_status,
            readiness_status=ReadinessStatus.READY,
            can_start=True,
            blocked_by="",
            material_available=True,
            previous_operation_complete=True,
            last_updated=datetime.now()
        )
    
    @classmethod
    def create_waiting_material(cls, message: str) -> 'ReadinessResult':
        """Create ReadinessResult for waiting-for-material Job Card"""
        return cls(
            material_status=MaterialStatus.WAITING,
            readiness_status=ReadinessStatus.WAITING_MATERIAL,
            can_start=False,
            blocked_by=message,
            material_available=False,
            previous_operation_complete=True,
            last_updated=datetime.now(),
            warnings=[],
            errors=[]
        )
    
    @classmethod
    def create_waiting_previous_op(cls, previous_jc_name: str) -> 'ReadinessResult':
        """Create ReadinessResult for waiting-for-previous-operation Job Card"""
        return cls(
            material_status=MaterialStatus.AVAILABLE,
            readiness_status=ReadinessStatus.WAITING_PREVIOUS_OP,
            can_start=False,
            blocked_by=f"Waiting for: {previous_jc_name}",
            material_available=True,
            previous_operation_complete=False,
            last_updated=datetime.now()
        )
    
    @classmethod
    def create_blocked(cls, material_status: str, blocked_by: str) -> 'ReadinessResult':
        """Create ReadinessResult for blocked Job Card"""
        return cls(
            material_status=material_status,
            readiness_status=ReadinessStatus.BLOCKED,
            can_start=False,
            blocked_by=blocked_by,
            material_available=False,
            previous_operation_complete=True,
            last_updated=datetime.now()
        )
