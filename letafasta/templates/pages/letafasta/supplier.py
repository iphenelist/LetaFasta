import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/supplier"
        raise frappe.Redirect

    supplier_row = frappe.db.sql("""
        SELECT parent FROM `tabLF Organization Member`
        WHERE user = %s AND parenttype = 'LF Organization' LIMIT 1
    """, (frappe.session.user,), as_dict=True)

    if not supplier_row:
        frappe.local.flags.redirect_location = "/letafasta/onboarding"
        raise frappe.Redirect

    org = frappe.get_doc("LF Organization", supplier_row[0].parent)

    stats = {
        "active_orders": frappe.db.count("LF Order", {
            "supplier": org.name,
            "status": ["in", ["confirmed", "in_progress", "partly_collected"]],
        }),
        "open_rfqs": frappe.db.count("LF RFQ", {"status": ["in", ["open", "quoted"]]}),
    }

    recent_orders = frappe.db.sql("""
        SELECT o.name, o.buyer, o.status, o.agreed_price, h.hub_name
        FROM `tabLF Order` o
        JOIN `tabLF Hub` h ON h.name = o.hub
        WHERE o.supplier = %(supplier)s
        ORDER BY o.creation DESC
        LIMIT 10
    """, {"supplier": org.name}, as_dict=True)

    context.org = org
    context.stats = stats
    context.recent_orders = recent_orders
    context.no_cache = 1
