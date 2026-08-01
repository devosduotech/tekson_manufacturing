import frappe
import unittest
from tekson_manufacturing.diagnostics.exception_handler import (
    ExceptionHandler,
    MaterialException,
    ProductionException,
    EquipmentException,
    QualityException,
    CancellationException,
    SystemException,
    ExceptionSeverity,
    raise_material_exception,
    raise_production_exception,
    handle_exception
)


class TestExceptionCategories(unittest.TestCase):
    """Test exception category classification"""
    
    def test_all_categories_defined(self):
        """Test all 6 exception categories are defined"""
        from tekson_manufacturing.diagnostics.exception_handler import ExceptionCategory
        
        categories = [c.value for c in ExceptionCategory]
        
        expected = ["EX-MAT", "EX-PROD", "EX-EQ", "EX-Q", "EX-CANCEL", "EX-SYS"]
        
        for exp in expected:
            self.assertIn(exp, categories)


class TestMaterialExceptions(unittest.TestCase):
    """Test material exceptions (EX-MAT-*)"""
    
    def test_ex_mat_001_material_shortage(self):
        """EX-MAT-001: Material shortage exception"""
        exc = MaterialException("Material not available", "EX-MAT-001")
        self.assertEqual(exc.exception_code, "EX-MAT-001")
        self.assertEqual(exc.severity, ExceptionSeverity.HIGH)
    
    def test_ex_mat_002_partial_availability(self):
        """EX-MAT-002: Partial material availability"""
        exc = MaterialException("Partial stock available", "EX-MAT-002")
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertEqual(result['exception_code'], "EX-MAT-002")
        self.assertEqual(result['category'], "material")
        self.assertIn("Partial material", result['user_message'])
    
    def test_ex_mat_003_transfer_failure(self):
        """EX-MAT-003: Material transfer failure"""
        exc = MaterialException("Transfer failed", "EX-MAT-003")
        exc.with_context(warehouse="WIP-W")
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertIn("warehouse", result['context'])
        self.assertEqual(result['context']['warehouse'], "WIP-W")


class TestProductionExceptions(unittest.TestCase):
    """Test production exceptions (EX-PROD-*)"""
    
    def test_ex_prod_001_partial_completion(self):
        """EX-PROD-001: Partial job card completion"""
        exc = ProductionException("Job card partially completed", "EX-PROD-001")
        self.assertEqual(exc.exception_code, "EX-PROD-001")
    
    def test_ex_prod_005_sequence_violation(self):
        """EX-PROD-005: Operation sequence violation"""
        exc = ProductionException(
            "Previous operation not complete",
            "EX-PROD-005"
        )
        exc.with_context(
            current_operation="Op 30",
            pending_operation="Op 20"
        )
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertEqual(result['exception_code'], "EX-PROD-005")
        self.assertIn("sequence", result['user_message'].lower())
    
    def test_ex_prod_009_no_job_card(self):
        """EX-PROD-009: Production without job card"""
        exc = ProductionException("No job card found", "EX-PROD-009")
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertIn("job card", result['user_message'].lower())


class TestEquipmentExceptions(unittest.TestCase):
    """Test equipment exceptions (EX-EQ-*)"""
    
    def test_ex_eq_001_machine_breakdown(self):
        """EX-EQ-001: Machine breakdown"""
        exc = EquipmentException("Machine breakdown", "EX-EQ-001")
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertEqual(result['category'], "equipment")
        self.assertIn("breakdown", result['user_message'].lower())
    
    def test_ex_eq_005_calibration_expired(self):
        """EX-EQ-005: Calibration expired"""
        exc = EquipmentException("Calibration expired", "EX-EQ-005")
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertIn("calibration", result['user_message'].lower())


class TestQualityExceptions(unittest.TestCase):
    """Test quality exceptions (EX-Q-*)"""
    
    def test_ex_q_001_quality_rejection(self):
        """EX-Q-001: Quality rejection during production"""
        exc = QualityException("Quality rejection", "EX-Q-001")
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertEqual(result['category'], "quality")
        self.assertIn("rejection", result['user_message'].lower())
    
    def test_ex_q_002_first_article_failed(self):
        """EX-Q-002: First article inspection failed"""
        exc = QualityException("First article failed", "EX-Q-002")
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertIn("first article", result['user_message'].lower())


class TestCancellationExceptions(unittest.TestCase):
    """Test cancellation exceptions (EX-CANCEL-*)"""
    
    def test_ex_cancel_001_job_card_cancellation(self):
        """EX-CANCEL-001: Job card cancellation"""
        exc = CancellationException("Job card cancelled", "EX-CANCEL-001")
        
        # Cancellation exceptions are MEDIUM severity
        self.assertEqual(exc.severity, ExceptionSeverity.MEDIUM)
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertEqual(result['category'], "cancellation")
    
    def test_ex_cancel_002_work_order_cancellation(self):
        """EX-CANCEL-002: Work order cancellation"""
        exc = CancellationException(
            "Work order cancelled",
            "EX-CANCEL-002"
        )
        exc.with_context(job_cards=["JC-001", "JC-002"])
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertIn("job_cards", result['context'])


