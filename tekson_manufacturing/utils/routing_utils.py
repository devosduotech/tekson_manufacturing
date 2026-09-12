import frappe


@frappe.whitelist()
def get_routing_operations(routing_name):
    if not routing_name:
        return []
    doc = frappe.get_doc("Routing", routing_name)
    return [{"operation": op.operation} for op in doc.operations]


@frappe.whitelist()
def get_routing_operations_query(doctype, txt, searchfield, start, page_len, filters):
    routing_name = filters.get("routing_name")
    if not routing_name:
        return []
    doc = frappe.get_doc("Routing", routing_name)
    results = []
    for op in doc.operations:
        if not txt or txt.lower() in op.operation.lower():
            results.append([op.operation])
    return results
