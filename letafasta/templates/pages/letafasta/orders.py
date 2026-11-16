import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Sum
from frappe.query_builder import Case


STATUS_COLORS = {
	"confirmed": "success", "in_progress": "primary",
	"partly_collected": "warning", "completed": "secondary",
	"cancelled": "danger",
}


def lf_status_color(status):
	return STATUS_COLORS.get(status, "secondary")


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/orders"
		raise frappe.Redirect

	Order = DocType("LF Order")
	Org = DocType("LF Organization")
	Hub = DocType("LF Hub")
	Load = DocType("LF Load")

	orders = (
		frappe.qb.from_(Order)
		.inner_join(Org).on(Org.name == Order.supplier)
		.inner_join(Hub).on(Hub.name == Order.hub)
		.left_join(Load).on(
			(Load.order == Order.name) & (Load.status != "cancelled")
		)
		.select(
			Order.name, Order.status, Order.agreed_price, Order.creation,
			Org.org_name.as_("supplier_name"),
			Hub.hub_name,
			Count(Load.name).as_("load_count"),
			Sum(Case().when(Load.status == "collected", 1).else_(0)).as_("collected_count"),
		)
		.where(Order.buyer == frappe.session.user)
		.groupby(Order.name)
		.orderby(Order.creation, order=frappe.qb.desc)
		.limit(50)
	).run(as_dict=True)

	context.orders = orders
	context.lf_status_color = lf_status_color
	context.no_cache = 1
