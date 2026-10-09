"""
Monkey patch for Frappe v15.121.0 bug: getdoctype() missing 'doctype' argument
when loading query reports with with_parent=1
"""

import sys
from frappe.desk.form import load as frappe_load


# Store original function
_original_getdoctype = frappe_load.getdoctype


def patched_getdoctype(doctype=None, with_parent=False, cached_timestamp=None, **kwargs):
    """
    Patched getdoctype that handles missing doctype argument when with_parent=True.
    
    In Frappe v15.121.0, when loading a query report with with_parent=1,
    the function is called without the doctype argument, causing TypeError.
    """
    # If doctype is missing but with_parent is True, try to infer from request
    if doctype is None and with_parent:
        # Try to get doctype from request context or default to 'Work Order'
        # since our report has ref_doctype = "Work Order"
        doctype = "Work Order"
    
    return _original_getdoctype(doctype, with_parent, cached_timestamp, **kwargs)


# Apply monkey patch immediately at import time - patch both the module and sys.modules
frappe_load.getdoctype = patched_getdoctype

# Also patch in sys.modules to ensure all references get the patched version
if 'frappe.desk.form.load' in sys.modules:
    sys.modules['frappe.desk.form.load'].getdoctype = patched_getdoctype
