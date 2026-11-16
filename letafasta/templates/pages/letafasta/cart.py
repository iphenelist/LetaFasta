import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/cart"
        raise frappe.Redirect
    context.hubs = frappe.get_all("LF Hub", filters={"is_active": 1},
                                  fields=["name", "hub_name", "region"],
                                  order_by="hub_name asc")
    context.no_cache = 1
