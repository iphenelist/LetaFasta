import frappe
from frappe.query_builder import DocType, Case
from frappe.query_builder.functions import Count, Sum

from letafasta.letafasta.utils import get_supplier_org


STATUS_COLORS = {
	"confirmed": "success", "in_progress": "primary",
	"partly_collected": "warning", "completed": "secondary",
	"cancelled": "danger",
}


def lf_status_color(status):
	return STATUS_COLORS.get(status, "secondary")


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/my-orders"
		raise frappe.Redirect

	supplier_name = get_supplier_org()
	if not supplier_name:
		frappe.local.flags.redirect_location = "/letafasta/onboarding"
		raise frappe.Redirect

	Order = DocType("LF Order")
	Hub = DocType("LF Hub")
	Load = DocType("LF Load")

	# FIELD(status, ...) ordering expressed as a Case rank
	status_rank = (
		Case()
		.when(Order.status == "confirmed", 1)
		.when(Order.status == "in_progress", 2)
		.when(Order.status == "partly_collected", 3)
		.when(Order.status == "completed", 4)
		.when(Order.status == "cancelled", 5)
		.else_(6)
	)

	orders = (
		frappe.qb.from_(Order)
		.inner_join(Hub).on(Hub.name == Order.hub)
		.left_join(Load).on(
			(Load.order == Order.name) & (Load.status != "cancelled")
		)
		.select(
			Order.name, Order.buyer, Order.status, Order.agreed_price, Order.creation,
			Hub.hub_name,
			Count(Load.name).as_("load_count"),
			Sum(Case().when(Load.status.isin(["booked", "departed", "arrived"]), 1).else_(0)).as_("booked_count"),
		)
		.where(Order.supplier == supplier_name)
		.groupby(Order.name)
		.orderby(status_rank)
		.orderby(Order.creation, order=frappe.qb.desc)
		.limit(50)
	).run(as_dict=True)

	context.orders = orders
	context.lf_status_color = lf_status_color
	context.no_cache = 1
