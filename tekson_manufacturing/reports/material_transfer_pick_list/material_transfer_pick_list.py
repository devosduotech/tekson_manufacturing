"""
Material Transfer Pick List Report

Shows materials to be transferred from source warehouses to department WIP
warehouses for submitted, open Work Orders (not Completed, Closed, Stopped or
Cancelled) within a date range.

Access:
    ERPNext UI → Reports → Material Transfer Pick List
    Or from Work Order List → Actions → Pick List
"""

import frappe
from frappe import _
from frappe.utils import flt

from tekson_manufacturing.utils import operation_warehouse as operation_warehouse_utils


def execute(filters=None):
    """Main report execution"""
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": _("Work Order"),
            "fieldname": "work_order",
            "fieldtype": "Link",
            "options": "Work Order",
            "width": 180
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 250
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Operation"),
            "fieldname": "operation",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Qty/Piece"),
            "fieldname": "required_per_piece",
            "fieldtype": "Float",
            "width": 80
        },
        {
            "label": _("Required"),
            "fieldname": "required_total",
            "fieldtype": "Float",
            "precision": 3,
            "width": 90
        },
        {
            "label": _("From Warehouse"),
            "fieldname": "source_warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 180
        },
        {
            "label": _("Available"),
            "fieldname": "available_qty",
            "fieldtype": "Float",
            "precision": 3,
            "width": 90
        },
        {
            "label": _("To Transfer"),
            "fieldname": "balance_to_transfer",
            "fieldtype": "Float",
            "precision": 3,
            "width": 90
        },
        {
            "label": _("To (WIP)"),
            "fieldname": "target_warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 180
        }
    ]


def get_data(filters):
    """Fetch data for the report"""
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')

    if not from_date or from_date == '':
        from_date = '2026-01-01'
    if not to_date or to_date == '':
        to_date = '2026-12-31'

    # Get submitted Work Orders that are still open
    work_orders = frappe.db.sql("""
        SELECT
            wo.name,
            wo.production_item,
            wo.qty,
            wo.status,
            wo.planned_start_date,
            wo.wip_warehouse,
            wo.source_warehouse,
            wo.bom_no
        FROM `tabWork Order` wo
        WHERE wo.docstatus = 1
          AND wo.status NOT IN ('Completed', 'Closed', 'Stopped', 'Cancelled')
          AND DATE(wo.planned_start_date) BETWEEN %s AND %s
        ORDER BY wo.planned_start_date
    """, (from_date, to_date), as_dict=True)

    frappe.logger().info(f"Pick List Report: Found {len(work_orders)} WOs between {from_date} and {to_date}")

    if not work_orders:
        return []

    # Job Card WIP + workstation per (WO, operation) — fallbacks when BOM
    # Operation configuration cannot be resolved. Case/whitespace-tolerant
    # key; keep the first non-empty value of each.
    jc_map = {}
    for jc in frappe.get_all(
            'Job Card',
            filters={'work_order': ['in', [wo.name for wo in work_orders]]},
            fields=['work_order', 'operation', 'wip_warehouse', 'workstation'],
            order_by='name asc'):
        key = (jc.work_order, operation_warehouse_utils.normalize_operation(jc.operation))
        wip_wh, workstation = jc_map.get(key, ('', ''))
        jc_map[key] = (
            wip_wh or (jc.wip_warehouse or ''),
            workstation or (jc.get('workstation') or ''),
        )

    operation_wh_cache = {}
    result = []

    for wo in work_orders:
        # Get BOM items
        if not wo.bom_no or not frappe.db.exists('BOM', wo.bom_no):
            frappe.logger().warning(f"WO {wo.name}: No BOM or BOM not found (bom_no={wo.bom_no})")
            continue

        bom_items = frappe.get_all('BOM Item',
            filters={'parent': wo.bom_no},
            fields=['item_code', 'item_name', 'qty', 'source_warehouse', 'operation']
        )

        frappe.logger().info(f"WO {wo.name}: Found {len(bom_items)} BOM items for BOM {wo.bom_no}")

        for item in bom_items:
            required_total = flt(item.qty) * flt(wo.qty)

            # Source warehouse: BOM item source → WO source → Raw Material Stores
            source_wh = item.source_warehouse or wo.source_warehouse or ''

            # Target: driven by the BOM Item's operation (BOM Operation →
            # workstation → plant floor WIP), Job Card WIP / workstation as
            # fallback — never the WO header (first-operation) warehouse.
            operation = (item.get('operation') or '').strip()
            reasons = []
            if operation:
                jc_wh, jc_workstation = jc_map.get(
                    (wo.name, operation_warehouse_utils.normalize_operation(operation)),
                    ('', ''),
                )
                target_wh = operation_warehouse_utils.resolve_target_warehouse(
                    wo.bom_no, operation, jc_warehouse=jc_wh, jc_workstation=jc_workstation,
                    cache=operation_wh_cache, reasons=reasons)
            else:
                target_wh = wo.wip_warehouse or ''

            if operation and not target_wh and reasons:
                frappe.logger().warning(
                    f"Pick List Report: WO {wo.name} item {item.item_code} — no target warehouse "
                    f"for operation '{operation}': " + '; '.join(reasons)
                )

            # Check stock already in target WIP (already transferred)
            already_in_wip = 0.0
            if target_wh:
                already_in_wip = flt(
                    frappe.db.get_value('Bin',
                        {'item_code': item.item_code, 'warehouse': target_wh},
                        'actual_qty'
                    ) or 0
                )

            # Check stock at source
            available = 0.0
            if source_wh:
                available = flt(
                    frappe.db.get_value('Bin',
                        {'item_code': item.item_code, 'warehouse': source_wh},
                        'actual_qty'
                    ) or 0
                )

            # Balance: required - already in WIP
            balance = max(0, required_total - already_in_wip)

            result.append({
                'work_order': wo.name,
                'item_code': item.item_code,
                'item_name': item.item_name,
                'operation': operation,
                'required_per_piece': flt(item.qty),
                'required_total': required_total,
                'source_warehouse': source_wh,
                'target_warehouse': target_wh,
                'available_qty': available,
                'balance_to_transfer': balance,
                'wip_warehouse': target_wh
            })

    # Sort by warehouse then item
    result.sort(key=lambda x: (x.get('source_warehouse', ''),
                                x.get('item_code', ''),
                                x.get('work_order', '')))

    frappe.logger().info(f"Pick List Report: Returning {len(result)} rows")

    return result


def get_summary(data):
    """Generate summary message"""
    unique_wo = len(set(d.get('work_order') for d in data))
    unique_items = len(set(d.get('item_code') for d in data))
    total_qty = sum(d.get('balance_to_transfer', 0) for d in data)

    warehouses = set(d.get('source_warehouse', '') for d in data)
    wh_list = ', '.join(sorted(warehouses)) if warehouses else 'N/A'

    return f"""
    <div style="margin:15px 0;">
        <b>Summary:</b> {unique_wo} Work Orders |
        {unique_items} Items |
        {total_qty:.1f} total qty to transfer<br>
        <b>From:</b> {wh_list}
    </div>
    """
