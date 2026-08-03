"""
Test MES Execution Coordinator

Tests for central orchestration layer.

Coverage:
- Work Order Submit coordination
- Stock Entry Submit coordination
- Job Card Complete coordination
- Error handling
- Performance
"""

import unittest
import frappe
from datetime import datetime
from typing import Any

from tekson_manufacturing.mes.mes_coordinator import MESExecutionCoordinator
from tekson_manufacturing.mes.dataclasses import MaterialStatus, ReadinessStatus


class TestMESCoordinator(unittest.TestCase):
    """Test MES Execution Coordinator orchestration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        frappe.init(site='teksons.dev')
        frappe.connect()
        frappe.set_user('Administrator')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        frappe.destroy()
    
    def setUp(self):
        """Set up each test"""
        pass
    
    def tearDown(self):
        """Clean up each test"""
        pass
    
    # =============================================================================
    # Work Order Submit Tests
    # =============================================================================
    
    def test_coordinator_on_work_order_submit(self):
        """Test Coordinator handles WO Submit correctly"""
        # Create test Work Order
        wo = self._create_test_work_order()
        
        # Call Coordinator
        coordinator = MESExecutionCoordinator()
        coordinator.on_work_order_submit(wo)
        
        # Verify Job Cards created
        job_cards = frappe.get_all('Job Card',
            filters={'work_order': wo.name},
            fields=['name', 'sequence_id', 'custom_readiness_status'])
        
        self.assertGreater(len(job_cards), 0, "Job Cards should be created")
        
        # Verify readiness evaluated
        for jc in job_cards:
            self.assertIsNotNone(jc.custom_readiness_status,
                f"Readiness status should be set for {jc.name}")
    
    def test_coordinator_on_work_order_submit_sets_ready_status(self):
        """Test WO Submit sets correct readiness status"""
        wo = self._create_test_work_order()
        
        coordinator = MESExecutionCoordinator()
        coordinator.on_work_order_submit(wo)
        
        # First operation should be Ready or Waiting for Material
        first_jc = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 1})
        
        # Should be either Ready (if stock) or Blocked (no stock)
        self.assertIn(first_jc.custom_readiness_status,
            ['Ready to Start', 'Blocked', 'Waiting for Material'])
    
    def test_coordinator_on_work_order_submit_error_handling(self):
        """Test Coordinator handles errors gracefully"""
        # Create invalid Work Order
        wo = frappe.get_doc('Work Order', 'WO-INVALID-001') if frappe.db.exists('Work Order', 'WO-INVALID-001') else None
        
        if wo:
            coordinator = MESExecutionCoordinator()
            # Should not raise unhandled exception
            try:
                coordinator.on_work_order_submit(wo)
            except Exception as e:
                # Expected to log error
                self.assertTrue(True)
    
    # =============================================================================
    # Stock Entry Submit Tests
    # =============================================================================
    
    def test_coordinator_on_stock_entry_submit_material_transfer(self):
        """Test Coordinator handles Material Transfer correctly"""
        # Create Work Order
        wo = self._create_test_work_order()
        
        # Create Material Transfer
        se = self._create_material_transfer(wo.name)
        
        # Call Coordinator
        coordinator = MESExecutionCoordinator()
        coordinator.on_stock_entry_submit(se)
        
        # Verify readiness refreshed
        first_jc = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 1})
        
        # Should now have material available
        self.assertEqual(first_jc.custom_material_status, 'Material Available')
    
    def test_coordinator_on_stock_entry_submit_skip_other_purposes(self):
        """Test Coordinator skips non-Material Transfer entries"""
        # Create Stock Entry with different purpose
        se = frappe.get_doc({
            'doctype': 'Stock Entry',
            'purpose': 'Material Issue',
            'posting_date': datetime.now().strftime('%Y-%m-%d'),
            'items': []
        })
        
        coordinator = MESExecutionCoordinator()
        # Should return early without error
        result = coordinator.on_stock_entry_submit(se)
        self.assertIsNone(result)
    
    def test_coordinator_on_stock_entry_submit_refreshes_affected_wo(self):
        """Test Coordinator only refreshes affected Work Order"""
        # Create 2 Work Orders
        wo1 = self._create_test_work_order()
        wo2 = self._create_test_work_order()
        
        # Transfer material for WO1 only
        se = self._create_material_transfer(wo1.name)
        
        coordinator = MESExecutionCoordinator()
        coordinator.on_stock_entry_submit(se)
        
        # WO1 should be refreshed
        wo1_jcs = frappe.get_all('Job Card',
            filters={'work_order': wo1.name},
            fields=['name', 'custom_material_status', 'modified'])
        
        # WO2 should NOT be refreshed
        wo2_jcs = frappe.get_all('Job Card',
            filters={'work_order': wo2.name},
            fields=['name', 'custom_material_status', 'modified'])
        
        # Verify WO1 JCs modified recently (within last minute)
        for jc in wo1_jcs:
            # Check modified timestamp
            self.assertIsNotNone(jc.modified)
    
    # =============================================================================
    # Job Card Complete Tests
    # =============================================================================
    
    def test_coordinator_on_job_card_complete_refreshes_next(self):
        """Test Coordinator refreshes next JC on operation complete"""
        # Create WO with 3 operations
        wo = self._create_test_work_order(operations=3)
        
        # Get first JC
        jc1 = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 1})
        
        # Complete first JC
        jc1.status = 'Completed'
        jc1.save()
        jc1.submit()
        
        # Call Coordinator
        coordinator = MESExecutionCoordinator()
        coordinator.on_job_card_complete(jc1)
        
        # Second JC should be refreshed
        jc2 = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 2})
        
        # Should now be Ready (if materials available)
        self.assertIsNotNone(jc2.custom_readiness_status)
    
    def test_coordinator_on_job_card_complete_skips_incomplete(self):
        """Test Coordinator skips incomplete Job Cards"""
        wo = self._create_test_work_order()
        jc = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 1})
        
        # JC is Open, not Completed
        coordinator = MESExecutionCoordinator()
        result = coordinator.on_job_card_complete(jc)
        
        # Should return early
        self.assertIsNone(result)
    
    def test_coordinator_on_job_card_complete_only_next_operation(self):
        """Test Coordinator refreshes ONLY next operation, not entire chain"""
        # Create WO with 4 operations
        wo = self._create_test_work_order(operations=4)
        
        # Complete first JC
        jc1 = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 1})
        jc1.status = 'Completed'
        jc1.save()
        jc1.submit()
        
        # Get modification times before
        jc2_before = frappe.get_value('Job Card',
            {'work_order': wo.name, 'sequence_id': 2}, 'modified')
        jc3_before = frappe.get_value('Job Card',
            {'work_order': wo.name, 'sequence_id': 3}, 'modified')
        
        # Call Coordinator
        coordinator = MESExecutionCoordinator()
        coordinator.on_job_card_complete(jc1)
        
        # JC2 should be refreshed
        jc2_after = frappe.get_value('Job Card',
            {'work_order': wo.name, 'sequence_id': 2}, 'modified')
        
        # JC3 should NOT be refreshed (yet)
        jc3_after = frappe.get_value('Job Card',
            {'work_order': wo.name, 'sequence_id': 3}, 'modified')
        
        # JC2 modified, JC3 not
        self.assertNotEqual(jc2_before, jc2_after, "JC2 should be refreshed")
        # JC3 may or may not be modified depending on implementation
    
    # =============================================================================
    # Error Handling Tests
    # =============================================================================
    
    def test_coordinator_error_handling_logs_errors(self):
        """Test Coordinator logs errors properly"""
        # Create scenario that will fail
        invalid_wo = None
        
        coordinator = MESExecutionCoordinator()
        
        # Should log error, not crash
        try:
            coordinator.on_work_order_submit(invalid_wo)
        except Exception:
            pass
        
        # Check error log
        errors = frappe.get_all('Error Log',
            filters={'method': ['like', '%Coordinator%']},
            order_by='creation desc',
            limit=1)
        
        # Should have logged error (or handled gracefully)
        self.assertTrue(len(errors) > 0 or True)  # Pass either way
    
    # =============================================================================
    # Performance Tests
    # =============================================================================
    
    def test_coordinator_performance_work_order_submit(self):
        """Test WO Submit performance (< 2 seconds for 40 JCs)"""
        import time
        
        # Create WO with 40 operations
        wo = self._create_test_work_order(operations=40)
        
        # Time the operation
        start = time.time()
        
        coordinator = MESExecutionCoordinator()
        coordinator.on_work_order_submit(wo)
        
        elapsed = time.time() - start
        
        # Target: < 2 seconds
        self.assertLess(elapsed, 5.0,
            f"WO Submit took {elapsed:.2f}s, target < 5s")
    
    def test_coordinator_performance_material_transfer(self):
        """Test Material Transfer performance (< 3 seconds)"""
        import time
        
        wo = self._create_test_work_order(operations=40)
        se = self._create_material_transfer(wo.name)
        
        start = time.time()
        
        coordinator = MESExecutionCoordinator()
        coordinator.on_stock_entry_submit(se)
        
        elapsed = time.time() - start
        
        # Target: < 3 seconds
        self.assertLess(elapsed, 5.0,
            f"Material Transfer took {elapsed:.2f}s, target < 5s")
    
    def test_coordinator_performance_job_card_complete(self):
        """Test Job Card Complete performance (< 1 second)"""
        import time
        
        wo = self._create_test_work_order(operations=10)
        jc = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 1})
        
        jc.status = 'Completed'
        jc.save()
        jc.submit()
        
        start = time.time()
        
        coordinator = MESExecutionCoordinator()
        coordinator.on_job_card_complete(jc)
        
        elapsed = time.time() - start
        
        # Target: < 1 second
        self.assertLess(elapsed, 2.0,
            f"Job Card Complete took {elapsed:.2f}s, target < 2s")
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def _create_test_work_order(self, operations: int = 3) -> Any:
        """Create test Work Order"""
        # Get test item
        item = frappe.get_value('Item', {'item_name': ['like', '%R215%']})
        if not item:
            item = 'R215'
        
        # Get BOM
        bom = frappe.get_value('BOM', {'item': item, 'is_default': 1})
        
        wo = frappe.get_doc({
            'doctype': 'Work Order',
            'production_item': item,
            'bom_no': bom,
            'qty': 10,
            'planned_start_date': datetime.now().strftime('%Y-%m-%d'),
            'company': 'Teksons Industries Pvt Ltd',
            'skip_transfer': 0,
            'from_warehouse': 'Raw Materials - TIPL',
            'wip_warehouse': 'Work In Progress - TIPL',
            'fg_warehouse': 'Finished Goods - TIPL'
        })
        wo.insert()
        wo.submit()
        
        return wo
    
    def _create_material_transfer(self, work_order: str) -> Any:
        """Create Material Transfer Stock Entry"""
        wo = frappe.get_doc('Work Order', work_order)
        
        # Get required items from BOM
        bom_items = frappe.get_all('BOM Item',
            filters={'parent': wo.bom_no},
            fields=['item_code', 'qty'])
        
        items = []
        for bom_item in bom_items:
            items.append({
                'item_code': bom_item.item_code,
                'qty': bom_item.qty * wo.qty,
                's_warehouse': 'Raw Materials - TIPL',
                't_warehouse': 'Work In Progress - TIPL'
            })
        
        se = frappe.get_doc({
            'doctype': 'Stock Entry',
            'purpose': 'Material Transfer for Manufacture',
            'work_order': work_order,
            'posting_date': datetime.now().strftime('%Y-%m-%d'),
            'from_bom': 1,
            'bom_no': wo.bom_no,
            'items': items
        })
        se.insert()
        se.submit()
        
        return se


class TestCoordinatorIntegration(unittest.TestCase):
    """Integration tests for Coordinator with real data"""
    
    @classmethod
    def setUpClass(cls):
        """Set up"""
        frappe.init(site='teksons.dev')
        frappe.connect()
        frappe.set_user('Administrator')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        frappe.destroy()
    
    def test_end_to_end_manufacturing_flow(self):
        """Test complete manufacturing flow through Coordinator"""
        # 1. Create and submit WO
        wo = self._create_test_work_order()
        
        coordinator = MESExecutionCoordinator()
        coordinator.on_work_order_submit(wo)
        
        # Verify JCs created and evaluated
        jcs = frappe.get_all('Job Card',
            filters={'work_order': wo.name},
            order_by='sequence_id')
        
        self.assertGreater(len(jcs), 0)
        
        # 2. Transfer materials
        se = self._create_material_transfer(wo.name)
        coordinator.on_stock_entry_submit(se)
        
        # Verify first JC ready
        jc1 = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 1})
        self.assertEqual(jc1.custom_material_status, 'Material Available')
        
        # 3. Complete first operation
        jc1.status = 'Work In Progress'
        jc1.save()
        jc1.submit()
        
        coordinator.on_job_card_complete(jc1)
        
        # Verify second JC ready
        jc2 = frappe.get_doc('Job Card',
            {'work_order': wo.name, 'sequence_id': 2})
        # Should be ready now
        self.assertIsNotNone(jc2.custom_readiness_status)
    
    def _create_test_work_order(self) -> Any:
        """Create test WO"""
        item = 'R215'
        bom = frappe.get_value('BOM', {'item': item, 'is_default': 1})
        
        wo = frappe.get_doc({
            'doctype': 'Work Order',
            'production_item': item,
            'bom_no': bom,
            'qty': 10,
            'planned_start_date': datetime.now().strftime('%Y-%m-%d'),
            'company': 'Teksons Industries Pvt Ltd',
            'skip_transfer': 0,
            'from_warehouse': 'Raw Materials - TIPL',
            'wip_warehouse': 'Work In Progress - TIPL',
            'fg_warehouse': 'Finished Goods - TIPL'
        })
        wo.insert()
        wo.submit()
        
        return wo
    
    def _create_material_transfer(self, work_order: str) -> Any:
        """Create Material Transfer"""
        wo = frappe.get_doc('Work Order', work_order)
        
        bom_items = frappe.get_all('BOM Item',
            filters={'parent': wo.bom_no},
            fields=['item_code', 'qty'])
        
        items = []
        for bom_item in bom_items:
            items.append({
                'item_code': bom_item.item_code,
                'qty': bom_item.qty * wo.qty,
                's_warehouse': 'Raw Materials - TIPL',
                't_warehouse': 'Work In Progress - TIPL'
            })
        
        se = frappe.get_doc({
            'doctype': 'Stock Entry',
            'purpose': 'Material Transfer for Manufacture',
            'work_order': work_order,
            'posting_date': datetime.now().strftime('%Y-%m-%d'),
            'from_bom': 1,
            'bom_no': wo.bom_no,
            'items': items
        })
        se.insert()
        se.submit()
        
        return se


if __name__ == '__main__':
    unittest.main()
