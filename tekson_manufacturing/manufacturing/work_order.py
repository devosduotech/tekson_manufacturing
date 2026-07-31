import frappe

from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry


@frappe.whitelist()
def complete_work_order(work_order):

    # --------------------------------------------------------
    # Load Work Order
    # --------------------------------------------------------

    wo = frappe.get_doc("Work Order", work_order)

    if wo.docstatus != 1:
        return

    wo.reload()

    # --------------------------------------------------------
    # Already completed
    # --------------------------------------------------------

    if wo.status == "Completed":
        return "Already Completed"

    # --------------------------------------------------------
    # Duplicate Manufacture Stock Entry Protection
    # --------------------------------------------------------

    existing = frappe.db.exists(
        "Stock Entry",
        {
            "work_order": work_order,
            "purpose": "Manufacture",
            "docstatus": 1,
        },
    )

    if existing:
        wo.reload()

        if wo.status != "Completed":
            try:
                wo.update_work_order_qty()
                wo.set_status()
                wo.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                pass

        return existing

    # --------------------------------------------------------
    # Verify ALL Operations are Completed
    # --------------------------------------------------------

    pending = []

    wo.reload()

    for op in wo.operations:

        if op.status != "Completed":
            pending.append(op.operation)

    if pending:
        return

    # --------------------------------------------------------
    # Manufacture Stock Entry
    # --------------------------------------------------------

    se_dict = make_stock_entry(
        work_order_id=work_order,
        purpose="Manufacture",
    )

    stock_entry = frappe.get_doc(se_dict)

    stock_entry.insert(ignore_permissions=True)

    stock_entry.submit()

    # --------------------------------------------------------
    # Reload WO
    # --------------------------------------------------------

    wo.reload()

    # ERPNext normally updates Produced Qty during SE submit.
    # Just ensure status is refreshed.

    try:
        wo.update_work_order_qty()
    except Exception:
        pass

    wo.reload()

    if wo.status != "Completed":

        try:
            wo.set_status()
            wo.save(ignore_permissions=True)
        except Exception:
            pass

    frappe.db.commit()

    return stock_entry.name
