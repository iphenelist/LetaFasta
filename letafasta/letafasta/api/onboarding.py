"""
Onboarding API: register new users as buyers or supplier organisations.
"""
import frappe
from frappe import _


@frappe.whitelist()
def set_buyer_role():
    """Grant LF Buyer role to current user."""
    user = frappe.get_doc("User", frappe.session.user)
    user.add_roles("LF Buyer")
    return {"role": "LF Buyer", "redirect": "/letafasta/catalogue"}


@frappe.whitelist()
def register_supplier(org_name, region, phone_number, tin="", address=""):
    """
    Register current user as a supplier.
    Creates LF Organization (pending) and grants LF Supplier Owner role.
    """
    if not org_name:
        frappe.throw(_("Organisation name is required."))

    if frappe.db.exists("LF Organization", org_name):
        frappe.throw(_("An organisation named '{0}' already exists.").format(org_name))

    org = frappe.new_doc("LF Organization")
    org.org_name = org_name
    org.type = "supplier"
    org.status = "pending"
    org.region = region
    org.phone_number = phone_number
    org.tin = tin
    org.address = address
    org.append("members", {
        "user": frappe.session.user,
        "role": "owner",
    })
    org.insert(ignore_permissions=True)

    user = frappe.get_doc("User", frappe.session.user)
    user.add_roles("LF Supplier Owner")

    frappe.db.commit()
    return {"org": org.name, "status": "pending"}
