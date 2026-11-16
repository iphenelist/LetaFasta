import frappe

from letafasta.letafasta.utils import get_supplier_org


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect

	supplier_name = get_supplier_org()
	if not supplier_name:
		frappe.local.flags.redirect_location = "/letafasta/onboarding"
		raise frappe.Redirect

	context.products = frappe.get_all(
		"LF Product",
		filters={"supplier": supplier_name},
		fields=["name", "product_name", "unit_price", "unit_label",
		        "stock_quantity", "is_active"],
		order_by="creation desc",
	)
	context.no_cache = 1
