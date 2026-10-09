__version__ = "15.1.29"

# Apply monkey patches for Frappe framework bugs
from tekson_manufacturing.patches import fix_getdoctype_bug  # noqa: F401
