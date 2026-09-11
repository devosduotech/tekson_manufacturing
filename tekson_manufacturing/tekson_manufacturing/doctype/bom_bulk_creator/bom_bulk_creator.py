# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
BOM Bulk Creator — Phase 1

Creates multi-level BOM hierarchies as Draft.
Does NOT submit BOMs. Does NOT link child bom_no.
Maintains internal parent-child mapping for future Phase 2.
"""

from collections import OrderedDict

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from erpnext.manufacturing.doctype.bom.bom import get_bom_item_rate


class BOMBulkCreator(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from tekson_manufacturing.doctype.bom_bulk_creator_item.bom_bulk_creator_item import BOMBulkCreatorItem

		amended_from: DF.Link | None
		buying_price_list: DF.Link | None
		company: DF.Link
		conversion_rate: DF.Float
		currency: DF.Link
		default_warehouse: DF.Link | None
		error_log: DF.Text | None
		item_code: DF.Link
		item_group: DF.Link | None
		item_name: DF.Data | None
		items: DF.Table[BOMBulkCreatorItem]
		plc_conversion_rate: DF.Float
		price_list_currency: DF.Link | None
		project: DF.Link | None
		qty: DF.Float
		raw_material_cost: DF.Currency
		remarks: DF.TextEditor | None
		rm_cost_as_per: DF.Literal["Valuation Rate", "Last Purchase Rate", "Price List"]
		set_rate_based_on_warehouse: DF.Check
		status: DF.Literal["Draft", "Submitted", "In Progress", "Completed", "Failed", "Cancelled"]
		uom: DF.Link | None
	# end: auto-generated types

	def before_save(self):
		self.set_status()
		self.set_is_expandable()
		self.set_conversion_factor()
		self.set_reference_id()
		self.set_rate_for_items()

	def validate(self):
		self.validate_items()

	def validate_items(self):
		for row in self.items:
			if row.is_expandable and row.item_code == self.item_code:
				frappe.throw(_("Item {0} cannot be added as a sub-assembly of itself").format(row.item_code))

			if not row.parent_row_no and row.fg_item and row.fg_item != self.item_code:
				frappe.throw(
					_("At row {0}: set Parent Row No for item {1}").format(row.idx, row.item_code),
					title=_("Set Parent Row No in Items Table"),
				)

			elif row.parent_row_no and row.fg_item == self.item_code:
				frappe.throw(
					_("At row {0}: Parent Row No cannot be set for item {1}").format(row.idx, row.item_code),
					title=_("Remove Parent Row No in Items Table"),
				)

	def set_status(self, save=False):
		self.status = {
			0: "Draft",
			1: "Submitted",
			2: "Cancelled",
		}[self.docstatus]

		self.set_status_completed()
		if save:
			self.db_set("status", self.status)

	def set_status_completed(self):
		if self.docstatus != 1:
			return

		has_completed = True
		for row in self.items:
			if row.is_expandable and not row.bom_created:
				has_completed = False
				break

		if not frappe.get_cached_value("BOM", {"bom_bulk_creator": self.name, "item": self.item_code}, "name"):
			has_completed = False

		if has_completed:
			self.status = "Completed"

	def on_cancel(self):
		self.set_status(True)

	def set_conversion_factor(self):
		for row in self.items:
			row.conversion_factor = 1.0

	def before_submit(self):
		self.validate_fields()
		self.set_status()

	def set_reference_id(self):
		parent_reference = {row.idx: row.name for row in self.items}

		for row in self.items:
			ref_id = ""

			if row.parent_row_no:
				ref_id = parent_reference.get(cint(row.parent_row_no))

			if row.fg_reference_id and row.fg_reference_id == ref_id:
				continue

			if row.parent_row_no:
				row.fg_reference_id = ref_id
			elif row.fg_item == self.item_code:
				row.fg_reference_id = self.name

	@frappe.whitelist()
	def add_boms(self):
		self.check_permission("submit")
		self.submit()

	def set_rate_for_items(self):
		amount = self.get_raw_material_cost()
		self.raw_material_cost = amount

	def get_raw_material_cost(self, fg_item=None, amount=0):
		if not fg_item:
			fg_item = self.item_code

		for row in self.items:
			if row.fg_item != fg_item:
				continue

			if not row.is_expandable:
				row.rate = get_bom_item_rate(
					{
						"company": self.company,
						"item_code": row.item_code,
						"bom_no": "",
						"qty": row.qty,
						"uom": row.uom,
						"stock_uom": row.stock_uom,
						"conversion_factor": row.conversion_factor,
						"sourced_by_supplier": row.sourced_by_supplier,
					},
					self,
				)

				row.amount = flt(row.rate) * flt(row.qty)

			else:
				row.amount = 0.0
				row.amount = self.get_raw_material_cost(row.item_code, row.amount)
				row.rate = flt(row.amount) / (flt(row.qty) * flt(row.conversion_factor))

			amount += flt(row.amount)

		return amount

	def set_is_expandable(self):
		fg_items = [row.fg_item for row in self.items if row.fg_item != self.item_code]
		for row in self.items:
			row.is_expandable = 0
			if row.item_code in fg_items:
				row.is_expandable = 1

	def validate_fields(self):
		fields = {
			"items": "Items",
		}

		for field, label in fields.items():
			if not self.get(field):
				frappe.throw(_("Please set {0} in BOM Bulk Creator {1}").format(_(label), self.name))

	def on_submit(self):
		self.enqueue_bom_creation()

	@frappe.whitelist()
	def enqueue_create_boms(self):
		self.check_permission("submit")
		self.enqueue_bom_creation()

	def enqueue_bom_creation(self):
		frappe.enqueue(
			self.create_boms,
			queue="short",
			timeout=600,
			is_async=True,
		)

		frappe.msgprint(
			_("BOMs creation has been enqueued, kindly check the status after some time"), alert=True
		)

	def create_boms(self):
		"""
		Phase 1: Create all BOMs as Draft without submitting.

		Workflow:
		1. Build complete multi-level hierarchy
		2. Identify all items that need their own BOM
		3. Create BOMs as Draft (docstatus = 0)
		4. Do NOT submit any BOM
		5. Do NOT populate bom_no for child relationships
		6. Track parent-child mapping internally
		"""
		self.db_set("status", "In Progress")

		try:
			# Step 1: Build complete hierarchy
			hierarchy = self.build_bom_hierarchy()

			# Step 2: Create all BOMs as Draft
			creation_result = self.create_all_boms_as_draft(hierarchy)

			# Step 3: Update status
			if creation_result["failed"] > 0:
				self.db_set({
					"status": "Failed",
					"error_log": creation_result["error_log"],
				})
				frappe.msgprint(
					_("BOM creation completed with {0} failures. Check error log.").format(creation_result["failed"])
				)
			else:
				self.db_set("status", "Completed")
				frappe.msgprint(
					_("Successfully created {0} Draft BOMs").format(creation_result["created"])
				)

		except Exception:
			traceback = frappe.get_traceback(with_context=True)
			self.db_set({
				"status": "Failed",
				"error_log": traceback,
			})
			frappe.msgprint(_("BOMs creation failed. Check error log."))

	def build_bom_hierarchy(self):
		"""
		Build complete multi-level BOM hierarchy from items table.

		Returns dict: {item_code: {"item_code": ..., "items": [...], "level": ..., "parent_item": ...}}
		"""
		hierarchy = OrderedDict()

		# Get all items and organize by fg_item (parent)
		for row in self.items:
			if row.fg_item == self.item_code:
				# Root level items
				key = (row.item_code, row.name)
				if key not in hierarchy:
					hierarchy[key] = {
						"item_code": row.item_code,
						"item_name": row.item_name,
						"items": [],
						"level": 0,
						"parent_item": self.item_code,
						"qty": row.qty,
						"uom": row.uom,
						"stock_uom": row.stock_uom,
						"conversion_factor": row.conversion_factor,
						"source_warehouse": row.source_warehouse,
						"rate": row.rate,
						"amount": row.amount,
						"is_expandable": row.is_expandable,
						"bom_creator_item": row.name,
					}
				hierarchy[key]["items"].append(row)

		# Process expandable items (sub-assemblies)
		for row in self.items:
			if row.fg_item != self.item_code and row.is_expandable:
				key = (row.item_code, row.name)
				if key not in hierarchy:
					hierarchy[key] = {
						"item_code": row.item_code,
						"item_name": row.item_name,
						"items": [],
						"level": self.get_item_level(row),
						"parent_item": row.fg_item,
						"qty": row.qty,
						"uom": row.uom,
						"stock_uom": row.stock_uom,
						"conversion_factor": row.conversion_factor,
						"source_warehouse": row.source_warehouse,
						"rate": row.rate,
						"amount": row.amount,
						"is_expandable": row.is_expandable,
						"bom_creator_item": row.name,
					}
				hierarchy[key]["items"].append(row)

		return hierarchy

	def get_item_level(self, row):
		"""Calculate the level of an item in the hierarchy"""
		level = 1
		current_fg = row.fg_item

		# Walk up the hierarchy
		for r in self.items:
			if r.item_code == current_fg and r.fg_item == self.item_code:
				return level
			elif r.item_code == current_fg:
				level += 1
				current_fg = r.fg_item

		return level

	def create_all_boms_as_draft(self, hierarchy):
		"""
		Create all BOMs as Draft from the hierarchy.

		Returns: {"created": int, "skipped": int, "failed": int, "error_log": str}
		"""
		result = {
			"created": 0,
			"skipped": 0,
			"failed": 0,
			"error_log": "",
			"bom_mapping": [],
		}

		errors = []

		for key, bom_data in hierarchy.items():
			try:
				bom_result = self.create_single_bom_draft(bom_data)

				if bom_result["status"] == "created":
					result["created"] += 1
					result["bom_mapping"].append({
						"parent_item": bom_data["parent_item"],
						"child_item": bom_data["item_code"],
						"generated_bom": bom_result["bom_name"],
						"level": bom_data["level"],
					})
				elif bom_result["status"] == "skipped":
					result["skipped"] += 1

			except Exception as e:
				result["failed"] += 1
				errors.append(f"Item {bom_data['item_code']}: {str(e)}")

		if errors:
			result["error_log"] = "\n".join(errors)

		return result

	def create_single_bom_draft(self, bom_data):
		"""
		Create a single BOM as Draft.

		Returns: {"status": "created"|"skipped", "bom_name": str}
		"""
		item_code = bom_data["item_code"]

		# Check for existing BOM
		existing_bom = self.check_existing_bom(item_code)

		if existing_bom:
			if existing_bom["docstatus"] == 1:
				# Submitted BOM exists - skip
				return {"status": "skipped", "bom_name": existing_bom["name"]}
			elif existing_bom["docstatus"] == 0:
				# Draft BOM exists - skip
				return {"status": "skipped", "bom_name": existing_bom["name"]}

		# Create new BOM as Draft
		bom = frappe.new_doc("BOM")
		bom.update({
			"item": item_code,
			"bom_type": "Production",
			"quantity": bom_data["qty"],
			"company": self.company,
			"rm_cost_as_per": self.rm_cost_as_per,
			"currency": self.currency,
			"conversion_rate": self.conversion_rate,
			"buying_price_list": self.buying_price_list,
			"project": self.project,
		})

		# Add BOM Items (child items)
		child_items = self.get_child_items_for_item(item_code)
		for child in child_items:
			bom.append("items", {
				"item_code": child["item_code"],
				"qty": child["qty"],
				"uom": child.get("uom", ""),
				"stock_qty": child.get("stock_qty", child["qty"]),
				"stock_uom": child.get("stock_uom", ""),
				"conversion_factor": child.get("conversion_factor", 1),
				"rate": child.get("rate", 0),
				"amount": child.get("amount", 0),
				"source_warehouse": child.get("source_warehouse", ""),
				"do_not_explode": 0,
				"allow_alternative_item": child.get("allow_alternative_item", 0),
				"sourced_by_supplier": child.get("sourced_by_supplier", 0),
				"include_item_in_manufacturing": 1,
				"bom_no": "",  # Intentionally blank - child BOM linking is Phase 2
			})

		# Save as Draft (docstatus = 0)
		bom.save(ignore_permissions=True)
		# Do NOT submit - keep as Draft

		# Mark the BOM Creator Item as created
		self.mark_bom_created(item_code)

		return {"status": "created", "bom_name": bom.name}

	def check_existing_bom(self, item_code):
		"""Check if a BOM already exists for this item"""
		existing = frappe.db.get_value(
			"BOM",
			{"item": item_code, "bom_type": "Production", "company": self.company},
			["name", "docstatus"],
			as_dict=True
		)
		return existing

	def get_child_items_for_item(self, parent_item_code):
		"""
		Get all child items for a given parent item from the hierarchy.
		These become the BOM Items in the generated BOM.
		"""
		child_items = []

		for row in self.items:
			if row.fg_item == parent_item_code:
				child_items.append({
					"item_code": row.item_code,
					"item_name": row.item_name,
					"qty": row.qty,
					"uom": row.uom,
					"stock_qty": row.stock_qty,
					"stock_uom": row.stock_uom,
					"conversion_factor": row.conversion_factor,
					"rate": row.rate,
					"amount": row.amount,
					"source_warehouse": row.source_warehouse,
					"allow_alternative_item": row.allow_alternative_item,
					"sourced_by_supplier": row.sourced_by_supplier,
				})

		return child_items

	def mark_bom_created(self, item_code):
		"""Mark the BOM Creator Item as having BOM created"""
		for row in self.items:
			if row.item_code == item_code:
				row.bom_created = 1
		self.save(ignore_permissions=True)

	@frappe.whitelist()
	def edit_qty(self, docname: str, qty: float):
		if not frappe.db.exists("BOM Bulk Creator Item", {"name": docname, "parent": self.name}):
			frappe.throw(_("BOM Bulk Creator Item {0} does not exist").format(docname))

		for row in self.items:
			if row.name == docname:
				row.qty = flt(qty)
				break

		self.set_rate_for_items()
		self.save()

		return self

	@frappe.whitelist()
	def get_default_bom(self, item_code: str) -> str:
		self.check_permission("read")
		return frappe.get_cached_value("Item", item_code, "default_bom")

	@frappe.whitelist()
	def add_item(self, **kwargs):
		if isinstance(kwargs, str):
			kwargs = frappe.parse_json(kwargs)

		if isinstance(kwargs, dict):
			kwargs = frappe._dict(kwargs)

		item_info = get_item_details(kwargs.item_code)

		parent_row_no = ""
		if kwargs.fg_reference_id and self.name != kwargs.fg_reference_id:
			parent_row_no = get_parent_row_no(self, kwargs.fg_reference_id)

		kwargs.update({
			"uom": item_info.stock_uom,
			"stock_uom": item_info.stock_uom,
			"conversion_factor": 1,
		})

		if parent_row_no:
			kwargs.update({"parent_row_no": parent_row_no})

		for key in BOM_ITEM_FIELDS:
			if key not in kwargs:
				kwargs[key] = ""

		self.append("items", kwargs)
		self.save()

		return self

	@frappe.whitelist()
	def add_sub_assembly(self, **kwargs):
		if isinstance(kwargs, str):
			kwargs = frappe.parse_json(kwargs)

		if isinstance(kwargs, dict):
			kwargs = frappe._dict(kwargs)

		bom_item = frappe.parse_json(kwargs.bom_item)

		name = kwargs.fg_reference_id
		parent_row_no = ""
		if not kwargs.convert_to_sub_assembly:
			item_info = get_item_details(bom_item.item_code)
			parent_row_no = get_parent_row_no(self, kwargs.fg_reference_id)

			item_row = self.append("items", {
				"item_code": bom_item.item_code,
				"qty": bom_item.qty,
				"uom": item_info.stock_uom,
				"fg_item": kwargs.fg_item,
				"conversion_factor": 1,
				"parent_row_no": parent_row_no,
				"fg_reference_id": name,
				"stock_qty": bom_item.qty,
				"do_not_explode": 1,
				"is_expandable": 1,
				"stock_uom": item_info.stock_uom,
				"allow_alternative_item": kwargs.allow_alternative_item,
			})

			parent_row_no = item_row.idx
			name = ""
		else:
			parent_row_no = get_parent_row_no(self, kwargs.fg_reference_id)

		for row in bom_item.get("items"):
			row = frappe._dict(row)
			item_info = get_item_details(row.item_code)
			self.append("items", {
				"item_code": row.item_code,
				"qty": row.qty,
				"fg_item": bom_item.item_code,
				"uom": item_info.stock_uom,
				"fg_reference_id": name,
				"parent_row_no": parent_row_no,
				"conversion_factor": 1,
				"do_not_explode": 1,
				"stock_qty": row.qty,
				"stock_uom": item_info.stock_uom,
			})

		self.save()

		return self

	@frappe.whitelist()
	def delete_node(self, **kwargs):
		if isinstance(kwargs, str):
			kwargs = frappe.parse_json(kwargs)

		if isinstance(kwargs, dict):
			kwargs = frappe._dict(kwargs)

		updated = False
		if kwargs.docname:
			row = next((row for row in self.items if row.name == kwargs.docname), None)
			if not row:
				frappe.throw(_("BOM Bulk Creator Item with name {0} does not exist").format(kwargs.docname))

			row.delete()
			self.remove(row)
			updated = True

		items = get_children(parent=kwargs.fg_item, parent_id=self.name)
		if items:
			for item in items:
				updated = True
				child_row = next((row for row in self.items if row.name == item.name), None)
				if child_row:
					child_row.delete()
					self.remove(child_row)

				if item.expandable:
					self.delete_node(fg_item=item.value)

		if updated:
			self.set_rate_for_items()
			self.save()

			return self

		return frappe._dict()

	@frappe.whitelist()
	def preview_boms(self):
		"""
		Dry run: show what BOMs would be created without actually creating them.
		Returns summary of hierarchy.
		"""
		hierarchy = self.build_bom_hierarchy()

		preview = {
			"total_boms": 0,
			"bom_list": [],
			"existing_boms": [],
		}

		for key, bom_data in hierarchy.items():
			existing = self.check_existing_bom(bom_data["item_code"])
			status = "will_create"
			if existing:
				if existing["docstatus"] == 1:
					status = "submitted_exists"
				else:
					status = "draft_exists"

			preview["bom_list"].append({
				"item_code": bom_data["item_code"],
				"level": bom_data["level"],
				"parent_item": bom_data["parent_item"],
				"child_items_count": len(self.get_child_items_for_item(bom_data["item_code"])),
				"status": status,
			})

			if not existing:
				preview["total_boms"] += 1
			else:
				preview["existing_boms"].append(existing["name"])

		return preview


# Helper functions

BOM_ITEM_FIELDS = [
	"item_code",
	"qty",
	"uom",
	"rate",
	"stock_qty",
	"stock_uom",
	"conversion_factor",
	"do_not_explode",
	"source_warehouse",
	"allow_alternative_item",
]


@frappe.whitelist()
def get_children(doctype=None, parent=None, **kwargs):
	if isinstance(kwargs, str):
		kwargs = frappe.parse_json(kwargs)

	if isinstance(kwargs, dict):
		kwargs = frappe._dict(kwargs)

	frappe.has_permission("BOM Bulk Creator", "read", doc=kwargs.parent_id, throw=True)

	fields = [
		"item_code as value",
		"item_name as title",
		"is_expandable as expandable",
		"parent as parent_id",
		"qty",
		"idx",
		"'BOM Bulk Creator Item' as doctype",
		"name",
		"uom",
		"rate",
		"amount",
	]

	query_filters = {
		"fg_item": parent,
		"parent": kwargs.parent_id,
	}

	if kwargs.name:
		query_filters["name"] = kwargs.name

	return frappe.get_all("BOM Bulk Creator Item", fields=fields, filters=query_filters, order_by="idx")


def get_item_details(item_code):
	return frappe.get_cached_value(
		"Item", item_code, ["item_name", "description", "image", "stock_uom", "default_bom"], as_dict=1
	)


def get_parent_row_no(doc, name):
	for row in doc.items:
		if row.name == name:
			return row.idx

	if name == doc.name:
		return None

	frappe.msgprint(_("Parent Row No not found for {0}").format(name), alert=True)

	return None
