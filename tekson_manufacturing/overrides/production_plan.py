"""
Custom Production Plan — batch rounding + WO consolidation by planned date
+ demand-driven FG warehouse routing for split (dual target) BOMs
"""

import frappe
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from frappe.utils import flt

from tekson_manufacturing.services.batch_planning import get_production_qty


class TeksonProductionPlan(ProductionPlan):
    def combine_subassembly_items(self, sub_assembly_items_store):
        """Override: include schedule_date when combine_sub_items enabled"""
        key_wise_data = {}
        for row in sub_assembly_items_store:
            key = (
                row.get("production_item"),
                row.get("fg_warehouse"),
                row.get("bom_no"),
                row.get("type_of_manufacturing"),
                str(row.get("schedule_date", "")) if self.combine_sub_items else "",
            )
            if key not in key_wise_data:
                key_wise_data[key] = row
                continue
            existing_row = key_wise_data[key]
            if existing_row:
                existing_row.qty += flt(row.qty)
                existing_row.stock_qty += flt(row.stock_qty)
                existing_row.bom_level = max(existing_row.bom_level, row.bom_level)

        return list(key_wise_data.values())

    def set_sub_assembly_items_based_on_level(self, row, bom_data, manufacturing_type=None):
        super().set_sub_assembly_items_based_on_level(row, bom_data, manufacturing_type)
        self._route_split_fg_warehouse(row, bom_data)

    def _route_split_fg_warehouse(self, po_item_row, bom_data):
        """Demand-driven split routing for BOMs with target_fg_warehouse_2.

        For every sub-assembly row whose component BOM has a secondary target
        FG warehouse, match the consuming BOM Item row's source_warehouse
        against the component BOM's primary (target_fg_warehouse) or secondary
        (target_fg_warehouse_2) target:

        - source matches primary   -> row outputs to the primary warehouse
        - source matches secondary -> row outputs to the secondary warehouse
        - matches neither          -> row keeps the default warehouse

        Rows that land on different warehouses are NOT combined (the combine
        key includes fg_warehouse), so the plan creates one Work Order per
        destination with its own quantity — no intra-WO split required.

        A dual-target demand whose source matches neither target is reported
        to the user instead of silently falling back (it would otherwise merge
        with other default-routed demand into a single Work Order).

        Only immediate BOM Item rows (one level up) are inspected; demands
        from multiple parent BOMs are naturally separate rows in bom_data.
        """
        # item_code of the row being expanded -> BOM that contains its children
        meta = frappe.get_meta("BOM")
        if not meta.has_field("target_fg_warehouse_2"):
            # Custom field not created yet (patch not run) — no split routing
            return

        target_fields = [
            f for f in ("target_fg_warehouse", "target_fg_warehouse_2") if meta.has_field(f)
        ]
        containing_bom = {po_item_row.get("item_code"): po_item_row.get("bom_no")}
        targets_cache = {}
        sources_cache = {}
        unrouted = []
        unrouted_details = []

        for data in bom_data:
            production_item = data.get("production_item")
            production_bom = data.get("bom_no")

            # Register this row's production BOM as the container for its own
            # children (children were appended after this row during explosion).
            if production_item and production_bom:
                containing_bom.setdefault(production_item, production_bom)

            if not (production_item and production_bom):
                continue

            parent_bom = containing_bom.get(data.get("parent_item_code"))
            if not parent_bom:
                continue

            targets = targets_cache.get(production_bom)
            if targets is None:
                targets = frappe.db.get_value(
                    "BOM",
                    production_bom,
                    target_fields,
                    as_dict=True,
                )
                targets_cache[production_bom] = targets or frappe._dict()

            secondary = targets.get("target_fg_warehouse_2")
            if not secondary:
                continue
            primary = targets.get("target_fg_warehouse")

            cache_key = (parent_bom, production_item)
            if cache_key not in sources_cache:
                rows = frappe.get_all(
                    "BOM Item",
                    filters={"parent": parent_bom, "item_code": production_item},
                    fields=["source_warehouse"],
                )
                sources_cache[cache_key] = [r.source_warehouse for r in rows if r.source_warehouse]

            matched = next(
                (wh for wh in sources_cache[cache_key] if wh in (primary, secondary)),
                None,
            )
            if matched:
                data.fg_warehouse = matched
            elif cache_key not in unrouted:
                unrouted.append(cache_key)
                unrouted_details.append(
                    {
                        "item": production_item,
                        "parent_bom": parent_bom,
                        "source": ", ".join(sources_cache[cache_key]),
                        "primary": primary,
                        "secondary": secondary,
                    }
                )

        if unrouted_details:
            lines = [
                f"  - {d['item']} in {d['parent_bom']}: Source Warehouse "
                f"{d['source'] or '(empty)'} matches neither {d['primary']} (Target 1) "
                f"nor {d['secondary']} (Target 2)"
                for d in unrouted_details
            ]
            frappe.msgprint(
                "Split routing skipped for these demands — they keep the default warehouse "
                "and may merge with other demand into a single Work Order:\n"
                + "\n".join(lines)
                + "\nSet the BOM Item Source Warehouse to Target FG Warehouse or "
                "Target FG Warehouse 2 to route them.",
                title="Split Routing Warning",
                indicator="orange",
            )

    def make_work_order_for_subassembly_items(self, wo_list, subcontracted_po, default_warehouses):
        self._apply_batch_rounding()
        super().make_work_order_for_subassembly_items(wo_list, subcontracted_po, default_warehouses)

    def _apply_batch_rounding(self):
        for item in self.sub_assembly_items:
            if item.bom_no and item.qty > 0:
                result = get_production_qty(item.bom_no, item.qty)
                if result["is_fixed_batch"]:
                    item.qty = result["production_qty"]
