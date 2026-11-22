import frappe


def get_context(context):
	# No login required — driver accesses via token URL
	load_name = frappe.form_dict.get("load") or frappe.local.path_args.get("load")
	token = frappe.form_dict.get("t")

	if not load_name or not token:
		frappe.throw("Invalid driver link", frappe.DoesNotExistError)

	stored_token = frappe.db.get_value("LF Load", load_name, "driver_token")
	if not stored_token or stored_token != token:
		frappe.throw("Invalid or expired driver link", frappe.PermissionError)

	load = frappe.get_doc("LF Load", load_name)
	so = frappe.get_doc("Sales Order", load.order) if load.order else None

	if load.status in ("collected", "cancelled"):
		context.delivery_done = True

	context.load = load
	context.so = so
	context.token = token
	context.no_cache = 1
