import frappe

@frappe.whitelist()
def get_manufacturing_settings():
    """Get Manufacturing Settings as a dictionary"""
    return frappe.single_doc("Manufacturing Settings")


@frappe.whitelist()
def is_auto_complete_wo_enabled():
    """Check if auto work order completion is enabled"""
    settings = frappe.single_doc("Manufacturing Settings")
    return settings.auto_complete_work_order


@frappe.whitelist()
def is_material_readiness_enabled():
    """Check if material readiness validation is enabled"""
    settings = frappe.single_doc("Manufacturing Settings")
    return settings.enable_material_readiness


@frappe.whitelist()
def is_previous_operation_validation_enabled():
    """Check if previous operation validation is enabled"""
    settings = frappe.single_doc("Manufacturing Settings")
    return settings.enable_previous_operation_validation


@frappe.whitelist()
def is_diagnostics_enabled():
    """Check if diagnostics are enabled"""
    settings = frappe.single_doc("Manufacturing Settings")
    return settings.enable_diagnostics


@frappe.whitelist()
def is_strict_material_validation_enabled():
    """Check if strict material validation is enabled"""
    settings = frappe.single_doc("Manufacturing Settings")
    return settings.strict_material_validation
