import frappe
from frappe.query_builder import DocType

from letafasta.letafasta.utils import get_supplier_org


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/supplier"
		raise frappe.Redirect

	supplier_name = get_supplier_org()
	if not supplier_name:
		frappe.local.flags.redirect_location = "/letafasta/onboarding"
		raise frappe.Redirect

	org = frappe.get_doc("LF Organization", supplier_name)

	stats = {
		"active_orders": frappe.db.count("LF Order", {
			"supplier": org.name,
			"status": ["in", ["confirmed", "in_progress", "partly_collected"]],
		}),
		"open_rfqs": frappe.db.count("LF RFQ", {"status": ["in", ["open", "quoted"]]}),
	}

	Order = DocType("LF Order")
	Hub = DocType("LF Hub")
	recent_orders = (
		frappe.qb.from_(Order)
		.inner_join(Hub).on(Hub.name == Order.hub)
		.select(
			Order.name, Order.buyer, Order.status, Order.agreed_price,
			Hub.hub_name,
		)
		.where(Order.supplier == org.name)
		.orderby(Order.creation, order=frappe.qb.desc)
		.limit(10)
	).run(as_dict=True)

	context.org = org
	context.stats = stats
	context.recent_orders = recent_orders
	context.no_cache = 1
