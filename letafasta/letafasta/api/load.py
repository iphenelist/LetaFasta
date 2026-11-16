"""
Load lifecycle APIs: plan_loads, add_transport_details, update_load_status, confirm_collection.
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, flt, cint


VALID_TRANSITIONS = {
    "planned":  ("booked", "cancelled"),
    "booked":   ("departed", "cancelled"),
    "departed": ("arrived",),
    "arrived":  ("collected",),
}


@frappe.whitelist()
def plan_loads(order_name, loads_json):
    """
    Supplier creates one or more load records for an order.
    loads_json: list of {weight_kg, items:[{order_item, quantity}]} dicts.
    Returns list of created load names.
    """
    import json
    order = frappe.get_doc("LF Order", order_name)
    _assert_supplier(order)

    if order.status not in ("confirmed", "in_progress"):
        frappe.throw(_("Cannot plan loads for an order with status '{0}'.").format(order.status))

    loads_data = json.loads(loads_json) if isinstance(loads_json, str) else loads_json
    if not loads_data:
        frappe.throw(_("No load data provided."))

    total_weight = sum(flt(l.get("weight_kg", 0)) for l in loads_data)
    shares = _allocate_shares(order.agreed_price, [flt(l.get("weight_kg", 0)) for l in loads_data], total_weight)

    created = []
    existing_count = frappe.db.count("LF Load", {"order": order_name})
    for idx, load_data in enumerate(loads_data):
        load = frappe.new_doc("LF Load")
        load.order = order_name
        load.label = "Truck " + chr(65 + existing_count + idx)
        load.status = "planned"
        load.weight_kg = cint(load_data.get("weight_kg", 0))
        load.share_amount = shares[idx]
        for li in load_data.get("items", []):
            load.append("items", {
                "order_item": li.get("order_item"),
                "quantity": cint(li.get("quantity", 0)),
            })
        load.insert(ignore_permissions=True)
        created.append(load.name)

    if order.status == "confirmed":
        frappe.db.set_value("LF Order", order_name, "status", "in_progress")

    frappe.db.commit()
    return created


@frappe.whitelist()
def add_transport_details(load_name, plate_number, driver_name, driver_phone,
                          transport_company_name="", departure_date=None,
                          eta=None, waybill_no=""):
    """Supplier adds truck details to a planned load → moves to booked."""
    load = frappe.get_doc("LF Load", load_name)
    _assert_load_supplier(load)

    if load.status != "planned":
        frappe.throw(_("Load is already {0}.").format(load.status))

    frappe.db.set_value("LF Load", load_name, {
        "plate_number": plate_number,
        "driver_name": driver_name,
        "driver_phone": driver_phone,
        "transport_company_name": transport_company_name,
        "departure_date": departure_date,
        "eta": eta,
        "waybill_no": waybill_no,
        "status": "booked",
    })
    return {"load": load_name, "status": "booked"}


@frappe.whitelist()
def update_load_status(load_name, new_status):
    """
    Supplier advances load status: booked→departed→arrived.
    Buyer/supplier can move arrived→collected (via confirm_collection).
    """
    load = frappe.get_doc("LF Load", load_name)
    allowed_next = VALID_TRANSITIONS.get(load.status, ())

    if new_status not in allowed_next:
        frappe.throw(
            _("Cannot move from '{0}' to '{1}'.").format(load.status, new_status)
        )

    # supplier can advance up to arrived; collected is via confirm_collection
    if new_status == "collected":
        frappe.throw(_("Use confirm_collection to mark a load as collected."))

    # only supplier can advance status
    _assert_load_supplier(load)

    updates = {"status": new_status}
    if new_status == "departed":
        updates["departed_at"] = now_datetime()
    elif new_status == "arrived":
        updates["arrived_at"] = now_datetime()

    frappe.db.set_value("LF Load", load_name, updates)
    _refresh_order_status(load.order)
    return {"load": load_name, "status": new_status}


@frappe.whitelist()
def confirm_collection(load_name):
    """Buyer confirms they collected goods from a truck (arrived → collected)."""
    load = frappe.get_doc("LF Load", load_name)
    order = frappe.get_doc("LF Order", load.order)

    if order.buyer != frappe.session.user and "LF Admin" not in frappe.get_roles():
        frappe.throw(_("Only the buyer can confirm collection."))

    if load.status != "arrived":
        frappe.throw(_("Load must be in 'arrived' status before confirming collection."))

    # check for open issues blocking this load
    open_issues = frappe.db.count("LF Issue", {
        "load": load_name,
        "status": ["in", ["open", "escalated"]],
    })
    if open_issues:
        frappe.throw(_("Cannot confirm collection — {0} open issue(s) on this load.").format(open_issues))

    frappe.db.set_value("LF Load", load_name, {
        "status": "collected",
        "confirmed_at": now_datetime(),
    })

    _refresh_order_status(load.order)
    return {"collected": load_name, "show_rating_prompt": _all_loads_collected(load.order)}


@frappe.whitelist()
def get_order_loads(order_name):
    """Return all loads for an order."""
    order = frappe.get_doc("LF Order", order_name)
    _assert_order_party(order)
    loads = frappe.get_all(
        "LF Load",
        filters={"order": order_name},
        fields=["name", "label", "status", "weight_kg", "share_amount",
                "plate_number", "driver_name", "driver_phone",
                "transport_company_name", "departure_date", "eta",
                "departed_at", "arrived_at", "confirmed_at", "waybill_no"],
        order_by="creation asc",
    )
    return loads


# ── helpers ────────────────────────────────────────────────────────────────

def _allocate_shares(agreed_price, weights, total_weight):
    """Largest-remainder allocation so shares sum exactly to agreed_price."""
    agreed_price = flt(agreed_price)
    if total_weight == 0 or agreed_price == 0:
        return [0.0] * len(weights)

    raw = [(agreed_price * w / total_weight) for w in weights]
    floored = [int(r) for r in raw]
    remainders = [(raw[i] - floored[i], i) for i in range(len(raw))]
    deficit = int(agreed_price) - sum(floored)
    for _, i in sorted(remainders, reverse=True)[:deficit]:
        floored[i] += 1
    return [float(f) for f in floored]


def _refresh_order_status(order_name):
    """Recalculate and update the order's status based on its loads."""
    loads = frappe.get_all("LF Load", filters={"order": order_name}, pluck="status")
    active = [s for s in loads if s not in ("cancelled",)]

    if not active:
        return
    if all(s == "collected" for s in active):
        frappe.db.set_value("LF Order", order_name, "status", "completed")
    elif any(s == "collected" for s in active):
        frappe.db.set_value("LF Order", order_name, "status", "partly_collected")
    elif any(s in ("departed", "arrived") for s in active):
        frappe.db.set_value("LF Order", order_name, "status", "in_progress")


def _all_loads_collected(order_name):
    loads = frappe.get_all("LF Load", filters={"order": order_name}, pluck="status")
    active = [s for s in loads if s != "cancelled"]
    return bool(active) and all(s == "collected" for s in active)


def _assert_supplier(order):
    if not frappe.db.exists("LF Organization Member",
                            {"user": frappe.session.user, "parent": order.supplier}):
        if "LF Admin" not in frappe.get_roles():
            frappe.throw(_("Only the supplier can manage loads for this order."))


def _assert_load_supplier(load):
    order_supplier = frappe.db.get_value("LF Order", load.order, "supplier")
    if not frappe.db.exists("LF Organization Member",
                            {"user": frappe.session.user, "parent": order_supplier}):
        if "LF Admin" not in frappe.get_roles():
            frappe.throw(_("Not authorised."))


def _assert_order_party(order):
    roles = frappe.get_roles()
    is_buyer = order.buyer == frappe.session.user
    is_supplier = frappe.db.exists(
        "LF Organization Member",
        {"user": frappe.session.user, "parent": order.supplier},
    )
    if not (is_buyer or is_supplier or "LF Admin" in roles):
        frappe.throw(_("Not authorised."))
