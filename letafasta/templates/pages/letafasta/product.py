import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    product_id = frappe.form_dict.get("name") or frappe.local.path_args.get("name")
    if not product_id:
        frappe.throw("Product not found", frappe.DoesNotExistError)

    product = frappe.get_doc("LF Product", product_id)
    if not product.is_active:
        frappe.throw("Product not found", frappe.DoesNotExistError)

    supplier = frappe.get_doc("LF Organization", product.supplier)

    context.product = product
    context.supplier = supplier
    context.no_cache = 1
