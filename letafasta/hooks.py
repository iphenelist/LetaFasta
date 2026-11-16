app_name = "letafasta"
app_title = "LetaFasta"
app_publisher = "Innocent P M"
app_description = "B2B bulk-materials procurement and last-mile freight marketplace for Tanzania"
app_email = "innocentphenelist@gmail.com"
app_license = "mit"

app_logo_url = "/assets/letafasta/images/letafasta-logo.svg"

# No "route": a bare /desk/<module> is not a valid v16 page; the client
# falls through to the Dock's first Sidebar entry instead.
add_to_apps_screen = [
    {
        "name": "letafasta",
        "logo": app_logo_url,
        "title": "LetaFasta",
    }
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "letafasta",
# 		"logo": "/assets/letafasta/logo.png",
# 		"title": "LetaFasta",
# 		"route": "/letafasta",
# 		"has_permission": "letafasta.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/letafasta/css/letafasta.css"
# app_include_js = "/assets/letafasta/js/letafasta.js"

# include js, css files in header of web template
# web_include_css = "/assets/letafasta/css/letafasta.css"
# web_include_js = "/assets/letafasta/js/letafasta.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "letafasta/public/scss/website"

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
# app_include_icons = "letafasta/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
role_home_page = {
    "LF Admin": "app/letafasta-admin",
    "LF Buyer": "letafasta/orders",
    "LF Supplier Owner": "letafasta/supplier",
    "LF Supplier Staff": "letafasta/my-orders",
}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Fixtures — exported documents synced by migrate / bench import-fixtures
# Workspace omitted: created via Python console; fixture import fails on 'type' mandatory field.
fixtures = [
    {"dt": "Workflow", "filters": [["document_type", "in", ["LF Organization"]]]},
]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "letafasta.utils.jinja_methods",
# 	"filters": "letafasta.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "letafasta.install.before_install"
# after_install = "letafasta.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "letafasta.uninstall.before_uninstall"
# after_uninstall = "letafasta.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "letafasta.utils.before_app_install"
# after_app_install = "letafasta.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "letafasta.utils.before_app_uninstall"
# after_app_uninstall = "letafasta.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "letafasta.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "letafasta.notifications.get_notification_config"

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

scheduler_events = {
    # SMS queue — flush every minute
    "cron": {
        "* * * * *": ["letafasta.letafasta.tasks.flush_sms_queue"],
    },
    # Business logic — expire orders/RFQs, auto-confirm, escalate issues
    "all": [
        "letafasta.letafasta.tasks.run_scheduled_jobs",
    ],
}

# scheduler_events = {
# 	"all": [
# 		"letafasta.tasks.all"
# 	],
# 	"daily": [
# 		"letafasta.tasks.daily"
# 	],
# 	"hourly": [
# 		"letafasta.tasks.hourly"
# 	],
# 	"weekly": [
# 		"letafasta.tasks.weekly"
# 	],
# 	"monthly": [
# 		"letafasta.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "letafasta.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "letafasta.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "letafasta.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "letafasta.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["letafasta.utils.before_request"]
# after_request = ["letafasta.utils.after_request"]

# Job Events
# ----------
# before_job = ["letafasta.utils.before_job"]
# after_job = ["letafasta.utils.after_job"]

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
# 	"letafasta.auth.validate"
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

