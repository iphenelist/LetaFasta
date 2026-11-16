import frappe
from frappe.query_builder import DocType


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/catalogue"
		raise frappe.Redirect

	Product = DocType("LF Product")
	Org = DocType("LF Organization")
	context.products = (
		frappe.qb.from_(Product)
		.inner_join(Org).on(Org.name == Product.supplier)
		.select(
			Product.name, Product.product_name, Product.unit_label, Product.unit_price,
			Product.unit_weight_kg, Product.stock_quantity, Product.image,
			Org.name.as_("supplier_id"), Org.org_name.as_("supplier"),
			Org.is_verified, Org.avg_rating,
		)
		.where((Product.is_active == 1) & (Org.status == "approved"))
		.orderby(Org.is_verified, order=frappe.qb.desc)
		.orderby(Org.avg_rating, order=frappe.qb.desc)
		.orderby(Product.creation, order=frappe.qb.desc)
		.limit(100)
	).run(as_dict=True)
	context.no_cache = 1
