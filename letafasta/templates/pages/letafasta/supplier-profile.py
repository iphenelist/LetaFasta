import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    org_id = frappe.form_dict.get("name") or frappe.local.path_args.get("name")
    if not org_id:
        frappe.throw("Supplier not found", frappe.DoesNotExistError)

    org = frappe.db.get_value(
        "LF Organization", org_id,
        ["name", "org_name", "region", "address", "is_verified",
         "avg_rating", "total_orders_completed", "status"],
        as_dict=True,
    )
    if not org or org.status != "approved":
        frappe.throw("Supplier not found", frappe.DoesNotExistError)

    products = frappe.get_all(
        "LF Product",
        filters={"supplier": org_id, "is_active": 1},
        fields=["name", "product_name", "unit_label", "unit_price",
                "unit_weight_kg", "stock_quantity", "image"],
        order_by="creation desc",
        limit=20,
    )

    ratings = frappe.db.sql("""
        SELECT r.quality_rating, r.punctuality_rating,
               r.communication_rating, r.overall_rating,
               r.comment, r.creation, u.full_name AS buyer_name
        FROM `tabLF Rating` r
        JOIN `tabUser` u ON u.name = r.buyer
        WHERE r.supplier = %s
        ORDER BY r.creation DESC
        LIMIT 10
    """, (org_id,), as_dict=True)

    context.org = org
    context.products = products
    context.ratings = ratings
    context.no_cache = 1
