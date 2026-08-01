"""
Unit Tests for Dependency Engine

Business Rules:
- DV-001: Previous operation validation
- DV-002: Sequence validation

Test Coverage:
- Previous operation validation
- Sequence validation
- Dependency status
- API endpoints
"""

import frappe
import unittest
from datetime import datetime
from tekson_manufacturing.validation.dependency_engine import (
    DependencyEngine,
    validate_previous_operation,
    validate_sequence,
    get_dependency_status,
    can_job_card_start
)
from tekson_manufacturing.repositories.job_card_repository import JobCardRepository


class TestDependencyEngineDV001(unittest.TestCase):
    """
    Test Suite for DV-001: Previous Operation Validation
    
    DV-001 states: A Job Card cannot start until all previous 
    operations are complete.
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_wo = self._create_test_work_order()
        self.repo = JobCardRepository()
    
    def tearDown(self):
        """Clean up test data"""
        # Delete test Job Cards
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
            {"production_item": "Test DV Item"},
            "name"
        )
        
        if existing_wo:
            return existing_wo
        
        # Create test item
        if not frappe.db.exists("Item", "Test DV Item"):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test DV Item",
                "item_name": "Test DV Item",
                "item_group": "Products",
                "is_stock_item": 1,
                "stock_uom": "Nos"
            })
            item.insert(ignore_permissions=True)
        
        # Create test BOM
        bom_name = frappe.db.get_value("BOM", {"item": "Test DV Item"}, "name")
        if not bom_name:
            bom = frappe.get_doc({
                "doctype": "BOM",
                "item": "Test DV Item",
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
            "production_item": "Test DV Item",
            "bom_no": bom_name,
            "qty": 10,
            "planned_start_date": datetime.now()
        })
        wo.insert(ignore_permissions=True)
        wo.submit()
        
        return wo.name
    
    def _create_job_card(self, work_order, operation, sequence_id, status="Work In Progress"):
        """Helper to create test Job Card"""
        jc_name = f"TEST-JC-{operation}-{sequence_id}-{datetime.now().timestamp()}"
        
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
    
    def test_dv_001_first_operation_no_dependency(self):
        """
        Test DV-001: First operation has no previous dependency
        
        Expected: is_valid = True, message indicates no dependency
        """
        jc_name = self._create_job_card(self.test_wo, "Operation 1", 1)
        
        engine = DependencyEngine(job_card=jc_name)
        result = engine.validate_previous_operation()
        
        # Verify validation passed
        self.assertTrue(result['is_valid'])
        self.assertIn("no previous dependency", result['message'].lower())
        
        # Verify no previous operation
        self.assertIsNone(result['previous_operation'])
    
    def test_dv_001_previous_operation_complete(self):
        """
        Test DV-001: Previous operation completed
        
        Scenario:
        - JC-001 (sequence 1): Completed
        - JC-002 (sequence 2): Trying to start
        
        Expected: is_valid = True
        """
        jc1_name = self._create_job_card(self.test_wo, "Operation 1", 1, status="Completed")
        jc2_name = self._create_job_card(self.test_wo, "Operation 2", 2)
        
        # Submit JC-001 to mark as completed
        jc1 = frappe.get_doc("Job Card", jc1_name)
        jc1.submit()
        
        engine = DependencyEngine(job_card=jc2_name)
        result = engine.validate_previous_operation()
        
        # Verify validation passed
        self.assertTrue(result['is_valid'])
        self.assertIn("completed", result['message'].lower())
        
        # Verify previous operation info
        self.assertIsNotNone(result['previous_operation'])
        self.assertEqual(result['previous_operation']['name'], jc1_name)
    
    def test_dv_001_previous_operation_not_complete(self):
        """
        Test DV-001: Previous operation not completed
        
        Scenario:
        - JC-001 (sequence 1): Work In Progress
        - JC-002 (sequence 2): Trying to start
        
        Expected: is_valid = False, appropriate error message
        """
        jc1_name = self._create_job_card(self.test_wo, "Operation 1", 1, status="Work In Progress")
        jc2_name = self._create_job_card(self.test_wo, "Operation 2", 2)
        
        engine = DependencyEngine(job_card=jc2_name)
        result = engine.validate_previous_operation()
        
        # Verify validation failed
        self.assertFalse(result['is_valid'])
        self.assertIn("not completed", result['message'].lower())
        
        # Verify diagnostic info
        self.assertIn('diagnostic', result)
        self.assertEqual(result['diagnostic']['type'], 'warning')
        self.assertIn('previous_job_card', result['diagnostic'])
    
    def test_dv_001_previous_operation_not_found(self):
        """
        Test DV-001: Previous operation Job Card not found
        
        Scenario:
        - JC-001 (sequence 1): Deleted
        - JC-002 (sequence 2): Exists
        
        Expected: is_valid = False, error message
        """
        jc_name = self._create_job_card(self.test_wo, "Operation 2", 2)
        
        # Manually set sequence_id to 2 (simulating missing sequence 1)
        jc = frappe.get_doc("Job Card", jc_name)
        jc.sequence_id = 2
        jc.save()
        
        engine = DependencyEngine(job_card=jc_name)
        result = engine.validate_previous_operation()
        
        # Verify validation failed
        self.assertFalse(result['is_valid'])
        self.assertIn("not found", result['message'].lower())
    
    def test_dv_001_api_validation(self):
        """
        Test DV-001 API endpoint
        
        Expected: API returns valid response structure
        """
        jc_name = self._create_job_card(self.test_wo, "Operation 1", 1)
        
        result = validate_previous_operation(jc_name)
        
        # Verify API response structure
        self.assertIn('is_valid', result)
        self.assertIn('message', result)
        self.assertIn('diagnostic', result)


class TestDependencyEngineDV002(unittest.TestCase):
    """
    Test Suite for DV-002: Sequence Validation
    
    DV-002 states: Operations must follow the defined sequence 
    without gaps.
    """
    
    def setUp(self):
        """Set up test fixtures"""
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
            {"production_item": "Test DV Seq Item"},
            "name"
        )
        
        if existing_wo:
            return existing_wo
        
        # Create test item
        if not frappe.db.exists("Item", "Test DV Seq Item"):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test DV Seq Item",
                "item_name": "Test DV Seq Item",
                "item_group": "Products",
                "is_stock_item": 1,
                "stock_uom": "Nos"
            })
            item.insert(ignore_permissions=True)
        
        # Create test BOM
        bom_name = frappe.db.get_value("BOM", {"item": "Test DV Seq Item"}, "name")
        if not bom_name:
            bom = frappe.get_doc({
                "doctype": "BOM",
                "item": "Test DV Seq Item",
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
            "production_item": "Test DV Seq Item",
            "bom_no": bom_name,
            "qty": 10,
            "planned_start_date": datetime.now()
        })
        wo.insert(ignore_permissions=True)
        wo.submit()
        
        return wo.name
    
    def _create_job_card(self, work_order, operation, sequence_id):
        """Helper to create test Job Card"""
        jc_name = f"TEST-JC-SEQ-{operation}-{sequence_id}-{datetime.now().timestamp()}"
        
        jc = frappe.get_doc({
            "doctype": "Job Card",
            "work_order": work_order,
            "operation": operation,
            "sequence_id": sequence_id,
            "for_quantity": 10
        })
        jc.insert(ignore_permissions=True)
        
        if not hasattr(self, 'test_jcs'):
            self.test_jcs = []
        self.test_jcs.append(jc.name)
        
        return jc.name
    
    def test_dv_002_sequence_valid(self):
        """
        Test DV-002: Valid sequence (1, 2, 3, 4, 5)
        
        Expected: is_valid = True, no issues
        """
        # Create Job Cards with valid sequence
        self._create_job_card(self.test_wo, "Op 1", 1)
        self._create_job_card(self.test_wo, "Op 2", 2)
        self._create_job_card(self.test_wo, "Op 3", 3)
        
        engine = DependencyEngine(work_order=self.test_wo)
        result = engine.validate_sequence()
        
        # Verify validation passed
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['issues']), 0)
        self.assertEqual(len(result['sequence_details']), 3)
    
    def test_dv_002_sequence_gap(self):
        """
        Test DV-002: Sequence with gap (1, 3, 4) - missing 2
        
        Expected: is_valid = False, issue reported
        """
        # Create Job Cards with gap
        self._create_job_card(self.test_wo, "Op 1", 1)
        # Skip sequence 2
        self._create_job_card(self.test_wo, "Op 3", 3)
        self._create_job_card(self.test_wo, "Op 4", 4)
        
        engine = DependencyEngine(work_order=self.test_wo)
        result = engine.validate_sequence()
        
        # Verify validation failed
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['issues']), 0)
        
        # Verify issue details
        issue = result['issues'][0]
        self.assertIn("Sequence gap", issue['issue'])
        self.assertIn("Expected sequence 2", issue['issue'])
    
    def test_dv_002_no_job_cards(self):
        """
        Test DV-002: No Job Cards for Work Order
        
        Expected: is_valid = True, message indicates no Job Cards
        """
        # Create new Work Order without Job Cards
        new_wo = self._create_test_work_order()
        
        engine = DependencyEngine(work_order=new_wo)
        result = engine.validate_sequence()
        
        # Verify validation passed (no Job Cards is valid)
        self.assertTrue(result['is_valid'])
        self.assertIn("No Job Cards found", result['message'])
    
    def test_dv_002_api_validation(self):
        """
        Test DV-002 API endpoint
        
        Expected: API returns valid response structure
        """
        self._create_job_card(self.test_wo, "Op 1", 1)
        
        result = validate_sequence(self.test_wo)
        
        # Verify API response structure
        self.assertIn('is_valid', result)
        self.assertIn('message', result)
        self.assertIn('sequence_details', result)


class TestDependencyEngineIntegration(unittest.TestCase):
    """
    Integration Tests for Dependency Engine
    """
    
    def test_get_dependency_status(self):
        """
        Test get_dependency_status API
        
        Expected: Returns complete dependency information
        """
        # Create test Work Order and Job Card
        wo_name = self._create_minimal_work_order()
        
        if wo_name:
            jc_name = self._create_job_card(wo_name, "Test Op", 1)
            
            status = get_dependency_status(jc_name)
            
            # Verify response structure
            self.assertIn('job_card', status)
            self.assertIn('sequence_id', status)
            self.assertIn('has_dependencies', status)
            self.assertIn('can_start', status)
    
    def test_can_job_card_start_api(self):
        """
        Test can_job_card_start API
        
        Expected: Returns can_start with reason
        """
        wo_name = self._create_minimal_work_order()
        
        if wo_name:
            jc_name = self._create_job_card(wo_name, "Test Op", 1)
            
            result = can_job_card_start(jc_name)
            
            # Verify response structure
            self.assertIn('can_start', result)
            self.assertIn('reason', result)
    
    def _create_minimal_work_order(self):
        """Create minimal Work Order for testing"""
        try:
            wo = frappe.get_doc({
                "doctype": "Work Order",
                "production_item": "Test DV Item",
                "qty": 1,
                "planned_start_date": datetime.now()
            })
            wo.insert(ignore_permissions=True)
            return wo.name
        except Exception:
            return None
    
    def _create_job_card(self, work_order, operation, sequence_id):
        """Create test Job Card"""
        try:
            jc = frappe.get_doc({
                "doctype": "Job Card",
                "work_order": work_order,
                "operation": operation,
                "sequence_id": sequence_id,
                "for_quantity": 1
            })
            jc.insert(ignore_permissions=True)
            return jc.name
        except Exception:
            return None


def run_tests():
    """Run all dependency engine tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test suites
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyEngineDV001))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyEngineDV002))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyEngineIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    run_tests()
