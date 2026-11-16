import frappe
from frappe.query_builder import DocType


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect

	org_id = frappe.form_dict.get("name") or frappe.local.path_args.get("name")
	if not org_id:
		frappe.throw("Supplier not found", frappe.DoesNotExistError)

	org = frappe.db.get_value(
		"LF Organization", org_id,
		["name", "org_name", "region", "address", "is_verified",
		 "avg_rating", "total_orders_completed", "status"],
		as_dict=True,
	)
	if not org or org.status != "approved":
		frappe.throw("Supplier not found", frappe.DoesNotExistError)

	products = frappe.get_all(
		"LF Product",
		filters={"supplier": org_id, "is_active": 1},
		fields=["name", "product_name", "unit_label", "unit_price",
		        "unit_weight_kg", "stock_quantity", "image"],
		order_by="creation desc",
		limit=20,
	)

	Rating = DocType("LF Rating")
	User = DocType("User")
	ratings = (
		frappe.qb.from_(Rating)
		.inner_join(User).on(User.name == Rating.buyer)
		.select(
			Rating.quality_rating, Rating.punctuality_rating,
			Rating.communication_rating, Rating.overall_rating,
			Rating.comment, Rating.creation,
			User.full_name.as_("buyer_name"),
		)
		.where(Rating.supplier == org_id)
		.orderby(Rating.creation, order=frappe.qb.desc)
		.limit(10)
	).run(as_dict=True)

	context.org = org
	context.products = products
	context.ratings = ratings
	context.no_cache = 1
