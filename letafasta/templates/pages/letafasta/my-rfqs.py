import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count


STATUS_COLORS = {
	"open": "primary", "quoted": "warning", "accepted": "success",
	"expired": "secondary", "cancelled": "danger",
}


def lf_status_color(status):
	return STATUS_COLORS.get(status, "secondary")


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/my-rfqs"
		raise frappe.Redirect

	Rfq = DocType("LF RFQ")
	Product = DocType("LF Product")
	Hub = DocType("LF Hub")
	Quote = DocType("LF RFQ Quote")

	rfqs = (
		frappe.qb.from_(Rfq)
		.left_join(Product).on(Product.name == Rfq.product)
		.left_join(Hub).on(Hub.name == Rfq.hub)
		.left_join(Quote).on(
			(Quote.rfq == Rfq.name) & (Quote.status == "submitted")
		)
		.select(
			Rfq.name, Rfq.rfq_title, Rfq.quantity, Rfq.unit_label, Rfq.status, Rfq.expires_at,
			Rfq.product, Rfq.product_description,
			Product.product_name,
			Hub.hub_name,
			Count(Quote.name).as_("quote_count"),
		)
		.where(Rfq.buyer == frappe.session.user)
		.groupby(Rfq.name)
		.orderby(Rfq.creation, order=frappe.qb.desc)
		.limit(50)
	).run(as_dict=True)

	context.rfqs = rfqs
	context.lf_status_color = lf_status_color
	context.no_cache = 1
