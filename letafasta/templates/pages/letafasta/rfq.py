import frappe


STATUS_COLORS = {
    "open": "primary", "quoted": "warning", "accepted": "success",
    "expired": "secondary", "cancelled": "danger",
}


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    rfq_id = frappe.form_dict.get("name") or frappe.local.path_args.get("name")
    if not rfq_id:
        frappe.throw("RFQ not found", frappe.DoesNotExistError)

    rfq = frappe.get_doc("LF RFQ", rfq_id)

    # Enrich with hub name and product name
    rfq_data = rfq.as_dict()
    rfq_data["hub_name"] = frappe.db.get_value("LF Hub", rfq.hub, "hub_name") if rfq.hub else ""
    rfq_data["product_name"] = frappe.db.get_value("LF Product", rfq.product, "product_name") if rfq.product else ""

    is_buyer = (rfq.buyer == frappe.session.user)

    supplier_org = None
    is_supplier = False
    can_quote = False
    already_quoted = False

    if not is_buyer:
        org = frappe.db.sql("""
            SELECT parent FROM `tabLF Organization Member`
            WHERE user = %s AND parenttype = 'LF Organization' LIMIT 1
        """, (frappe.session.user,), as_dict=True)
        if org:
            supplier_org = org[0].parent
            is_supplier = True
            can_quote = rfq.status in ("open", "quoted")
            already_quoted = bool(frappe.db.exists("LF RFQ Quote", {
                "rfq": rfq_id,
                "supplier": supplier_org,
                "status": ["not in", ["rejected", "expired"]],
            }))
            if already_quoted:
                can_quote = False

    quotes = frappe.get_all(
        "LF RFQ Quote",
        filters={"rfq": rfq_id},
        fields=["name", "supplier", "price_per_unit", "total_price",
                "delivery_lead_days", "terms", "status", "valid_until"],
        order_by="price_per_unit asc",
    )

    context.rfq = rfq_data
    context.quotes = quotes
    context.is_buyer = is_buyer
    context.is_supplier = is_supplier
    context.can_quote = can_quote
    context.already_quoted = already_quoted
    context.status_color = STATUS_COLORS.get(rfq.status, "secondary")
    context.no_cache = 1
