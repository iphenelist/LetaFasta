"""
Rating API: buyer submits a rating after all loads are collected.
"""
import frappe
from frappe import _


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
    ratings = frappe.db.sql("""
        SELECT r.name, r.quality_rating, r.punctuality_rating,
               r.communication_rating, r.overall_rating, r.comment,
               r.creation, u.full_name AS buyer_name
        FROM `tabLF Rating` r
        JOIN `tabUser` u ON u.name = r.buyer
        WHERE r.supplier = %s
        ORDER BY r.creation DESC
        LIMIT %s
    """, (supplier, int(limit)), as_dict=True)
    return ratings