class TestSystemExceptions(unittest.TestCase):
    """Test system exceptions (EX-SYS-*)"""
    
    def test_ex_sys_001_stock_entry_failure(self):
        """EX-SYS-001: Stock entry creation failure"""
        exc = SystemException(
            "Failed to create Stock Entry",
            "EX-SYS-001"
        )
        
        # System exceptions are CRITICAL severity
        self.assertEqual(exc.severity, ExceptionSeverity.CRITICAL)
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertEqual(result['category'], "system")
        self.assertEqual(result['severity'], "critical")
        self.assertFalse(result['can_proceed'])


class TestExceptionHandling(unittest.TestCase):
    """Test exception handling functionality"""
    
    def test_exception_with_context(self):
        """Test exception context preservation"""
        exc = MaterialException("Shortage", "EX-MAT-001")
        exc.with_context(
            item_code="ITEM-001",
            required_qty=100,
            available_qty=60
        )
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        self.assertEqual(result['context']['item_code'], "ITEM-001")
        self.assertEqual(result['context']['required_qty'], 100)
    
    def test_exception_formatting(self):
        """Test exception response formatting"""
        exc = ProductionException("Error", "EX-PROD-001")
        
        handler = ExceptionHandler()
        result = handler.handle_exception(exc)
        
        # Check all required fields
        self.assertIn('exception_code', result)
        self.assertIn('title', result)
        self.assertIn('message', result)
        self.assertIn('user_message', result)
        self.assertIn('category', result)
        self.assertIn('severity', result)
        self.assertIn('context', result)
        self.assertIn('can_proceed', result)
    
    def test_severity_levels(self):
        """Test different severity levels"""
        # HIGH severity
        exc_high = MaterialException("Error", "EX-MAT-001")
        self.assertEqual(exc_high.severity, ExceptionSeverity.HIGH)
        
        # MEDIUM severity (cancellation)
        exc_med = CancellationException("Cancelled", "EX-CANCEL-001")
        self.assertEqual(exc_med.severity, ExceptionSeverity.MEDIUM)
        
        # CRITICAL severity (system)
        exc_crit = SystemException("Critical error", "EX-SYS-001")
        self.assertEqual(exc_crit.severity, ExceptionSeverity.CRITICAL)


class TestWhitelistedMethods(unittest.TestCase):
    """Test whitelisted exception handling methods"""
    
    def test_handle_exception_material(self):
        """Test handle_exception with material exception"""
        result = handle_exception(
            exception_code="EX-MAT-001",
            message="Material shortage",
            reference_doctype="Job Card",
            reference_name="JC-2026-001",
            context={"item_code": "ITEM-001"}
        )
        
        self.assertEqual(result['exception_code'], "EX-MAT-001")
        self.assertEqual(result['category'], "material")
    
    def test_handle_exception_production(self):
        """Test handle_exception with production exception"""
        result = handle_exception(
            exception_code="EX-PROD-005",
            message="Sequence violation",
            reference_doctype="Job Card",
            reference_name="JC-2026-001"
        )
        
        self.assertEqual(result['exception_code'], "EX-PROD-005")
        self.assertEqual(result['category'], "production")
    
    def test_handle_exception_system(self):
        """Test handle_exception with system exception"""
        result = handle_exception(
            exception_code="EX-SYS-001",
            message="System error",
            reference_doctype="Stock Entry",
            reference_name="SE-2026-001"
        )
        
        self.assertEqual(result['exception_code'], "EX-SYS-001")
        self.assertEqual(result['category'], "system")
        self.assertEqual(result['severity'], "critical")


class TestExceptionRaiseFunctions(unittest.TestCase):
    """Test convenience raise functions"""
    
    def test_raise_material_exception(self):
        """Test raise_material_exception function"""
        with self.assertRaises(MaterialException) as context:
            raise_material_exception(
                "Material not available",
                "EX-MAT-001",
                item_code="ITEM-001"
            )
        
        exc = context.exception
        self.assertEqual(exc.exception_code, "EX-MAT-001")
        self.assertIn("item_code", exc.context)
    
    def test_raise_production_exception(self):
        """Test raise_production_exception function"""
        with self.assertRaises(ProductionException) as context:
            raise_production_exception(
                "Operation sequence error",
                "EX-PROD-005"
            )
        
        exc = context.exception
        self.assertEqual(exc.exception_code, "EX-PROD-005")


if __name__ == '__main__':
    unittest.main()
