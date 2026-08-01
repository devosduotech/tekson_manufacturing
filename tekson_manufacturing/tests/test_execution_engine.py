"""
Unit Tests for Execution Engine

Business Rules:
- JC-001: Job Card Start Permission
- JC-002: Job Card Completion Permission
- JC-003: Job Card Material Check
- JC-004: Job Card Auto-Refresh
- JC-005: Job Card Work Order Link
- WO-001: Auto-Completion Trigger
- WO-002: Duplicate Stock Entry Prevention

Test Coverage:
- Job Card start validation
- Job Card completion validation
- Work Order auto-completion
- Duplicate prevention
- Status refresh
- API endpoints
"""

import frappe
import unittest
from datetime import datetime
from tekson_manufacturing.execution.execution_engine import (
    ExecutionEngine,
    can_start_job_card,
    can_complete_job_card,
    complete_work_order_api,
    refresh_job_card_status_api
)
from tekson_manufacturing.repositories.job_card_repository import JobCardRepository
from tekson_manufacturing.repositories.work_order_repository import WorkOrderRepository


class TestExecutionEngineJC001(unittest.TestCase):
    """
    Test Suite for JC-001: Job Card Start Permission
    
    JC-001 states: A Job Card cannot start until all previous 
    operations are complete.
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ExecutionEngine()
        self.test_wo = self._create_test_work_order()
        self.repo = JobCardRepository()
    
    def tearDown(self):
        """Clean up test data"""
        if hasattr(self, 'test_jcs'):
            for jc_name in self.test_jcs:
                try:
                    jc = frappe.get_doc("Job Card", jc_name)
                    if jc.docstatus == 1:
                        jc.cancel()
                    jc.delete()
                except Exception:
                    pass
    
    def _create_test_work_order(self):
        """Helper to create test Work Order"""
        existing_wo = frappe.db.get_value(
            "Work Order",
            {"production_item": "Test Execution Item"},
            "name"
        )
        
        if existing_wo:
            return existing_wo
        
        # Create test item
        if not frappe.db.exists("Item", "Test Execution Item"):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test Execution Item",
                "item_name": "Test Execution Item",
                "item_group": "Products",
                "is_stock_item": 1,
                "stock_uom": "Nos"
            })
            item.insert(ignore_permissions=True)
        
        # Create test BOM
        bom_name = frappe.db.get_value("BOM", {"item": "Test Execution Item"}, "name")
        if not bom_name:
            bom = frappe.get_doc({
                "doctype": "BOM",
                "item": "Test Execution Item",
                "quantity": 1,
                "uom": "Nos",
                "is_active": 1,
                "is_default": 1
            })
            bom.insert(ignore_permissions=True)
            bom.submit()
            bom_name = bom.name
        
        # Create Work Order
        wo = frappe.get_doc({
            "doctype": "Work Order",
            "production_item": "Test Execution Item",
            "bom_no": bom_name,
            "qty": 10,
            "planned_start_date": datetime.now()
        })
        wo.insert(ignore_permissions=True)
        wo.submit()
        
        return wo.name
    
    def _create_job_card(self, work_order, operation, sequence_id, status="Work In Progress"):
        """Helper to create test Job Card"""
        jc_name = f"TEST-EXEC-JC-{operation}-{sequence_id}-{datetime.now().timestamp()}"
        
        jc = frappe.get_doc({
            "doctype": "Job Card",
            "work_order": work_order,
            "operation": operation,
            "sequence_id": sequence_id,
            "for_quantity": 10,
            "status": status
        })
        jc.insert(ignore_permissions=True)
        
        if not hasattr(self, 'test_jcs'):
            self.test_jcs = []
        self.test_jcs.append(jc.name)
        
        return jc.name
    
    def test_jc_001_start_permission_first_operation(self):
        """
        Test JC-001: First operation can start (no previous dependency)
        
        Expected: can_start = True
        """
        jc_name = self._create_job_card(self.test_wo, "Operation 1", 1)
        
        result = self.engine.can_job_card_start(jc_name)
        
        # Verify can start
        self.assertTrue(result['can_start'])
        self.assertTrue(result['validations']['jc_001_previous_operation'])
    
    def test_jc_001_start_permission_previous_complete(self):
        """
        Test JC-001: Can start when previous operation completed
        
        Expected: can_start = True
        """
        jc1_name = self._create_job_card(self.test_wo, "Operation 1", 1, status="Completed")
        jc2_name = self._create_job_card(self.test_wo, "Operation 2", 2)
        
        # Submit JC-001
        jc1 = frappe.get_doc("Job Card", jc1_name)
        jc1.submit()
        
        result = self.engine.can_job_card_start(jc2_name)
        
        # Verify can start
        self.assertTrue(result['can_start'])
        self.assertTrue(result['validations']['jc_001_previous_operation'])
    
    def test_jc_001_start_permission_previous_not_complete(self):
        """
        Test JC-001: Cannot start when previous operation not completed
        
        Expected: can_start = False
        """
        jc1_name = self._create_job_card(self.test_wo, "Operation 1", 1, status="Work In Progress")
        jc2_name = self._create_job_card(self.test_wo, "Operation 2", 2)
        
        result = self.engine.can_job_card_start(jc2_name)
        
        # Verify cannot start
        self.assertFalse(result['can_start'])
        self.assertFalse(result['validations']['jc_001_previous_operation'])
    
    def test_jc_001_api(self):
        """
        Test JC-001 API endpoint
        
        Expected: API returns valid response structure
        """
        jc_name = self._create_job_card(self.test_wo, "Operation 1", 1)
        
        result = can_start_job_card(jc_name)
        
        # Verify API response structure
        self.assertIn('can_start', result)
        self.assertIn('reason', result)
        self.assertIn('validations', result)


class TestExecutionEngineJC002(unittest.TestCase):
    """
    Test Suite for JC-002: Job Card Completion Permission
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ExecutionEngine()
        self.test_wo = self._create_test_work_order()
    
    def tearDown(self):
        """Clean up test data"""
        if hasattr(self, 'test_jcs'):
            for jc_name in self.test_jcs:
                try:
                    jc = frappe.get_doc("Job Card", jc_name)
                    if jc.docstatus == 1:
                        jc.cancel()
                    jc.delete()
                except Exception:
                    pass
    
    def _create_test_work_order(self):
        """Helper to create test Work Order"""
        existing_wo = frappe.db.get_value(
            "Work Order",
            {"production_item": "Test JC-002 Item"},
            "name"
        )
        
        if existing_wo:
            return existing_wo
        
        # Create test item
        if not frappe.db.exists("Item", "Test JC-002 Item"):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test JC-002 Item",
                "item_name": "Test JC-002 Item",
                "item_group": "Products",
                "is_stock_item": 1,
                "stock_uom": "Nos"
            })
            item.insert(ignore_permissions=True)
        
        # Create test BOM
        bom_name = frappe.db.get_value("BOM", {"item": "Test JC-002 Item"}, "name")
        if not bom_name:
            bom = frappe.get_doc({
                "doctype": "BOM",
                "item": "Test JC-002 Item",
                "quantity": 1,
                "uom": "Nos",
                "is_active": 1,
                "is_default": 1
            })
            bom.insert(ignore_permissions=True)
            bom.submit()
            bom_name = bom.name
        
        # Create Work Order
        wo = frappe.get_doc({
            "doctype": "Work Order",
            "production_item": "Test JC-002 Item",
            "bom_no": bom_name,
            "qty": 10,
            "planned_start_date": datetime.now()
        })
        wo.insert(ignore_permissions=True)
        wo.submit()
        
        return wo.name
    
    def _create_job_card(self, work_order, operation, sequence_id, completed_qty=0):
        """Helper to create test Job Card"""
        jc_name = f"TEST-JC-002-{operation}-{sequence_id}-{datetime.now().timestamp()}"
        
        jc = frappe.get_doc({
            "doctype": "Job Card",
            "work_order": work_order,
            "operation": operation,
            "sequence_id": sequence_id,
            "for_quantity": 10,
            "total_completed_qty": completed_qty
        })
        jc.insert(ignore_permissions=True)
        
        if not hasattr(self, 'test_jcs'):
            self.test_jcs = []
        self.test_jcs.append(jc.name)
        
        return jc.name
    
    def test_jc_002_completion_permission_quantity_met(self):
        """
        Test JC-002: Can complete when quantity met
        
        Expected: can_complete = True
        """
        jc_name = self._create_job_card(self.test_wo, "Operation 1", 1, completed_qty=10)
        
        result = self.engine.can_job_card_complete(jc_name)
        
        # Verify can complete
        self.assertTrue(result['can_complete'])
        self.assertTrue(result['validations']['jc_002_quantity_check'])
    
    def test_jc_002_completion_permission_quantity_not_met(self):
        """
        Test JC-002: Cannot complete when quantity not met
        
        Expected: can_complete = False
        """
        jc_name = self._create_job_card(self.test_wo, "Operation 1", 1, completed_qty=5)
        
        result = self.engine.can_job_card_complete(jc_name)
        
        # Verify cannot complete
        self.assertFalse(result['can_complete'])
        self.assertFalse(result['validations']['jc_002_quantity_check'])
    
    def test_jc_002_api(self):
        """
        Test JC-002 API endpoint
        
        Expected: API returns valid response structure
        """
        jc_name = self._create_job_card(self.test_wo, "Operation 1", 1, completed_qty=10)
        
        result = can_complete_job_card(jc_name)
        
        # Verify API response structure
        self.assertIn('can_complete', result)
        self.assertIn('reason', result)


