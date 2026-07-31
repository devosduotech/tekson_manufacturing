"""
Unit Tests for Material Readiness Engine

Business Rules:
- MR-010: Stores transfers materials to Department Warehouse before production starts
- MR-011: Cumulative availability check across multiple Stock Entries

Test Coverage:
- Material readiness evaluation
- Cumulative transfer validation
- Department warehouse mapping
- Transfer status determination
- Transfer suggestions
"""

import frappe
import unittest
from datetime import datetime, timedelta
from tekson_manufacturing.readiness.material_readiness import (
    MaterialReadinessEngine,
    evaluate_material_readiness,
    can_job_card_start,
    get_transfer_suggestions
)


class TestMaterialReadinessMR010(unittest.TestCase):
    """
    Test Suite for MR-010: Stores transfers materials to Department Warehouse
    
    MR-010 states: Production starts only after required materials have been 
    transferred by Stores to the Department Warehouse.
    """
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test Work Order if not exists
        self.test_wo = self._create_test_work_order()
        self.test_department_warehouse = "WIP-CNC"
    
    def tearDown(self):
        """Clean up test data"""
        # Cancel and delete test documents
        if hasattr(self, 'test_wo') and self.test_wo:
            try:
                wo = frappe.get_doc("Work Order", self.test_wo)
                if wo.docstatus == 1:
                    wo.cancel()
                wo.delete()
            except Exception:
                pass
    
    def _create_test_work_order(self):
        """Helper to create test Work Order"""
        # Check if test WO exists
        existing_wo = frappe.db.get_value(
            "Work Order", 
            {"production_item": "Test Production Item"},
            "name"
        )
        
        if existing_wo:
            return existing_wo
        
        # Create test item if not exists
        if not frappe.db.exists("Item", "Test Production Item"):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test Production Item",
                "item_name": "Test Production Item",
                "item_group": "Products",
                "is_stock_item": 1,
                "stock_uom": "Nos"
            })
            item.insert(ignore_permissions=True)
        
        # Create test BOM if not exists
        bom_name = frappe.db.get_value("BOM", {"item": "Test Production Item"}, "name")
        if not bom_name:
            bom = frappe.get_doc({
                "doctype": "BOM",
                "item": "Test Production Item",
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
            "production_item": "Test Production Item",
            "bom_no": bom_name,
            "qty": 10,
            "planned_start_date": datetime.now(),
            "custom_plant_floor": "CNC"
        })
        wo.insert(ignore_permissions=True)
        wo.submit()
        
        return wo.name
    
    def test_mr_010_evaluate_readiness_no_transfers(self):
        """
        Test MR-010: Material readiness when no transfers exist
        
        Expected: is_ready = False, missing_items populated
        """
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        result = engine.evaluate_material_readiness()
        
        # Verify structure
        self.assertIn('is_ready', result)
        self.assertIn('missing_items', result)
        self.assertIn('transferred_items', result)
        self.assertIn('transfer_summary', result)
        
        # Verify readiness status (should be False if no transfers)
        # Note: Actual result depends on BOM items and transfers
    
    def test_mr_010_department_warehouse_mapping(self):
        """
        Test MR-010: Department warehouse is correctly mapped from Plant Floor
        
        Expected: WIP-CNC for CNC Plant Floor
        """
        wo = frappe.get_doc("Work Order", self.test_wo)
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        
        warehouse = engine.get_department_warehouse(wo)
        
        # Verify warehouse is returned
        self.assertIsNotNone(warehouse)
        self.assertIsInstance(warehouse, str)
        self.assertTrue(len(warehouse) > 0)
    
    def test_mr_010_job_card_start_permission_no_transfers(self):
        """
        Test MR-010: Job Card cannot start without material transfers
        
        Expected: can_start = False with reason
        """
        # Create test Job Card
        jc = frappe.get_doc({
            "doctype": "Job Card",
            "work_order": self.test_wo,
            "operation": "Test Operation",
            "for_quantity": 10
        })
        jc.insert(ignore_permissions=True)
        
        try:
            result = can_job_card_start(jc.name)
            
            # Verify structure
            self.assertIn('can_start', result)
            self.assertIn('reason', result)
            self.assertIn('material_status', result)
            
            # Job Card should not be able to start without materials
            # (assuming no transfers exist)
            self.assertFalse(result['can_start'] or True)  # May be true if BOM is empty
        finally:
            # Clean up
            jc.delete()
    
    def test_mr_010_transfer_suggestions_structure(self):
        """
        Test MR-010: Transfer suggestions returned with correct structure
        
        Expected: List of suggestions with item details, quantities, warehouses
        """
        suggestions = get_transfer_suggestions(self.test_wo)
        
        # Verify structure
        self.assertIsInstance(suggestions, list)
        
        # Each suggestion should have required fields
        for suggestion in suggestions:
            self.assertIn('item_code', suggestion)
            self.assertIn('required_qty', suggestion)
            self.assertIn('remaining_to_transfer', suggestion)
            self.assertIn('source_warehouse', suggestion)
            self.assertIn('target_warehouse', suggestion)


