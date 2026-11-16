import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/catalogue"
        raise frappe.Redirect

    context.products = frappe.db.sql("""
        SELECT p.name, p.product_name, p.unit_label, p.unit_price,
               p.unit_weight_kg, p.stock_quantity, p.image,
               o.name AS supplier_id, o.org_name AS supplier, o.is_verified, o.avg_rating
        FROM `tabLF Product` p
        JOIN `tabLF Organization` o ON o.name = p.supplier
        WHERE p.is_active = 1
          AND o.status = 'approved'
        ORDER BY o.is_verified DESC, o.avg_rating DESC, p.creation DESC
        LIMIT 100
    """, as_dict=True)
    context.no_cache = 1