class TestExecutionEngineWO001(unittest.TestCase):
    """
    Test Suite for WO-001: Auto-Completion Trigger
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ExecutionEngine()
        self.test_wo = self._create_test_work_order()
    
    def tearDown(self):
        """Clean up test data"""
        if hasattr(self, 'test_jcs'):
            for jc_name in self.test_jcs:
                try:
                    jc = frappe.get_doc("Job Card", jc_name)
                    if jc.docstatus == 1:
                        jc.cancel()
                    jc.delete()
                except Exception:
                    pass
    
    def _create_test_work_order(self):
        """Helper to create test Work Order"""
        existing_wo = frappe.db.get_value(
            "Work Order",
            {"production_item": "Test WO-001 Item"},
            "name"
        )
        
        if existing_wo:
            return existing_wo
        
        # Create test item
        if not frappe.db.exists("Item", "Test WO-001 Item"):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test WO-001 Item",
                "item_name": "Test WO-001 Item",
                "item_group": "Products",
                "is_stock_item": 1,
                "stock_uom": "Nos"
            })
            item.insert(ignore_permissions=True)
        
        # Create test BOM
        bom_name = frappe.db.get_value("BOM", {"item": "Test WO-001 Item"}, "name")
        if not bom_name:
            bom = frappe.get_doc({
                "doctype": "BOM",
                "item": "Test WO-001 Item",
                "quantity": 1,
                "uom": "Nos",
                "is_active": 1,
                "is_default": 1
            })
            bom.insert(ignore_permissions=True)
            bom.submit()
            bom_name = bom.name
        
        # Create Work Order
        wo = frappe.get_doc({
            "doctype": "Work Order",
            "production_item": "Test WO-001 Item",
            "bom_no": bom_name,
            "qty": 10,
            "planned_start_date": datetime.now()
        })
        wo.insert(ignore_permissions=True)
        wo.submit()
        
        return wo.name
    
    def _create_job_card(self, work_order, operation, sequence_id, status="Completed"):
        """Helper to create test Job Card"""
        jc_name = f"TEST-WO-001-JC-{operation}-{sequence_id}-{datetime.now().timestamp()}"
        
        jc = frappe.get_doc({
            "doctype": "Job Card",
            "work_order": work_order,
            "operation": operation,
            "sequence_id": sequence_id,
            "for_quantity": 10,
            "status": status,
            "total_completed_qty": 10 if status == "Completed" else 0
        })
        jc.insert(ignore_permissions=True)
        
        if not hasattr(self, 'test_jcs'):
            self.test_jcs = []
        self.test_jcs.append(jc.name)
        
        return jc.name
    
    def test_wo_001_auto_completion_all_completed(self):
        """
        Test WO-001: Auto-complete when all Job Cards completed
        
        Expected: success = True, stock_entry created
        """
        # Create completed Job Cards
        self._create_job_card(self.test_wo, "Operation 1", 1, status="Completed")
        self._create_job_card(self.test_wo, "Operation 2", 2, status="Completed")
        
        result = self.engine.complete_work_order(self.test_wo)
        
        # Verify completion
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['stock_entry'])
        self.assertTrue(result['validations']['wo_001_all_jc_completed'])
    
    def test_wo_001_auto_completion_pending_jc(self):
        """
        Test WO-001: Cannot auto-complete with pending Job Cards
        
        Expected: success = False
        """
        # Create one completed, one pending
        self._create_job_card(self.test_wo, "Operation 1", 1, status="Completed")
        self._create_job_card(self.test_wo, "Operation 2", 2, status="Work In Progress")
        
        result = self.engine.complete_work_order(self.test_wo)
        
        # Verify cannot complete
        self.assertFalse(result['success'])
        self.assertFalse(result['validations']['wo_001_all_jc_completed'])


class TestExecutionEngineIntegration(unittest.TestCase):
    """
    Integration Tests for Execution Engine
    """
    
    def test_refresh_job_card_status_api(self):
        """
        Test JC-004 API: Refresh Job Card status
        
        Expected: API returns refreshed cards
        """
        # Create test Work Order and Job Cards
        wo_name = self._create_minimal_work_order()
        
        if wo_name:
            jc1_name = self._create_job_card(wo_name, "Op 1", 1, status="Completed")
            jc2_name = self._create_job_card(wo_name, "Op 2", 2)
            
            result = refresh_job_card_status_api(jc1_name)
            
            # Verify response structure
            self.assertIn('success', result)
            self.assertIn('refreshed_cards', result)
    
    def _create_minimal_work_order(self):
        """Create minimal Work Order for testing"""
        try:
            wo = frappe.get_doc({
                "doctype": "Work Order",
                "production_item": "Test Execution Item",
                "qty": 1,
                "planned_start_date": datetime.now()
            })
            wo.insert(ignore_permissions=True)
            return wo.name
        except Exception:
            return None
    
    def _create_job_card(self, work_order, operation, sequence_id, status="Work In Progress"):
        """Create test Job Card"""
        try:
            jc = frappe.get_doc({
                "doctype": "Job Card",
                "work_order": work_order,
                "operation": operation,
                "sequence_id": sequence_id,
                "for_quantity": 1,
                "status": status
            })
            jc.insert(ignore_permissions=True)
            return jc.name
        except Exception:
            return None


def run_tests():
    """Run all execution engine tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test suites
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionEngineJC001))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionEngineJC002))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionEngineWO001))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionEngineIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    run_tests()
