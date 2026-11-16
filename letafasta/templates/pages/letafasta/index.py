import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta"
        raise frappe.Redirect

    roles = frappe.get_roles()
    if "LF Admin" in roles:
        frappe.local.flags.redirect_location = "/app/letafasta-admin"
    elif "LF Supplier Owner" in roles or "LF Supplier Staff" in roles:
        frappe.local.flags.redirect_location = "/letafasta/supplier"
    elif "LF Buyer" in roles:
        frappe.local.flags.redirect_location = "/letafasta/catalogue"
    else:
        frappe.local.flags.redirect_location = "/letafasta/onboarding"
    raise frappe.Redirect
