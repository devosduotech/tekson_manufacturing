app_name = "tekson_manufacturing"
app_title = "Tekson Manufacturing"
app_publisher = "OSDuo Tech LLP"
app_description = "Teksons Manufacturing Enhancements"
app_email = "developer@osduotech.com"
app_license = "mit"

doc_events = {
    "Job Card": {
        "before_insert": [
            "tekson_manufacturing.utils.job_card_utils.populate_job_card_fields",
            "tekson_manufacturing.utils.job_card_utils.allocate_workstation",
        ],
        "before_save": [
            "tekson_manufacturing.utils.job_card_utils.validate_job_card_start",
        ],
        "validate": [
            "tekson_manufacturing.utils.job_card_utils.set_wip_warehouse",
            "tekson_manufacturing.utils.job_card_utils.update_job_card_status",
        ],
        "on_submit": "tekson_manufacturing.mes.mes_coordinator.on_job_card_complete",
        "on_cancel": "tekson_manufacturing.execution.execution_engine.on_job_card_cancel",
    },
    "Work Order": {
        "before_insert": "tekson_manufacturing.services.work_order_service.set_warehouses",
        "validate": "tekson_manufacturing.services.work_order_service.set_warehouses",
        "before_save": "tekson_manufacturing.services.work_order_service.round_production_qty",
        "before_submit": "tekson_manufacturing.services.work_order_service.round_production_qty",
        "on_submit": "tekson_manufacturing.mes.mes_coordinator.on_work_order_submit",
    },
    "Stock Entry": {
        "on_submit": "tekson_manufacturing.mes.mes_coordinator.on_stock_entry_submit",
        "on_cancel": "tekson_manufacturing.execution.execution_engine.on_stock_entry_cancel",
    }
}

override_doctype_class = {
    "Work Order": "tekson_manufacturing.overrides.work_order.TeksonWorkOrder"
}

app_include_js = [
    "/assets/tekson_manufacturing/js/job_card_list.js",
    "/assets/tekson_manufacturing/js/material_transfer_pick_list.js"
]

# Reports
# ------------------
report = [
    "tekson_manufacturing.reports.material_transfer_pick_list.material_transfer_pick_list.execute"
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "tekson_manufacturing",
# 		"logo": "/assets/tekson_manufacturing/logo.png",
# 		"title": "Tekson Manufacturing",
# 		"route": "/tekson_manufacturing",
# 		"has_permission": "tekson_manufacturing.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tekson_manufacturing/css/tekson_manufacturing.css"
# app_include_js = "/assets/tekson_manufacturing/js/tekson_manufacturing.js"

# include js, css files in header of web template
# web_include_css = "/assets/tekson_manufacturing/css/tekson_manufacturing.css"
# web_include_js = "/assets/tekson_manufacturing/js/tekson_manufacturing.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tekson_manufacturing/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "tekson_manufacturing/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "tekson_manufacturing.utils.jinja_methods",
# 	"filters": "tekson_manufacturing.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tekson_manufacturing.install.before_install"
# after_install = "tekson_manufacturing.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "tekson_manufacturing.uninstall.before_uninstall"
# after_uninstall = "tekson_manufacturing.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "tekson_manufacturing.utils.before_app_install"
# after_app_install = "tekson_manufacturing.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "tekson_manufacturing.utils.before_app_uninstall"
# after_app_uninstall = "tekson_manufacturing.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tekson_manufacturing.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"tekson_manufacturing.tasks.all"
# 	],
# 	"daily": [
# 		"tekson_manufacturing.tasks.daily"
# 	],
# 	"hourly": [
# 		"tekson_manufacturing.tasks.hourly"
# 	],
# 	"weekly": [
# 		"tekson_manufacturing.tasks.weekly"
# 	],
# 	"monthly": [
# 		"tekson_manufacturing.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "tekson_manufacturing.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "tekson_manufacturing.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "tekson_manufacturing.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["tekson_manufacturing.utils.before_request"]
# after_request = ["tekson_manufacturing.utils.after_request"]

# Job Events
# ----------
# before_job = ["tekson_manufacturing.utils.before_job"]
# after_job = ["tekson_manufacturing.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"tekson_manufacturing.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

