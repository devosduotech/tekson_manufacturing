# Copyright (c) 2026, OSDuo Tech LLP. All rights reserved.
# Developer & Maintainer: OSDuo Tech LLP <developer@osduotech.com>

from collections import OrderedDict

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from erpnext.manufacturing.doctype.bom.bom import get_bom_item_rate

BOM_FIELDS = [
	"company",
	"rm_cost_as_per",
	"project",
	"currency",
	"conversion_rate",
	"buying_price_list",
	"target_fg_warehouse",
]

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


class BOMBulkCreator(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from tekson_manufacturing.doctype.bom_bulk_creator_item.bom_bulk_creator_item import BOMBulkCreatorItem

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
		status: DF.Literal["Draft", "In Progress", "Completed", "Failed", "Cancelled"]
		target_fg_warehouse: DF.Link
		uom: DF.Link | None
	# end: auto-generated types

	def before_save(self):
		self.set_status()
		self.set_parent_row_no()
		self.set_is_expandable()
		self.set_conversion_factor()
		self.set_reference_id()
		self.set_rate_for_items()

	def validate(self):
		self.validate_items()
		self.validate_hierarchy_cycles()

	def validate_items(self):
		for row in self.items:
			if row.is_expandable and row.item_code == self.item_code:
				frappe.throw(_("Item {0} cannot be added as a sub-assembly of itself").format(row.item_code))

			if row.parent_row_no and row.fg_item == self.item_code:
				frappe.throw(
					_("At row {0}: Parent Row No cannot be set for item {1}").format(row.idx, row.item_code),
					title=_("Remove Parent Row No in Items Table"),
				)

	def validate_hierarchy_cycles(self):
		parent_map = {}
		for row in self.items:
			if row.fg_reference_id and row.fg_reference_id != self.name:
				parent_map[row.name] = row.fg_reference_id

		for row_name, parent_name in parent_map.items():
			visited = set()
			current = parent_name
			while current and current != self.name:
				if current in visited:
					frappe.throw(
						_("Cycle detected in hierarchy involving row {0}").format(row_name),
						title=_("Invalid Hierarchy"),
					)
				visited.add(current)
				current = parent_map.get(current)

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
		if not self.items:
			return

		for row in self.items:
			if not row.bom_created:
				return

		self.status = "Completed"

	def set_conversion_factor(self):
		for row in self.items:
			row.conversion_factor = 1.0

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
				divisor = flt(row.qty) * flt(row.conversion_factor)
				row.rate = flt(row.amount) / divisor if divisor else 0

			amount += flt(row.amount)

		return amount

	def set_parent_row_no(self):
		"""Auto-calculate parent_row_no from fg_item mapping."""
		# Build map: item_code → row.idx (for expandable rows that are parents)
		item_row_map = {}
		for row in self.items:
			if row.item_code not in item_row_map:
				item_row_map[row.item_code] = row.idx

		for row in self.items:
			if row.fg_item and row.fg_item != self.item_code:
				row.parent_row_no = item_row_map.get(row.fg_item, "")

	def set_is_expandable(self):
		fg_items = [row.fg_item for row in self.items if row.fg_item != self.item_code]
		for row in self.items:
			row.is_expandable = 0
			if row.item_code in fg_items:
				row.is_expandable = 1

	@frappe.whitelist()
	def enqueue_create_boms(self):
		self.check_permission("write")
		self.validate_for_bom_creation()

		current_status = frappe.db.get_value("BOM Bulk Creator", self.name, "status")
		if current_status == "In Progress":
			frappe.throw(_("BOM creation is already in progress"))

		frappe.db.set_value("BOM Bulk Creator", self.name, "status", "In Progress")
		frappe.db.commit()
		self.enqueue_bom_creation()

	def validate_for_bom_creation(self):
		if not self.target_fg_warehouse:
			frappe.throw(_("Target FG Warehouse is required for BOM creation"))

		if not self.company:
			frappe.throw(_("Company is required for BOM creation"))

		for row in self.items:
			if not row.item_code:
				frappe.throw(_("Row {0}: Item Code is required").format(row.idx))
			if flt(row.qty) <= 0:
				frappe.throw(_("Row {0}: Quantity must be greater than zero").format(row.idx))
			if row.is_expandable and not row.target_fg_warehouse:
				frappe.throw(
					_("Row {0}: Target FG Warehouse is required for sub-assembly {1}").format(
						row.idx, row.item_code
					)
				)

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
		Create all BOMs as Draft (bottom-up).
		All BOMs are saved as Draft — child bom_no references are intentionally
		left blank because ERPNext requires referenced BOMs to be submitted.
		User manually updates bom_no, operations, quality inspection templates, etc.

		For sub-assemblies used in multiple parents (same item_code), only ONE BOM
		is created and shared across all parents.
		"""
		self.db_set("status", "In Progress")

		# Step 1: Group items by their parent fg_item
		# Key: fg_item (item_code), Value: list of child rows
		fg_children = OrderedDict()
		for row in self.items:
			fg_children.setdefault(row.fg_item, []).append(row)

		# Step 2: Build BOM creation queue (bottom-up)
		# Key: item_code, Value: dict with items list and fg_item_data
		bom_queue = OrderedDict()

		# Root FG
		bom_queue[self.item_code] = frappe._dict({
			"bom_items": fg_children.get(self.item_code, []),
			"bom_no": "",
			"fg_item_data": self,
		})

		# Sub-assemblies (expandable items) - one entry per unique item_code
		for row in self.items:
			if row.is_expandable and row.item_code not in bom_queue:
				bom_queue[row.item_code] = frappe._dict({
					"bom_items": fg_children.get(row.item_code, []),
					"bom_no": "",
					"fg_item_data": row,
				})

		# Reverse for bottom-up processing (leaf sub-assemblies first, root last)
		reverse_queue = OrderedDict(reversed(list(bom_queue.items())))

		try:
			for item_code, data in reverse_queue.items():
				if not data.bom_items:
					continue
				self.create_bom(item_code, data.fg_item_data, data.bom_items, bom_queue)

			for row in self.items:
				frappe.db.set_value("BOM Bulk Creator Item", row.name, "bom_created", 1)

			self.db_set("status", "Completed")
			frappe.msgprint(_("BOMs created successfully as Draft"))
		except Exception:
			traceback = frappe.get_traceback(with_context=True)
			self.db_set(
				{
					"status": "Failed",
					"error_log": traceback,
				}
			)

			frappe.msgprint(_("BOMs creation failed"))

	@frappe.whitelist()
	def edit_qty(self, docname: str, qty: float):
		self.check_permission("write")

		if flt(qty) <= 0:
			frappe.throw(_("Quantity must be greater than zero"))

		if not frappe.db.exists("BOM Bulk Creator Item", {"name": docname, "parent": self.name}):
			frappe.throw(_("BOM Bulk Creator Item {0} does not exist").format(docname))

		for row in self.items:
			if row.name == docname:
				row.qty = flt(qty)
				break

		self.set_rate_for_items()
		self.save()

		return self

	def create_bom(self, item_code, fg_item_data, items, bom_queue):
		"""
		Create a single BOM as Draft.
		bom_no is intentionally left blank — ERPNext requires referenced BOMs to be submitted.
		"""
		if frappe.db.exists(
			"BOM",
			{
				"item": item_code,
				"bom_type": "Production",
				"docstatus": 0,
			},
		):
			existing = frappe.db.get_value(
				"BOM",
				{"item": item_code, "bom_type": "Production", "docstatus": 0},
				"name",
			)
			bom_queue[item_code].bom_no = existing
			return

		bom = frappe.new_doc("BOM")
		bom.update(
			{
				"item": item_code,
				"bom_type": "Production",
				"quantity": 1,
			}
		)

		for field in BOM_FIELDS:
			value = fg_item_data.get(field) if hasattr(fg_item_data, "get") and fg_item_data.get(field) else self.get(field)
			if value:
				bom.set(field, value)

		# Push routing to BOM — ERPNext auto-populates operations from routing
		routing = fg_item_data.get("routing") if hasattr(fg_item_data, "get") else None
		if routing:
			bom.with_operations = 1
			bom.routing = routing

		# Deduplicate items by item_code (same RM under same parent)
		# Don't aggregate - take first occurrence only (BOM is shared across instances)
		seen_items = {}
		for item in items:
			if item.item_code not in seen_items:
				seen_items[item.item_code] = item

		for item_code_key, item in seen_items.items():
			item.do_not_explode = 1

			item_args = {}
			for field in BOM_ITEM_FIELDS:
				item_args[field] = item.get(field)

			# For expandable child items, set bom_no from the queue
			if item.is_expandable and item.item_code in bom_queue:
				item_args["bom_no"] = bom_queue[item.item_code].bom_no
			else:
				item_args["bom_no"] = ""

			item_args.update(
				{
					"allow_scrap_items": 1,
					"include_item_in_manufacturing": 1,
				}
			)

			bom.append("items", item_args)

		bom.save(ignore_permissions=True)

		bom_queue[item_code].bom_no = bom.name

	@frappe.whitelist()
	def get_default_bom(self, item_code: str) -> str:
		self.check_permission("read")
		return frappe.get_cached_value("Item", item_code, "default_bom")

	@frappe.whitelist()
	def add_item(self, **kwargs):
		self.check_permission("write")

		if isinstance(kwargs, str):
			kwargs = frappe.parse_json(kwargs)

		if isinstance(kwargs, dict):
			kwargs = frappe._dict(kwargs)

		item_info = get_item_details(kwargs.item_code)

		parent_row_no = ""
		if kwargs.fg_reference_id and self.name != kwargs.fg_reference_id:
			parent_row_no = get_parent_row_no(self, kwargs.fg_reference_id)

		kwargs.update(
			{
				"uom": item_info.stock_uom,
				"stock_uom": item_info.stock_uom,
				"conversion_factor": 1,
			}
		)

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
		self.check_permission("write")

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

			item_row = self.append(
				"items",
				{
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
				},
			)

			parent_row_no = item_row.idx
			name = ""
		else:
			parent_row_no = get_parent_row_no(self, kwargs.fg_reference_id)

		for row in bom_item.get("items"):
			row = frappe._dict(row)
			item_info = get_item_details(row.item_code)
			self.append(
				"items",
				{
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
				},
			)

		self.save()

		return self

	@frappe.whitelist()
	def delete_node(self, **kwargs):
		if isinstance(kwargs, str):
			kwargs = frappe.parse_json(kwargs)

		if isinstance(kwargs, dict):
			kwargs = frappe._dict(kwargs)

		self.check_permission("write")

		if not kwargs.docname:
			frappe.throw(_("Docname is required to delete a node"))

		row = next((row for row in self.items if row.name == kwargs.docname), None)
		if not row:
			frappe.throw(_("BOM Bulk Creator Item with name {0} does not exist").format(kwargs.docname))

		descendants = self._get_descendants(kwargs.docname)
		descendants_to_delete = [d for d in descendants if d != kwargs.docname]

		for desc_name in reversed(descendants_to_delete):
			desc_row = next((r for r in self.items if r.name == desc_name), None)
			if desc_row:
				desc_row.delete()
				self.remove(desc_row)

		row = next((r for r in self.items if r.name == kwargs.docname), None)
		if row:
			row.delete()
			self.remove(row)

		self.set_rate_for_items()
		self.save()

		return self

	def _get_descendants(self, node_name):
		children = [
			row.name for row in self.items
			if row.fg_reference_id == node_name
		]
		descendants = list(children)
		for child_name in children:
			descendants.extend(self._get_descendants(child_name))
		return descendants


@frappe.whitelist()
def get_children(doctype: str | None = None, parent: str | None = None, **kwargs):
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
		"name as docname",
		"uom",
		"rate",
		"amount",
		"fg_item",
		"target_fg_warehouse",
		"source_warehouse",
	]

	query_filters = {
		"fg_item": parent,
		"parent": kwargs.parent_id,
	}

	if kwargs.get("name"):
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
