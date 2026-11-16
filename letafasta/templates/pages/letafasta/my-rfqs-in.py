import frappe
from frappe.query_builder import DocType, Case
from frappe.utils import now_datetime

from letafasta.letafasta.utils import get_supplier_org


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/my-rfqs-in"
		raise frappe.Redirect

	supplier_name = get_supplier_org()
	if not supplier_name:
		frappe.local.flags.redirect_location = "/letafasta/onboarding"
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
			(Quote.rfq == Rfq.name)
			& (Quote.supplier == supplier_name)
			& Quote.status.notin(["rejected", "expired"])
		)
		.select(
			Rfq.name, Rfq.rfq_title, Rfq.quantity, Rfq.unit_label, Rfq.expires_at,
			Rfq.budget_per_unit, Rfq.preferred_date,
			Product.product_name,
			Rfq.product_description,
			Hub.hub_name,
			Case().when(Quote.name.isnotnull(), 1).else_(0).as_("already_quoted"),
		)
		.where(
			Rfq.status.isin(["open", "quoted"])
			& (Rfq.expires_at > now_datetime())
		)
		.orderby(Rfq.creation, order=frappe.qb.desc)
		.limit(50)
	).run(as_dict=True)

	context.rfqs = rfqs
	context.no_cache = 1
