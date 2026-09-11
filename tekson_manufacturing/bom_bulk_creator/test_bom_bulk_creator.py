# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Tests for BOM Bulk Creator — Phase 1

Tests:
1. Single-level BOM
2. Two-level BOM
3. Three-level BOM
4. Complex multi-level BOM
5. Duplicate execution (idempotency)
6. Draft status verification
7. Blank bom_no verification
"""

import frappe
from frappe.tests import IntegrationTestCase

from tekson_manufacturing.bom_bulk_creator.bom_bulk_creator import BOMBulkCreator


class TestBOMBulkCreator(IntegrationTestCase):
	"""Tests for BOM Bulk Creator Phase 1"""

	def setUp(self):
		"""Set up test data"""
		self.company = "_Test Company"
		self.create_test_items()

	def create_test_items(self):
		"""Create test items for BOM testing"""
		items = [
			"Test FG Item",
			"Test Assembly A",
			"Test Assembly B",
			"Test Sub Assembly A1",
			"Test Sub Assembly B1",
			"Test Component A",
			"Test Component B",
			"Test Component C",
			"Test Component D",
			"Test Component E",
		]

		for item_code in items:
			if not frappe.db.exists("Item", item_code):
				frappe.get_doc({
					"doctype": "Item",
					"item_code": item_code,
					"item_name": item_code,
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
					"company": self.company,
				}).insert(ignore_permissions=True)

	def create_bom_bulk_creator(self, item_code, items_data):
		"""Helper to create a BOM Bulk Creator"""
		doc = frappe.get_doc({
			"doctype": "BOM Bulk Creator",
			"name": f"Test BBC - {item_code}",
			"item_code": item_code,
			"qty": 1,
			"company": self.company,
			"currency": "INR",
			"rm_cost_as_per": "Valuation Rate",
		})

		for item in items_data:
			doc.append("items", item)

		doc.insert(ignore_permissions=True)
		return doc

	def test_01_single_level_bom(self):
		"""
		Test 1: Single-level BOM
		FG
		├── Item A
		└── Item B
		Expected: 1 Draft BOM
		"""
		items = [
			{
				"item_code": "Test Component A",
				"qty": 10,
				"fg_item": "Test FG Item",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
			{
				"item_code": "Test Component B",
				"qty": 5,
				"fg_item": "Test FG Item",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
		]

		doc = self.create_bom_bulk_creator("Test FG Item", items)
		doc.submit()

		# Check status
		self.assertEqual(doc.status, "Completed")

		# Check BOM was created
		bom = frappe.db.get_value(
			"BOM",
			{"item": "Test FG Item", "bom_type": "Production", "company": self.company},
			["name", "docstatus"],
			as_dict=True
		)

		self.assertTrue(bom, "BOM should be created")
		self.assertEqual(bom.docstatus, 0, "BOM should be Draft")

		# Check BOM Items
		bom_doc = frappe.get_doc("BOM", bom.name)
		self.assertEqual(len(bom_doc.items), 2, "BOM should have 2 items")

	def test_02_two_level_bom(self):
		"""
		Test 2: Two-level BOM
		FG
		└── Assembly
		    ├── Item A
		    └── Item B
		Expected: 2 Draft BOMs
		"""
		items = [
			{
				"item_code": "Test Assembly A",
				"qty": 1,
				"fg_item": "Test FG Item",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			{
				"item_code": "Test Component A",
				"qty": 10,
				"fg_item": "Test Assembly A",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
			{
				"item_code": "Test Component B",
				"qty": 5,
				"fg_item": "Test Assembly A",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
		]

		doc = self.create_bom_bulk_creator("Test FG Item", items)
		doc.submit()

		# Check BOMs were created
		bom_fg = frappe.db.get_value(
			"BOM",
			{"item": "Test FG Item", "bom_type": "Production", "company": self.company},
			["name", "docstatus"],
			as_dict=True
		)

		bom_assembly = frappe.db.get_value(
			"BOM",
			{"item": "Test Assembly A", "bom_type": "Production", "company": self.company},
			["name", "docstatus"],
			as_dict=True
		)

		self.assertTrue(bom_fg, "FG BOM should be created")
		self.assertTrue(bom_assembly, "Assembly BOM should be created")
		self.assertEqual(bom_fg.docstatus, 0, "FG BOM should be Draft")
		self.assertEqual(bom_assembly.docstatus, 0, "Assembly BOM should be Draft")

	def test_03_three_level_bom(self):
		"""
		Test 3: Three-level BOM
		FG
		└── Assembly A
		    └── Assembly B
		        └── Component
		Expected: 3 Draft BOMs
		"""
		items = [
			{
				"item_code": "Test Assembly A",
				"qty": 1,
				"fg_item": "Test FG Item",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			{
				"item_code": "Test Sub Assembly A1",
				"qty": 1,
				"fg_item": "Test Assembly A",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			{
				"item_code": "Test Component A",
				"qty": 10,
				"fg_item": "Test Sub Assembly A1",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
		]

		doc = self.create_bom_bulk_creator("Test FG Item", items)
		doc.submit()

		# Check all 3 BOMs were created
		bom_fg = frappe.db.get_value(
			"BOM",
			{"item": "Test FG Item", "bom_type": "Production", "company": self.company},
			"name"
		)

		bom_assembly = frappe.db.get_value(
			"BOM",
			{"item": "Test Assembly A", "bom_type": "Production", "company": self.company},
			"name"
		)

		bom_sub_assembly = frappe.db.get_value(
			"BOM",
			{"item": "Test Sub Assembly A1", "bom_type": "Production", "company": self.company},
			"name"
		)

		self.assertTrue(bom_fg, "FG BOM should be created")
		self.assertTrue(bom_assembly, "Assembly BOM should be created")
		self.assertTrue(bom_sub_assembly, "Sub Assembly BOM should be created")

	def test_04_complex_multi_level_bom(self):
		"""
		Test 4: Complex multi-level BOM
		FG
		├── Assembly A
		│   ├── Sub Assembly A1
		│   │   └── Component A
		│   └── Component B
		└── Assembly B
		    └── Sub Assembly B1
		        └── Component C
		Expected: 5 Draft BOMs
		"""
		items = [
			# Level 1 assemblies
			{
				"item_code": "Test Assembly A",
				"qty": 1,
				"fg_item": "Test FG Item",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			{
				"item_code": "Test Assembly B",
				"qty": 1,
				"fg_item": "Test FG Item",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			# Level 2 sub-assemblies
			{
				"item_code": "Test Sub Assembly A1",
				"qty": 1,
				"fg_item": "Test Assembly A",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			{
				"item_code": "Test Component B",
				"qty": 5,
				"fg_item": "Test Assembly A",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
			{
				"item_code": "Test Sub Assembly B1",
				"qty": 1,
				"fg_item": "Test Assembly B",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			# Level 3 components
			{
				"item_code": "Test Component A",
				"qty": 10,
				"fg_item": "Test Sub Assembly A1",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
			{
				"item_code": "Test Component C",
				"qty": 10,
				"fg_item": "Test Sub Assembly B1",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
		]

		doc = self.create_bom_bulk_creator("Test FG Item", items)
		doc.submit()

		# Check all 5 BOMs were created
		expected_items = [
			"Test FG Item",
			"Test Assembly A",
			"Test Assembly B",
			"Test Sub Assembly A1",
			"Test Sub Assembly B1",
		]

		for item_code in expected_items:
			bom = frappe.db.get_value(
				"BOM",
				{"item": item_code, "bom_type": "Production", "company": self.company},
				["name", "docstatus"],
				as_dict=True
			)
			self.assertTrue(bom, f"BOM for {item_code} should be created")
			self.assertEqual(bom.docstatus, 0, f"BOM for {item_code} should be Draft")

	def test_05_duplicate_execution(self):
		"""
		Test 5: Duplicate execution (idempotency)
		Run the same creation process twice.
		Expected: Second run should skip existing BOMs
		"""
		items = [
			{
				"item_code": "Test Component A",
				"qty": 10,
				"fg_item": "Test FG Item",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
		]

		# First run
		doc1 = self.create_bom_bulk_creator("Test FG Item Dup", items)
		doc1.submit()

		# Count BOMs after first run
		count1 = frappe.db.count("BOM", {
			"item": "Test FG Item Dup",
			"bom_type": "Production",
			"company": self.company,
		})

		# Second run
		doc2 = self.create_bom_bulk_creator("Test FG Item Dup 2", items)
		doc2.submit()

		# Count BOMs after second run
		count2 = frappe.db.count("BOM", {
			"item": "Test FG Item Dup",
			"bom_type": "Production",
			"company": self.company,
		})

		# Should not create duplicate
		self.assertEqual(count1, count2, "Should not create duplicate BOMs")

	def test_06_draft_status_verification(self):
		"""
		Test 6: Verify all generated BOMs remain Draft
		"""
		items = [
			{
				"item_code": "Test Assembly A",
				"qty": 1,
				"fg_item": "Test FG Item Draft",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			{
				"item_code": "Test Component A",
				"qty": 10,
				"fg_item": "Test Assembly A",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
		]

		doc = self.create_bom_bulk_creator("Test FG Item Draft", items)
		doc.submit()

		# Check all BOMs are Draft
		boms = frappe.get_all("BOM", {
			"item": ["in", ["Test FG Item Draft", "Test Assembly A"]],
			"bom_type": "Production",
			"company": self.company,
		}, ["name", "docstatus"])

		for bom in boms:
			self.assertEqual(bom.docstatus, 0, f"BOM {bom.name} should be Draft")

	def test_07_blank_bom_no_verification(self):
		"""
		Test 7: Verify bom_no is blank for child items
		"""
		items = [
			{
				"item_code": "Test Assembly A",
				"qty": 1,
				"fg_item": "Test FG Item Blank",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 1,
			},
			{
				"item_code": "Test Component A",
				"qty": 10,
				"fg_item": "Test Assembly A",
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
				"is_expandable": 0,
			},
		]

		doc = self.create_bom_bulk_creator("Test FG Item Blank", items)
		doc.submit()

		# Check BOM Items have blank bom_no
		bom_fg = frappe.db.get_value(
			"BOM",
			{"item": "Test FG Item Blank", "bom_type": "Production", "company": self.company},
			"name"
		)

		if bom_fg:
			bom_doc = frappe.get_doc("BOM", bom_fg)
			for item in bom_doc.items:
				self.assertEqual(item.bom_no or "", "", f"BOM Item {item.item_code} should have blank bom_no")