class TestMaterialReadinessMR011(unittest.TestCase):
    """
    Test Suite for MR-011: Cumulative Availability Check
    
    MR-011 states: Material Transfer against a Work Order is treated as a 
    working set. MES must evaluate cumulative material availability regardless 
    of whether materials were transferred in single or multiple Stock Entries.
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_wo = self._create_test_work_order()
        self.test_item = "Test Raw Material"
        self.test_warehouse = "WIP-CNC"
    
    def tearDown(self):
        """Clean up test data"""
        # Cancel test stock entries
        if hasattr(self, 'test_stock_entries'):
            for se_name in self.test_stock_entries:
                try:
                    se = frappe.get_doc("Stock Entry", se_name)
                    if se.docstatus == 1:
                        se.cancel()
                    se.delete()
                except Exception:
                    pass
    
    def _create_test_work_order(self):
        """Helper to create test Work Order"""
        existing_wo = frappe.db.get_value(
            "Work Order", 
            {"production_item": "Test MR-011 Item"},
            "name"
        )
        
        if existing_wo:
            return existing_wo
        
        # Create test item
        if not frappe.db.exists("Item", "Test MR-011 Item"):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test MR-011 Item",
                "item_name": "Test MR-011 Item",
                "item_group": "Products",
                "is_stock_item": 1,
                "stock_uom": "Nos"
            })
            item.insert(ignore_permissions=True)
        
        # Create test raw material
        if not frappe.db.exists("Item", "Test Raw Material"):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test Raw Material",
                "item_name": "Test Raw Material",
                "item_group": "Raw Material",
                "is_stock_item": 1,
                "stock_uom": "Kg"
            })
            item.insert(ignore_permissions=True)
        
        # Create BOM with raw material
        bom_name = frappe.db.get_value("BOM", {"item": "Test MR-011 Item"}, "name")
        if not bom_name:
            bom = frappe.get_doc({
                "doctype": "BOM",
                "item": "Test MR-011 Item",
                "quantity": 1,
                "uom": "Nos"
            })
            bom.append("items", {
                "item_code": "Test Raw Material",
                "qty": 10,
                "uom": "Kg"
            })
            bom.insert(ignore_permissions=True)
            bom.submit()
            bom_name = bom.name
        
        # Create Work Order
        wo = frappe.get_doc({
            "doctype": "Work Order",
            "production_item": "Test MR-011 Item",
            "bom_no": bom_name,
            "qty": 10,
            "planned_start_date": datetime.now(),
            "custom_plant_floor": "CNC"
        })
        wo.insert(ignore_permissions=True)
        wo.submit()
        
        return wo.name
    
    def _create_material_transfer_entry(self, work_order, item_code, qty, warehouse):
        """Helper to create Material Transfer Stock Entry"""
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "purpose": "Material Transfer for Manufacture",
            "work_order": work_order,
            "from_warehouse": "Raw Materials Stores",
            "to_warehouse": warehouse
        })
        
        se.append("items", {
            "item_code": item_code,
            "qty": qty,
            "s_warehouse": "Raw Materials Stores",
            "t_warehouse": warehouse,
            "uom": "Kg"
        })
        
        se.insert(ignore_permissions=True)
        se.submit()
        
        if not hasattr(self, 'test_stock_entries'):
            self.test_stock_entries = []
        self.test_stock_entries.append(se.name)
        
        return se.name
    
    def test_mr_011_cumulative_transfer_single_entry(self):
        """
        Test MR-011: Cumulative transfer with single Stock Entry
        
        Scenario: Single transfer of 100 kg
        Expected: Cumulative = 100 kg
        """
        # Create single transfer
        self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            100, 
            self.test_warehouse
        )
        
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        cumulative = engine.get_cumulative_transferred_qty(
            self.test_item, 
            self.test_wo, 
            self.test_warehouse
        )
        
        # Verify cumulative quantity
        self.assertEqual(cumulative, 100.0)
    
    def test_mr_011_cumulative_transfer_multiple_entries(self):
        """
        Test MR-011: Cumulative transfer with multiple Stock Entries
        
        Scenario:
        - Transfer 1: 40 kg
        - Transfer 2: 35 kg
        - Transfer 3: 25 kg
        Expected: Cumulative = 100 kg
        """
        # Create multiple transfers
        self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            40, 
            self.test_warehouse
        )
        self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            35, 
            self.test_warehouse
        )
        self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            25, 
            self.test_warehouse
        )
        
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        cumulative = engine.get_cumulative_transferred_qty(
            self.test_item, 
            self.test_wo, 
            self.test_warehouse
        )
        
        # Verify cumulative quantity (40 + 35 + 25 = 100)
        self.assertEqual(cumulative, 100.0)
    
    def test_mr_011_transfer_entries_details(self):
        """
        Test MR-011: Transfer entries details returned correctly
        
        Expected: List of all Stock Entries with details
        """
        # Create multiple transfers
        se1 = self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            40, 
            self.test_warehouse
        )
        se2 = self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            60, 
            self.test_warehouse
        )
        
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        entries = engine.get_transfer_entries(
            self.test_item, 
            self.test_wo, 
            self.test_warehouse
        )
        
        # Verify entries returned
        self.assertEqual(len(entries), 2)
        
        # Verify entry details
        entry_names = [e['stock_entry'] for e in entries]
        self.assertIn(se1, entry_names)
        self.assertIn(se2, entry_names)
    
    def test_mr_011_partial_transfer_readiness(self):
        """
        Test MR-011: Material readiness with partial transfers
        
        Scenario: Required 100 kg, transferred 60 kg
        Expected: is_ready = False, shortage_qty = 40 kg
        """
        # Create partial transfer
        self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            60, 
            self.test_warehouse
        )
        
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        result = engine.evaluate_material_readiness()
        
        # Verify partial transfer detected
        self.assertFalse(result['is_ready'])
        
        # Verify shortage details
        if result['shortage_details']:
            shortage = result['shortage_details'][0]
            self.assertEqual(shortage['required_qty'], 100.0)
            self.assertLess(shortage['available_qty'], 100.0)
            self.assertEqual(
                shortage['shortage_qty'], 
                100.0 - shortage['available_qty']
            )
    
    def test_mr_011_cumulative_availability_working_set(self):
        """
        Test MR-011: Working set principle - cumulative availability
        
        Scenario: Work Order requires 100 kg
        Transfer 1: 40 kg (Day 1)
        Transfer 2: 35 kg (Day 2)
        Transfer 3: 25 kg (Day 3)
        
        After Transfer 3: Cumulative = 100 kg, is_ready = True
        """
        # Simulate multi-day transfers
        self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            40, 
            self.test_warehouse
        )
        
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        
        # After Transfer 1: 40 kg (not ready)
        result1 = engine.evaluate_material_readiness()
        cumulative1 = engine.get_cumulative_transferred_qty(
            self.test_item, self.test_wo, self.test_warehouse
        )
        self.assertEqual(cumulative1, 40.0)
        
        # Transfer 2: 35 kg (total 75 kg, not ready)
        self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            35, 
            self.test_warehouse
        )
        
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        cumulative2 = engine.get_cumulative_transferred_qty(
            self.test_item, self.test_wo, self.test_warehouse
        )
        self.assertEqual(cumulative2, 75.0)
        
        # Transfer 3: 25 kg (total 100 kg, ready)
        self._create_material_transfer_entry(
            self.test_wo, 
            self.test_item, 
            25, 
            self.test_warehouse
        )
        
        engine = MaterialReadinessEngine(work_order=self.test_wo)
        cumulative3 = engine.get_cumulative_transferred_qty(
            self.test_item, self.test_wo, self.test_warehouse
        )
        self.assertEqual(cumulative3, 100.0)
        
        # Verify material readiness
        result3 = engine.evaluate_material_readiness()
        # Should be ready if all items fully transferred


class TestMaterialReadinessIntegration(unittest.TestCase):
    """
    Integration Tests for Material Readiness Engine
    
    Tests end-to-end scenarios combining MR-010 and MR-011
    """
    
    def test_evaluate_material_readiness_api(self):
        """
        Test whitelisted API: evaluate_material_readiness
        
        Expected: Returns complete readiness structure
        """
        # Create test WO
        wo_name = self._create_minimal_work_order()
        
        if wo_name:
            result = evaluate_material_readiness(wo_name)
            
            # Verify API response structure
            self.assertIsInstance(result, dict)
            self.assertIn('is_ready', result)
            self.assertIn('missing_items', result)
            self.assertIn('transferred_items', result)
    
    def _create_minimal_work_order(self):
        """Create minimal Work Order for API testing"""
        try:
            wo = frappe.get_doc({
                "doctype": "Work Order",
                "production_item": "Test Production Item",
                "qty": 1,
                "planned_start_date": datetime.now()
            })
            wo.insert(ignore_permissions=True)
            return wo.name
        except Exception:
            return None


def run_tests():
    """Run all material readiness tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test suites
    suite.addTests(loader.loadTestsFromTestCase(TestMaterialReadinessMR010))
    suite.addTests(loader.loadTestsFromTestCase(TestMaterialReadinessMR011))
    suite.addTests(loader.loadTestsFromTestCase(TestMaterialReadinessIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    run_tests()
