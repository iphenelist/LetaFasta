import frappe
from frappe.utils import now_datetime
from letafasta.letafasta.utils import get_supplier_org


STATUS_COLORS = {
    "confirmed": "info", "in_progress": "primary", "partly_collected": "warning",
    "completed": "success", "cancelled": "danger",
}

LOAD_STATUS_COLORS = {
    "planned": "secondary", "booked": "info", "departed": "warning",
    "arrived": "primary", "collected": "success", "cancelled": "danger",
}


def truck_status_color(status):
    return LOAD_STATUS_COLORS.get(status, "secondary")


def get_context(context):
    order_id = frappe.form_dict.get("name") or frappe.local.path_args.get("name")
    if not order_id:
        frappe.throw("Order not found", frappe.DoesNotExistError)

    if not frappe.db.exists("LF Order", order_id):
        frappe.throw("Order not found", frappe.DoesNotExistError)

    order = frappe.get_doc("LF Order", order_id)

    roles = frappe.get_roles()
    is_admin = "LF Admin" in roles

    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = f"/login?redirect-to=/letafasta/order/{order_id}"
        raise frappe.Redirect

    is_buyer = frappe.session.user == order.buyer
    supplier_org = get_supplier_org()
    is_supplier = supplier_org == order.supplier

    if not (is_buyer or is_supplier or is_admin):
        frappe.throw("Not authorised", frappe.PermissionError)

    # Enrich order with display names
    org_data = frappe.db.get_value(
        "LF Organization", order.supplier,
        ["org_name", "avg_rating", "is_verified"], as_dict=True,
    ) or {}
    hub_data = frappe.db.get_value(
        "LF Hub", order.hub, ["hub_name", "region"], as_dict=True
    ) or {}

    order.supplier_name = org_data.get("org_name") or order.supplier
    order.hub_name = hub_data.get("hub_name") or order.hub

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
        is_buyer
        and bool(active_loads)
        and all(l.status == "collected" for l in active_loads)
        and not frappe.db.exists("LF Rating", {"order": order_id})
    )

    issues = frappe.get_all(
        "LF Issue",
        filters={"order": order_id},
        fields=["name", "type", "status", "load", "description",
                "raised_by", "due_at", "resolution_note", "resolved_at"],
        order_by="creation desc",
    )
    open_issues = [i for i in issues if i.status in ("open", "escalated")]

    context.order = order
    context.loads = loads
    context.order_items = order_items
    context.is_buyer = is_buyer
    context.is_supplier = is_supplier
    context.is_admin = is_admin
    context.show_rating_prompt = show_rating_prompt
    context.issues = issues
    context.open_issues = open_issues
    context.status_color = STATUS_COLORS.get(order.status, "secondary")
    context.truck_status_color = truck_status_color
    context.no_cache = 1
