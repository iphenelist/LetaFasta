import frappe


STATUS_COLORS = {
    "confirmed": "success", "in_progress": "primary",
    "partly_collected": "warning", "completed": "secondary",
    "cancelled": "danger",
}

TRUCK_COLORS = {
    "planned": "secondary", "booked": "info", "departed": "warning",
    "arrived": "primary", "collected": "success", "cancelled": "danger",
}


def lf_status_color(status):
    return STATUS_COLORS.get(status, "secondary")


def truck_status_color(status):
    return TRUCK_COLORS.get(status, "secondary")


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    order_id = frappe.form_dict.get("name") or frappe.local.path_args.get("name")
    if not order_id:
        frappe.throw("Order not found", frappe.DoesNotExistError)

    order = frappe.get_doc("LF Order", order_id)
    order_data = order.as_dict()
    order_data["supplier_name"] = frappe.db.get_value("LF Organization", order.supplier, "org_name")
    order_data["hub_name"] = frappe.db.get_value("LF Hub", order.hub, "hub_name")

    is_buyer = (order.buyer == frappe.session.user)
    supplier_member = frappe.db.exists(
        "LF Organization Member",
        {"user": frappe.session.user, "parent": order.supplier},
    )
    is_supplier = bool(supplier_member)

    if not (is_buyer or is_supplier or "LF Admin" in frappe.get_roles()):
        frappe.throw("Not authorised", frappe.PermissionError)

    loads = frappe.get_all(
        "LF Load",
        filters={"order": order_id},
        fields=["name", "label", "status", "weight_kg", "share_amount",
                "plate_number", "driver_name", "driver_phone",
                "transport_company_name", "departure_date", "eta",
                "departed_at", "arrived_at", "confirmed_at", "waybill_no"],
        order_by="creation asc",
    )

    order_items = frappe.get_all(
        "LF Order Item",
        filters={"parent": order_id},
        fields=["product", "product_name", "quantity", "unit_label", "unit_price", "line_total"],
    )

    active_loads = [l for l in loads if l.status != "cancelled"]
    show_rating_prompt = (
        is_buyer and
        bool(active_loads) and
        all(l.status == "collected" for l in active_loads) and
        not frappe.db.exists("LF Rating", {"order": order_id})
    )

    context.order = order_data
    context.loads = loads
    context.order_items = order_items
    context.is_buyer = is_buyer
    context.is_supplier = is_supplier
    context.show_rating_prompt = show_rating_prompt
    context.status_color = STATUS_COLORS.get(order.status, "secondary")
    context.truck_status_color = truck_status_color
    context.no_cache = 1
