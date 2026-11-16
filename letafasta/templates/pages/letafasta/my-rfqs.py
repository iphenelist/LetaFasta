import frappe
from frappe.utils import get_datetime


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

    rfqs = frappe.db.sql("""
        SELECT r.name, r.rfq_title, r.quantity, r.unit_label, r.status, r.expires_at,
               r.product, r.product_description,
               p.product_name,
               h.hub_name,
               COUNT(q.name) AS quote_count
        FROM `tabLF RFQ` r
        LEFT JOIN `tabLF Product` p ON p.name = r.product
        LEFT JOIN `tabLF Hub` h ON h.name = r.hub
        LEFT JOIN `tabLF RFQ Quote` q ON q.rfq = r.name AND q.status = 'submitted'
        WHERE r.buyer = %(user)s
        GROUP BY r.name
        ORDER BY r.creation DESC
        LIMIT 50
    """, {"user": frappe.session.user}, as_dict=True)

    context.rfqs = rfqs
    context.lf_status_color = lf_status_color
    context.no_cache = 1
