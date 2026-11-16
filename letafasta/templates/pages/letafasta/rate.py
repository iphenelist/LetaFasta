import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    order_id = frappe.form_dict.get("name") or frappe.local.path_args.get("name")
    if not order_id:
        frappe.throw("Order not specified", frappe.DoesNotExistError)

    order = frappe.get_doc("LF Order", order_id)

    if order.buyer != frappe.session.user:
        frappe.throw("Not authorised", frappe.PermissionError)

    if order.status != "completed":
        frappe.local.flags.redirect_location = f"/letafasta/order/{order_id}"
        raise frappe.Redirect

    if frappe.db.exists("LF Rating", {"order": order_id}):
        frappe.local.flags.redirect_location = f"/letafasta/order/{order_id}"
        raise frappe.Redirect

    supplier = frappe.db.get_value(
        "LF Organization", order.supplier,
        ["org_name", "avg_rating", "is_verified"], as_dict=True,
    )

    context.order = order
    context.supplier = supplier
    context.no_cache = 1
