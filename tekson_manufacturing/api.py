import frappe


@frappe.whitelist()
def get_routing_operations(routing_name):
    """Get operations from a Routing document for child table filtering."""
    if not routing_name:
        return []
    return frappe.get_all(
        "BOM Operation",
        filters={"parenttype": "Routing", "parent": routing_name},
        fields=["operation", "workstation", "time_in_mins"],
        order_by="sequence_id, idx",
    )
