"""
MES Exception Handler - Sprint 6

Handles all 46 exception scenarios with consistent formatting,
logging, and user-friendly messages.

Business Rules:
- EX-MAT-* (8): Material exceptions
- EX-PROD-* (10): Production exceptions
- EX-EQ-* (8): Equipment exceptions
- EX-Q-* (8): Quality exceptions
- EX-CANCEL-* (6): Cancellation exceptions
- EX-SYS-* (6): System exceptions
"""

import frappe
from frappe import _
from typing import Dict, Any, Optional, List
from enum import Enum


class ExceptionCategory(Enum):
    """Exception categories for EX-* rules"""
    MATERIAL = "EX-MAT"
    PRODUCTION = "EX-PROD"
    EQUIPMENT = "EX-EQ"
    QUALITY = "EX-Q"
    CANCELLATION = "EX-CANCEL"
    SYSTEM = "EX-SYS"


class ExceptionSeverity(Enum):
    """Exception severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MESException(Exception):
    """
    Base MES Exception class
    
    All MES exceptions inherit from this class
    """
    def __init__(self, message: str, exception_code: str, severity: ExceptionSeverity = ExceptionSeverity.HIGH):
        self.message = message
        self.exception_code = exception_code
        self.severity = severity
        self.context = {}
        super().__init__(self.message)
    
    def with_context(self, **kwargs):
        """Add context to exception"""
        self.context.update(kwargs)
        return self


class MaterialException(MESException):
    """Material-related exceptions (EX-MAT-*)"""
    def __init__(self, message: str, exception_code: str = "EX-MAT-001"):
        super().__init__(message, exception_code, ExceptionSeverity.HIGH)


class ProductionException(MESException):
    """Production-related exceptions (EX-PROD-*)"""
    def __init__(self, message: str, exception_code: str = "EX-PROD-001"):
        super().__init__(message, exception_code, ExceptionSeverity.HIGH)


class EquipmentException(MESException):
    """Equipment-related exceptions (EX-EQ-*)"""
    def __init__(self, message: str, exception_code: str = "EX-EQ-001"):
        super().__init__(message, exception_code, ExceptionSeverity.HIGH)


class QualityException(MESException):
    """Quality-related exceptions (EX-Q-*)"""
    def __init__(self, message: str, exception_code: str = "EX-Q-001"):
        super().__init__(message, exception_code, ExceptionSeverity.HIGH)


class CancellationException(MESException):
    """Cancellation-related exceptions (EX-CANCEL-*)"""
    def __init__(self, message: str, exception_code: str = "EX-CANCEL-001"):
        super().__init__(message, exception_code, ExceptionSeverity.MEDIUM)


class SystemException(MESException):
    """System-related exceptions (EX-SYS-*)"""
    def __init__(self, message: str, exception_code: str = "EX-SYS-001"):
        super().__init__(message, exception_code, ExceptionSeverity.CRITICAL)


class ExceptionHandler:
    """
    Central exception handler for MES
    
    Handles all 46 exception scenarios with:
    - Consistent formatting
    - Logging
    - User-friendly messages
    - Context preservation
    """
    
    def __init__(self):
        self.exception_handlers = {
            ExceptionCategory.MATERIAL: self.handle_material_exception,
            ExceptionCategory.PRODUCTION: self.handle_production_exception,
            ExceptionCategory.EQUIPMENT: self.handle_equipment_exception,
            ExceptionCategory.QUALITY: self.handle_quality_exception,
            ExceptionCategory.CANCELLATION: self.handle_cancellation_exception,
            ExceptionCategory.SYSTEM: self.handle_system_exception,
        }
    
    def handle_exception(self, exception: MESException) -> Dict[str, Any]:
        """
        Handle any MES exception
        
        Args:
            exception: MESException instance
        
        Returns:
            dict with formatted error response
        """
        # Get handler based on exception category
        category = self._get_category_from_code(exception.exception_code)
        handler = self.exception_handlers.get(category, self.handle_system_exception)
        
        return handler(exception)
    
    def _get_category_from_code(self, code: str) -> ExceptionCategory:
        """Extract category from exception code"""
        if code.startswith("EX-MAT"):
            return ExceptionCategory.MATERIAL
        elif code.startswith("EX-PROD"):
            return ExceptionCategory.PRODUCTION
        elif code.startswith("EX-EQ"):
            return ExceptionCategory.EQUIPMENT
        elif code.startswith("EX-Q"):
            return ExceptionCategory.QUALITY
        elif code.startswith("EX-CANCEL"):
            return ExceptionCategory.CANCELLATION
        else:
            return ExceptionCategory.SYSTEM
    
    def handle_material_exception(self, exception: MESException) -> Dict[str, Any]:
        """
        Handle material exceptions (EX-MAT-001 to EX-MAT-008)
        
        Scenarios:
        - EX-MAT-001: Material shortage
        - EX-MAT-002: Partial material availability
        - EX-MAT-003: Material transfer failure
        - EX-MAT-004: Wrong material transferred
        - EX-MAT-005: Damaged material
        - EX-MAT-006: Inventory mismatch
        - EX-MAT-007: Expired material
        - EX-MAT-008: Alternate material
        """
        return self._format_exception_response(
            exception,
            title="Material Issue",
            category="material",
            user_message=self._get_material_user_message(exception.exception_code, exception.context)
        )
    
    def handle_production_exception(self, exception: MESException) -> Dict[str, Any]:
        """
        Handle production exceptions (EX-PROD-001 to EX-PROD-010)
        
        Scenarios:
        - EX-PROD-001: Partial job card completion
        - EX-PROD-002: Over production
        - EX-PROD-003: Under production
        - EX-PROD-004: Wrong operation performed
        - EX-PROD-005: Operation sequence violation
        - EX-PROD-006: Incorrect parameters used
        - EX-PROD-007: Unreported production
        - EX-PROD-008: Duplicate production reporting
        - EX-PROD-009: Production without job card
        - EX-PROD-010: Unauthorized substitution
        """
        return self._format_exception_response(
            exception,
            title="Production Issue",
            category="production",
            user_message=self._get_production_user_message(exception.exception_code, exception.context)
        )
    
    def handle_equipment_exception(self, exception: MESException) -> Dict[str, Any]:
        """
        Handle equipment exceptions (EX-EQ-001 to EX-EQ-008)
        
        Scenarios:
        - EX-EQ-001: Machine breakdown
        - EX-EQ-002: Workstation unavailable
        - EX-EQ-003: Alternate workstation required
        - EX-EQ-004: Tooling not available
        - EX-EQ-005: Calibration expired
        """
        return self._format_exception_response(
            exception,
            title="Equipment Issue",
            category="equipment",
            user_message=self._get_equipment_user_message(exception.exception_code, exception.context)
        )
    
    def handle_quality_exception(self, exception: MESException) -> Dict[str, Any]:
        """
        Handle quality exceptions (EX-Q-001 to EX-Q-008)
        
        Scenarios:
        - EX-Q-001: Quality rejection during production
        - EX-Q-002: First article inspection failed
        - EX-Q-003: In-process inspection failed
        - EX-Q-004: Final inspection failed
        """
        return self._format_exception_response(
            exception,
            title="Quality Issue",
            category="quality",
            user_message=self._get_quality_user_message(exception.exception_code, exception.context)
        )
    
    def handle_cancellation_exception(self, exception: MESException) -> Dict[str, Any]:
        """
        Handle cancellation exceptions (EX-CANCEL-001 to EX-CANCEL-006)
        
        Scenarios:
        - EX-CANCEL-001: Job card cancellation
        - EX-CANCEL-002: Work order cancellation
        - EX-CANCEL-003: Production plan cancellation
        """
        return self._format_exception_response(
            exception,
            title="Cancellation",
            category="cancellation",
            user_message=self._get_cancellation_user_message(exception.exception_code, exception.context)
        )
    
    def handle_system_exception(self, exception: MESException) -> Dict[str, Any]:
        """
        Handle system exceptions (EX-SYS-001 to EX-SYS-006)
        
        Scenarios:
        - EX-SYS-001: Stock entry creation failure
        - EX-SYS-002: Database error
        - EX-SYS-003: Configuration error
        """
        # Log system exceptions immediately
        frappe.log_error(
            title=f"MES System Error: {exception.exception_code}",
            message=f"{exception.message}\nContext: {exception.context}"
        )
        
        return self._format_exception_response(
            exception,
            title="System Error",
            category="system",
            user_message="A system error occurred. Please contact the MES Administrator."
        )
    
    def _format_exception_response(
        self,
        exception: MESException,
        title: str,
        category: str,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Format exception response consistently
        
        Args:
            exception: Exception instance
            title: User-friendly title
            category: Exception category
            user_message: User-friendly message
        
        Returns:
            dict with formatted response
        """
        return {
            'exception_code': exception.exception_code,
            'title': title,
            'message': exception.message,
            'user_message': user_message,
            'category': category,
            'severity': exception.severity.value,
            'context': exception.context,
            'can_proceed': exception.severity != ExceptionSeverity.CRITICAL
        }
    
    def _get_material_user_message(self, code: str, context: dict) -> str:
        """Get user-friendly message for material exceptions"""
        messages = {
            'EX-MAT-001': "Material shortage detected. Please request material from Stores.",
            'EX-MAT-002': "Partial material available. Shortage quantity needs to be arranged.",
            'EX-MAT-003': "Material transfer failed. Please check warehouse configuration.",
            'EX-MAT-004': "Wrong material transferred. Please verify material code.",
            'EX-MAT-005': "Damaged material detected. Please quarantine and report.",
            'EX-MAT-006': "Inventory mismatch found. Please conduct stock verification.",
            'EX-MAT-007': "Material expired. Please arrange replacement.",
            'EX-MAT-008': "Alternate material approved. Please update BOM."
        }
        return messages.get(code, "Material issue detected. Please check details.")
    
    def _get_production_user_message(self, code: str, context: dict) -> str:
        """Get user-friendly message for production exceptions"""
        messages = {
            'EX-PROD-001': "Job card partially completed. Please review remaining quantity.",
            'EX-PROD-002': "Over production detected. Please verify reported quantity.",
            'EX-PROD-003': "Under production detected. Please complete remaining quantity.",
            'EX-PROD-004': "Wrong operation performed. Please verify operation sequence.",
            'EX-PROD-005': "Operation sequence violation. Previous operations must be completed first.",
            'EX-PROD-006': "Incorrect parameters used. Please verify operation settings.",
            'EX-PROD-007': "Unreported production found. Please update production records.",
            'EX-PROD-008': "Duplicate production reporting. Please verify entries.",
            'EX-PROD-009': "Production without job card. Please create job card first.",
            'EX-PROD-010': "Unauthorized substitution. Please obtain approval."
        }
        return messages.get(code, "Production issue detected. Please check details.")
    
    def _get_equipment_user_message(self, code: str, context: dict) -> str:
        """Get user-friendly message for equipment exceptions"""
        messages = {
            'EX-EQ-001': "Machine breakdown reported. Maintenance team notified.",
            'EX-EQ-002': "Workstation unavailable. Please select alternate workstation.",
            'EX-EQ-003': "Alternate workstation required. Please reassign operation.",
            'EX-EQ-004': "Tooling not available. Please request from Tool Room.",
            'EX-EQ-005': "Calibration expired. Please recalibrate before use."
        }
        return messages.get(code, "Equipment issue detected. Please check details.")
    
    def _get_quality_user_message(self, code: str, context: dict) -> str:
        """Get user-friendly message for quality exceptions"""
        messages = {
            'EX-Q-001': "Quality rejection during production. Please review defect.",
            'EX-Q-002': "First article inspection failed. Please adjust process.",
            'EX-Q-003': "In-process inspection failed. Please stop and review.",
            'EX-Q-004': "Final inspection failed. Material cannot proceed."
        }
        return messages.get(code, "Quality issue detected. Please check details.")
    
    def _get_cancellation_user_message(self, code: str, context: dict) -> str:
        """Get user-friendly message for cancellation exceptions"""
        messages = {
            'EX-CANCEL-001': "Job card cancelled. Please create new job card if needed.",
            'EX-CANCEL-002': "Work order cancelled. All associated job cards will be cancelled.",
            'EX-CANCEL-003': "Production plan cancelled. Please review schedule."
        }
        return messages.get(code, "Cancellation processed.")
    
    def log_exception(
        self,
        exception: MESException,
        reference_doctype: str,
        reference_name: str
    ) -> None:
        """
        Log exception with context
        
        Args:
            exception: MESException instance
            reference_doctype: Reference DocType
            reference_name: Reference document name
        """
        log_title = f"MES {exception.exception_code}: {exception.message[:50]}"
        
        log_message = f"""
Exception Code: {exception.exception_code}
Severity: {exception.severity.value}
Category: {self._get_category_from_code(exception.exception_code).value}
Reference: {reference_doctype} - {reference_name}

Message:
{exception.message}

Context:
{exception.context}
        """.strip()
        
        frappe.log_error(title=log_title, message=log_message)


