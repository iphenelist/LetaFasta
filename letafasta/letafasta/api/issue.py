"""Issue management: raise and resolve issues on orders/loads."""
import frappe
from frappe import _
from frappe.utils import now_datetime
from letafasta.letafasta.utils import get_supplier_org


def _assert_order_party(order_name):
    if frappe.session.user == "Administrator" or frappe.has_role("LF Admin"):
        return
    buyer = frappe.db.get_value("LF Order", order_name, "buyer")
    if frappe.session.user == buyer:
        return
    supplier = frappe.db.get_value("LF Order", order_name, "supplier")
    org = get_supplier_org()
    if org == supplier:
        return
    frappe.throw(_("Not authorised"), frappe.PermissionError)


@frappe.whitelist()
def raise_issue(order, issue_type, description, load=None):
    _assert_order_party(order)

    order_doc = frappe.get_doc("LF Order", order)
    if order_doc.status in ("completed", "cancelled"):
        frappe.throw(_("Cannot raise an issue on a {0} order.").format(order_doc.status))

    if load:
        load_status = frappe.db.get_value("LF Load", load, "status")
        if load_status in ("collected", "cancelled"):
            frappe.throw(_("Cannot raise an issue on a {0} load.").format(load_status))

    issue = frappe.new_doc("LF Issue")
    issue.order = order
    issue.load = load or None
    issue.type = issue_type
    issue.description = description
    issue.status = "open"
    issue.raised_by = frappe.session.user
    issue.assigned_org = order_doc.supplier
    issue.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"issue": issue.name, "status": issue.status}


@frappe.whitelist()
def resolve_issue(issue_name, resolution_note):
    issue = frappe.get_doc("LF Issue", issue_name)
    _assert_order_party(issue.order)

    if issue.status == "resolved":
        frappe.throw(_("Issue is already resolved."))

    issue.status = "resolved"
    issue.resolution_note = resolution_note
    issue.resolved_at = now_datetime()
    issue.resolved_by = frappe.session.user
    issue.save(ignore_permissions=True)
    frappe.db.commit()
    return {"issue": issue.name, "status": issue.status}


@frappe.whitelist()
def get_issues(order):
    _assert_order_party(order)
    return frappe.get_all(
        "LF Issue",
        filters={"order": order},
        fields=["name", "type", "status", "load", "description",
                "raised_by", "due_at", "resolution_note", "resolved_at"],
        order_by="creation desc",
    )


@frappe.whitelist()
def record_payment(order, amount, method, reference=None, proof=None, payment_date=None, notes=None):
    """Log an off-platform payment against an order."""
    if frappe.session.user == "Administrator" or frappe.has_role("LF Admin"):
        pass
    else:
        buyer = frappe.db.get_value("LF Order", order, "buyer")
        supplier = frappe.db.get_value("LF Order", order, "supplier")
        org = get_supplier_org()
        if frappe.session.user != buyer and org != supplier:
            frappe.throw(_("Not authorised"), frappe.PermissionError)

    from frappe.utils import today
    rec = frappe.new_doc("LF Payment Record")
    rec.order = order
    rec.amount = frappe.utils.flt(amount)
    rec.method = method
    rec.reference = reference
    rec.proof = proof
    rec.payment_date = payment_date or today()
    rec.notes = notes
    rec.recorded_by = frappe.session.user
    rec.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"record": rec.name}


@frappe.whitelist()
def get_payment_records(order):
    buyer = frappe.db.get_value("LF Order", order, "buyer")
    supplier = frappe.db.get_value("LF Order", order, "supplier")
    if frappe.session.user not in (buyer, "Administrator") and not frappe.has_role("LF Admin"):
        org = get_supplier_org()
        if org != supplier:
            frappe.throw(_("Not authorised"), frappe.PermissionError)
    return frappe.get_all(
        "LF Payment Record",
        filters={"order": order},
        fields=["name", "amount", "method", "reference", "payment_date", "recorded_by", "notes"],
        order_by="payment_date desc",
    )
