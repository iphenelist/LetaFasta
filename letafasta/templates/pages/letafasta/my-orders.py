import frappe


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

    supplier_row = frappe.db.sql("""
        SELECT parent FROM `tabLF Organization Member`
        WHERE user = %s AND parenttype = 'LF Organization' LIMIT 1
    """, (frappe.session.user,), as_dict=True)

    if not supplier_row:
        frappe.local.flags.redirect_location = "/letafasta/onboarding"
        raise frappe.Redirect

    supplier_name = supplier_row[0].parent

    orders = frappe.db.sql("""
        SELECT o.name, o.buyer, o.status, o.agreed_price, o.creation,
               h.hub_name,
               COUNT(l.name) AS load_count,
               SUM(CASE WHEN l.status IN ('booked','departed','arrived') THEN 1 ELSE 0 END) AS booked_count
        FROM `tabLF Order` o
        JOIN `tabLF Hub` h ON h.name = o.hub
        LEFT JOIN `tabLF Load` l ON l.order = o.name AND l.status != 'cancelled'
        WHERE o.supplier = %(supplier)s
        GROUP BY o.name
        ORDER BY
          FIELD(o.status,'confirmed','in_progress','partly_collected','completed','cancelled'),
          o.creation DESC
        LIMIT 50
    """, {"supplier": supplier_name}, as_dict=True)

    context.orders = orders
    context.lf_status_color = lf_status_color
    context.no_cache = 1
