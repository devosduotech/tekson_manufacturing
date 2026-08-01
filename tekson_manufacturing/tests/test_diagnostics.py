import frappe
import unittest
from frappe.exceptions import ValidationError
from tekson_manufacturing.diagnostics.messages import (
    DiagnosticMessages,
    DiagnosticCategory,
    SeverityLevel,
    get_diagnostic_message,
    format_diagnostics_for_ui,
    log_diagnostic_message
)


class TestDiagnosticMessages(unittest.TestCase):
    """
    Unit tests for Diagnostic Messages Engine
    Sprint 4: Diagnostics Framework
    
    Business Rules:
    - DM-001: Clear Operator Messages
    - DM-002: Diagnostic Categories
    - DM-003: Severity Levels
    - DM-004: UI-Friendly Formatting
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = DiagnosticMessages()
        self.sample_shortage = {
            'item_code': 'COPPER-TUBE-001',
            'item_name': 'Copper Tube',
            'required_qty': 100,
            'available_qty': 60,
            'shortage_qty': 40,
            'material_type': 'Raw Material',
            'reason': 'Stock not transferred from Stores',
            'action': 'Request Stores to transfer 40 kg to WIP-W',
            'warehouse': 'WIP-W'
        }
        
        self.sample_dependency = {
            'operation': 'Welding',
            'status': 'Work In Progress',
            'job_card': 'JC-2026-001',
            'department': 'Welding'
        }
        
        self.sample_config_error = {
            'setting_name': 'Default Warehouse',
            'expected_value': 'WIP-W',
            'actual_value': None,
            'impact': 'Cannot determine department warehouse'
        }
        
        self.sample_permission_error = {
            'user': 'test@example.com',
            'role': 'Department Manager',
            'action': 'approve transfer',
            'doctype': 'Stock Entry'
        }
    
    # ====================================================================
    # DM-001: Clear Operator Messages
    # ====================================================================
    
    def test_dm_001_material_shortage_message_format(self):
        """
        DM-001: Material shortage message has required format
        
        Required Format:
        - Title with item name
        - Details: Item, Required, Available, Shortage
        - Reason: Specific cause
        - Action: Actionable step
        """
        result = self.engine.build_material_shortage_message(self.sample_shortage)
        
        # Assert title format
        self.assertIn("Material Not Available", result['title'])
        self.assertIn("Copper Tube", result['title'])
        
        # Assert message contains required fields
        message = result['message']
        self.assertIn("Item:", message)
        self.assertIn("COPPER-TUBE-001", message)
        self.assertIn("Required:", message)
        self.assertIn("100", message)
        self.assertIn("Available:", message)
        self.assertIn("60", message)
        self.assertIn("Shortage:", message)
        self.assertIn("40", message)
        
        # Assert reason and action
        self.assertIn("Reason:", message)
        self.assertIn("Stock not transferred from Stores", message)
        self.assertIn("Action:", message)
        self.assertIn("Request Stores to transfer", message)
        
        # Assert it's an error
        self.assertEqual(result['type'], 'error')
        self.assertFalse(result['can_proceed'])
    
    def test_dm_001_previous_operation_message_format(self):
        """
        DM-001: Previous operation message has required format
        """
        result = self.engine.build_previous_operation_message(self.sample_dependency)
        
        # Assert title
        self.assertEqual(result['title'], "Previous Operation Not Complete")
        
        # Assert message contains required fields
        message = result['message']
        self.assertIn("Operation:", message)
        self.assertIn("Welding", message)
        self.assertIn("Status:", message)
        self.assertIn("Work In Progress", message)
        self.assertIn("Job Card:", message)
        self.assertIn("JC-2026-001", message)
        
        # Assert actionable note
        self.assertIn("Wait for previous operation to complete", message)
        
        # Assert it's a warning
        self.assertEqual(result['type'], 'warning')
        self.assertFalse(result['can_proceed'])
    
    def test_dm_001_work_order_not_started_message_format(self):
        """
        DM-001: Work Order not started message has required format
        """
        # Create mock work order
        class MockWorkOrder:
            name = "WO-2026-001"
            production_item = "Test Item"
            qty = 100
            status = "Not Started"
        
        result = self.engine.build_work_order_not_started_message(MockWorkOrder())
        
        # Assert title
        self.assertEqual(result['title'], "Work Order Not Started")
        
        # Assert message contains required fields
        message = result['message']
        self.assertIn("Work Order:", message)
        self.assertIn("WO-2026-001", message)
        self.assertIn("Item:", message)
        self.assertIn("Test Item", message)
        self.assertIn("Quantity:", message)
        self.assertIn("100", message)
        
        # Assert actionable step
        self.assertIn("Start the Work Order", message)
    
    def test_dm_001_success_message_format(self):
        """
        DM-001: Success message has clear format
        """
        result = self.engine.build_success_message("All validations passed")
        
        # Assert success format
        self.assertEqual(result['type'], 'success')
        self.assertEqual(result['title'], "Ready to Start")
        self.assertIn("All validations passed", result['message'])
        self.assertTrue(result['can_proceed'])
    
    # ====================================================================
    # DM-002: Diagnostic Categories
    # ====================================================================
    
    def test_dm_002_material_shortage_category(self):
        """
        DM-002: Material shortage has correct category
        """
        result = self.engine.build_material_shortage_message(self.sample_shortage)
        self.assertEqual(
            result['category'],
            DiagnosticCategory.MATERIAL_SHORTAGE.value
        )
    
    def test_dm_002_dependency_blocking_category(self):
        """
        DM-002: Dependency blocking has correct category
        """
        result = self.engine.build_previous_operation_message(self.sample_dependency)
        self.assertEqual(
            result['category'],
            DiagnosticCategory.DEPENDENCY_BLOCKING.value
        )
    
    def test_dm_002_wo_not_started_category(self):
        """
        DM-002: Work Order not started has correct category
        """
        class MockWorkOrder:
            name = "WO-2026-001"
            production_item = "Test Item"
            qty = 100
            status = "Not Started"
        
        result = self.engine.build_work_order_not_started_message(MockWorkOrder())
        self.assertEqual(
            result['category'],
            DiagnosticCategory.WO_NOT_STARTED.value
        )
    
    def test_dm_002_configuration_error_category(self):
        """
        DM-002: Configuration error has correct category
        """
        result = self.engine.build_configuration_error_message(self.sample_config_error)
        self.assertEqual(
            result['category'],
            DiagnosticCategory.CONFIGURATION_ERROR.value
        )
    
    def test_dm_002_permission_error_category(self):
        """
        DM-002: Permission error has correct category
        """
        result = self.engine.build_permission_error_message(self.sample_permission_error)
        self.assertEqual(
            result['category'],
            DiagnosticCategory.PERMISSION_ERROR.value
        )
    
    def test_dm_002_validation_passed_category(self):
        """
        DM-002: Success has validation_passed category
        """
        result = self.engine.build_success_message()
        self.assertEqual(
            result['category'],
            DiagnosticCategory.VALIDATION_PASSED.value
        )
    
    # ====================================================================
    # DM-003: Severity Levels
    # ====================================================================
    
    def test_dm_003_material_shortage_severity(self):
        """
        DM-003: Material shortage has HIGH severity
        """
        result = self.engine.build_material_shortage_message(self.sample_shortage)
        self.assertEqual(
            result['severity'],
            SeverityLevel.HIGH.value
        )
    
    def test_dm_003_dependency_blocking_severity(self):
        """
        DM-003: Dependency blocking has MEDIUM severity
        """
        result = self.engine.build_previous_operation_message(self.sample_dependency)
        self.assertEqual(
            result['severity'],
            SeverityLevel.MEDIUM.value
        )
    
    def test_dm_003_configuration_error_severity(self):
        """
        DM-003: Configuration error has CRITICAL severity
        """
        result = self.engine.build_configuration_error_message(self.sample_config_error)
        self.assertEqual(
            result['severity'],
            SeverityLevel.CRITICAL.value
        )
    
    def test_dm_003_permission_error_severity(self):
        """
        DM-003: Permission error has HIGH severity
        """
        result = self.engine.build_permission_error_message(self.sample_permission_error)
        self.assertEqual(
            result['severity'],
            SeverityLevel.HIGH.value
        )
    
    def test_dm_003_success_severity(self):
        """
        DM-003: Success has NONE severity
        """
        result = self.engine.build_success_message()
        self.assertEqual(
            result['severity'],
            SeverityLevel.NONE.value
        )
    
    def test_dm_003_warning_severity(self):
        """
        DM-003: Warning has MEDIUM severity
        """
        warning_data = {
            'title': 'Test Warning',
            'message': 'This is a warning',
            'impact': 'May cause issues'
        }
        result = self.engine.build_warning_message(warning_data)
        self.assertEqual(
            result['severity'],
            SeverityLevel.MEDIUM.value
        )
    
    # ====================================================================
    # DM-004: UI-Friendly Formatting
    # ====================================================================
    
    def test_dm_004_format_for_ui_with_errors(self):
        """
        DM-004: UI formatting with errors
        """
        error_diag = self.engine.build_material_shortage_message(self.sample_shortage)
        warning_diag = self.engine.build_previous_operation_message(self.sample_dependency)
        
        diagnostics = [error_diag, warning_diag]
        result = self.engine.format_for_ui(diagnostics)
        
        # Assert structure
        self.assertTrue(result['has_errors'])
        self.assertTrue(result['has_warnings'])
        self.assertFalse(result['can_proceed'])
        self.assertEqual(result['total_issues'], 2)
        self.assertEqual(result['error_count'], 1)
        self.assertEqual(result['warning_count'], 1)
        
        # Assert messages are formatted
        self.assertEqual(len(result['messages']), 2)
        for msg in result['messages']:
            self.assertIn('type', msg)
            self.assertIn('category', msg)
            self.assertIn('title', msg)
            self.assertIn('message', msg)
            self.assertIn('color', msg)
    
    def test_dm_004_format_for_ui_empty_list(self):
        """
        DM-004: UI formatting with empty list
        """
        result = self.engine.format_for_ui([])
        
        self.assertFalse(result['has_errors'])
        self.assertFalse(result['has_warnings'])
        self.assertTrue(result['can_proceed'])
        self.assertEqual(result['total_issues'], 0)
    
    def test_dm_004_color_codes(self):
        """
        DM-004: Color codes are assigned correctly
        """
        # Test error color
        error_diag = self.engine.build_material_shortage_message(self.sample_shortage)
        self.assertEqual(error_diag['color'], '#DC3545')  # Red
        
        # Test warning color
        warning_diag = self.engine.build_previous_operation_message(self.sample_dependency)
        self.assertEqual(warning_diag['color'], '#FFC107')  # Orange
        
        # Test success color
        success_diag = self.engine.build_success_message()
        self.assertEqual(success_diag['color'], '#28A745')  # Green
        
        # Test critical color
        config_diag = self.engine.build_configuration_error_message(self.sample_config_error)
        self.assertEqual(config_diag['color'], '#721C24')  # Dark Red
    
    def test_dm_004_context_message(self):
        """
        DM-004: Context-aware message building
        """
        diagnostic = self.engine.build_material_shortage_message(self.sample_shortage)
        context = {
            'user_role': 'Operator',
            'department': 'Welding',
            'show_technical': True
        }
        
        result = self.engine.build_context_message(diagnostic, context)
        
        # Assert context is added
        self.assertIn('context', result)
        self.assertEqual(result['context']['user_role'], 'Operator')
        self.assertEqual(result['context']['department'], 'Welding')
        
        # Assert message includes context
        self.assertIn('Role: Operator', result['message'])
        self.assertIn('Department: Welding', result['message'])
    
    def test_dm_004_aggregated_diagnostic(self):
        """
        DM-004: Aggregated diagnostic summary
        """
        error_diag = self.engine.build_material_shortage_message(self.sample_shortage)
        warning_diag = self.engine.build_previous_operation_message(self.sample_dependency)
        
        diagnostics = [error_diag, warning_diag]
        result = self.engine.build_aggregated_diagnostic(diagnostics)
        
        # Assert summary format
        self.assertIn("Summary:", result['title'])
        self.assertIn("1 Error", result['title'])
        self.assertIn("1 Warning", result['title'])
        
        # Assert counts
        self.assertEqual(result['error_count'], 1)
        self.assertEqual(result['warning_count'], 1)
        self.assertEqual(result['total_count'], 2)
        self.assertFalse(result['can_proceed'])
    
    # ====================================================================
    # Integration Tests
    # ====================================================================
    
    def test_integration_whitelisted_methods(self):
        """
        Test whitelisted methods are accessible
        """
        # Test get_diagnostic_message
        diagnostic_data = {
            'category': 'material_shortage',
            'item_code': 'ITEM-001',
            'item_name': 'Test Item',
            'required_qty': 100,
            'available_qty': 50,
            'shortage_qty': 50,
            'reason': 'Test reason',
            'action': 'Test action'
        }
        
        result = get_diagnostic_message(diagnostic_data, "WO-2026-001")
        self.assertEqual(result['type'], 'error')
        self.assertEqual(result['category'], 'material_shortage')
        
        # Test format_diagnostics_for_ui
        formatted = format_diagnostics_for_ui([result])
        self.assertTrue(formatted['has_errors'])
        self.assertFalse(formatted['can_proceed'])
        
        # Test log_diagnostic_message
        log_result = log_diagnostic_message(result, "Job Card", "JC-2026-001")
        self.assertTrue(log_result)


class TestDiagnosticCategories(unittest.TestCase):
    """Test diagnostic category enum values"""
    
    def test_all_categories_defined(self):
        """Test all DM-002 categories are defined"""
        categories = [c.value for c in DiagnosticCategory]
        
        expected_categories = [
            'material_shortage',
            'dependency_blocking',
            'wo_not_started',
            'validation_passed',
            'warning',
            'error',
            'configuration_error',
            'permission_error'
        ]
        
        for category in expected_categories:
            self.assertIn(category, categories)


class TestSeverityLevels(unittest.TestCase):
    """Test severity level enum values"""
    
    def test_all_severity_levels_defined(self):
        """Test all DM-003 severity levels are defined"""
        levels = [l.value for l in SeverityLevel]
        
        expected_levels = [
            'none',
            'low',
            'medium',
            'high',
            'critical'
        ]
        
        for level in expected_levels:
            self.assertIn(level, levels)


if __name__ == '__main__':
    unittest.main()
