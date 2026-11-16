import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    supplier_row = frappe.db.sql("""
        SELECT parent FROM `tabLF Organization Member`
        WHERE user = %s AND parenttype = 'LF Organization' LIMIT 1
    """, (frappe.session.user,), as_dict=True)

    if not supplier_row:
        frappe.local.flags.redirect_location = "/letafasta/onboarding"
        raise frappe.Redirect

    context.products = frappe.get_all(
        "LF Product",
        filters={"supplier": supplier_row[0].parent},
        fields=["name", "product_name", "unit_price", "unit_label",
                "stock_quantity", "is_active"],
        order_by="creation desc",
    )
    context.no_cache = 1
