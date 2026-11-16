"""
Rating API: buyer submits a rating after all loads are collected.
"""
import frappe
from frappe import _
from frappe.query_builder import DocType


@frappe.whitelist()
def submit_rating(order, quality_rating, punctuality_rating, communication_rating, comment=""):
	"""Submit a supplier rating for a completed order."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required."), frappe.AuthenticationError)

	order_doc = frappe.get_doc("LF Order", order)

	if order_doc.buyer != frappe.session.user:
		frappe.throw(_("Only the buyer can rate this order."), frappe.PermissionError)

	if order_doc.status != "completed":
		frappe.throw(_("Order must be completed before rating."))

	if frappe.db.exists("LF Rating", {"order": order}):
		frappe.throw(_("You have already rated this order."))

	rating = frappe.new_doc("LF Rating")
	rating.order = order
	rating.buyer = frappe.session.user
	rating.supplier = order_doc.supplier
	rating.quality_rating = int(quality_rating)
	rating.punctuality_rating = int(punctuality_rating)
	rating.communication_rating = int(communication_rating)
	rating.comment = comment
	rating.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"rating": rating.name,
		"overall_rating": rating.overall_rating,
		"redirect": f"/letafasta/order/{order}",
	}


@frappe.whitelist()
def get_supplier_ratings(supplier, limit=10):
	"""Return recent ratings for a supplier organisation."""
	Rating = DocType("LF Rating")
	User = DocType("User")
	return (
		frappe.qb.from_(Rating)
		.inner_join(User).on(User.name == Rating.buyer)
		.select(
			Rating.name, Rating.quality_rating, Rating.punctuality_rating,
			Rating.communication_rating, Rating.overall_rating,
			Rating.comment, Rating.creation,
			User.full_name.as_("buyer_name"),
		)
		.where(Rating.supplier == supplier)
		.orderby(Rating.creation, order=frappe.qb.desc)
		.limit(int(limit))
	).run(as_dict=True)