# Convenience functions for raising exceptions

def raise_material_exception(
    message: str,
    code: str = "EX-MAT-001",
    **context
) -> None:
    """Raise material exception"""
    exc = MaterialException(message, code).with_context(**context)
    raise exc


def raise_production_exception(
    message: str,
    code: str = "EX-PROD-001",
    **context
) -> None:
    """Raise production exception"""
    exc = ProductionException(message, code).with_context(**context)
    raise exc


def raise_equipment_exception(
    message: str,
    code: str = "EX-EQ-001",
    **context
) -> None:
    """Raise equipment exception"""
    exc = EquipmentException(message, code).with_context(**context)
    raise exc


def raise_quality_exception(
    message: str,
    code: str = "EX-Q-001",
    **context
) -> None:
    """Raise quality exception"""
    exc = QualityException(message, code).with_context(**context)
    raise exc


def raise_cancellation_exception(
    message: str,
    code: str = "EX-CANCEL-001",
    **context
) -> None:
    """Raise cancellation exception"""
    exc = CancellationException(message, code).with_context(**context)
    raise exc


def raise_system_exception(
    message: str,
    code: str = "EX-SYS-001",
    **context
) -> None:
    """Raise system exception"""
    exc = SystemException(message, code).with_context(**context)
    raise exc


@frappe.whitelist()
def handle_exception(
    exception_code: str,
    message: str,
    reference_doctype: str,
    reference_name: str,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Whitelisted method to handle exceptions
    
    Args:
        exception_code: EX-XXX code
        message: Error message
        reference_doctype: Reference DocType
        reference_name: Reference document name
        context: Additional context
    
    Returns:
        formatted exception response
    """
    handler = ExceptionHandler()
    
    # Create appropriate exception
    if exception_code.startswith("EX-MAT"):
        exc = MaterialException(message, exception_code)
    elif exception_code.startswith("EX-PROD"):
        exc = ProductionException(message, exception_code)
    elif exception_code.startswith("EX-EQ"):
        exc = EquipmentException(message, exception_code)
    elif exception_code.startswith("EX-Q"):
        exc = QualityException(message, exception_code)
    elif exception_code.startswith("EX-CANCEL"):
        exc = CancellationException(message, exception_code)
    else:
        exc = SystemException(message, exception_code)
    
    if context:
        exc.with_context(**context)
    
    # Log and handle
    handler.log_exception(exc, reference_doctype, reference_name)
    return handler.handle_exception(exc)
