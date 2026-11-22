"""In-app message thread for LF Order and LF RFQ."""
import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.query_builder import DocType


def _assert_party(reference_type, reference_name):
    """Raise PermissionError if the session user is not buyer, supplier, or admin."""
    if frappe.session.user == "Administrator":
        return
    if frappe.has_role("LF Admin"):
        return

    if reference_type == "LF Order":
        buyer, supplier = frappe.db.get_value("LF Order", reference_name, ["buyer", "supplier"])
        members = frappe.get_all(
            "LF Organization Member",
            filters={"parent": supplier, "user": frappe.session.user},
            fields=["name"],
        )
        if frappe.session.user != buyer and not members:
            frappe.throw(_("Not authorised"), frappe.PermissionError)
    elif reference_type == "LF RFQ":
        buyer = frappe.db.get_value("LF RFQ", reference_name, "buyer")
        if frappe.session.user != buyer and not frappe.has_role(["LF Supplier Owner", "LF Supplier Staff"]):
            frappe.throw(_("Not authorised"), frappe.PermissionError)


@frappe.whitelist()
def send_message(reference_type, reference_name, message):
    if not message or not message.strip():
        frappe.throw(_("Message cannot be empty."))
    _assert_party(reference_type, reference_name)
    msg = frappe.new_doc("LF Message")
    msg.reference_type = reference_type
    msg.reference_name = reference_name
    msg.sender = frappe.session.user
    msg.message = message.strip()
    msg.insert(ignore_permissions=True)
    frappe.db.commit()
    return {
        "name": msg.name,
        "sender": msg.sender,
        "message": msg.message,
        "creation": str(msg.creation),
    }


@frappe.whitelist()
def get_messages(reference_type, reference_name, after=None):
    _assert_party(reference_type, reference_name)
    Message = DocType("LF Message")
    q = (
        frappe.qb.from_(Message)
        .select(
            Message.name,
            Message.sender,
            Message.message,
            Message.creation,
            Message.is_read,
        )
        .where(
            (Message.reference_type == reference_type)
            & (Message.reference_name == reference_name)
        )
        .orderby(Message.creation)
        .limit(100)
    )
    if after:
        q = q.where(Message.creation > after)
    rows = q.run(as_dict=True)

    # Mark unread messages from the other party as read
    unread = [r.name for r in rows if not r.is_read and r.sender != frappe.session.user]
    if unread:
        (
            frappe.qb.update(Message)
            .set(Message.is_read, 1)
            .set(Message.read_at, now_datetime())
            .where(Message.name.isin(unread))
        ).run()
        frappe.db.commit()

    return rows


@frappe.whitelist()
def unread_count(reference_type, reference_name):
    _assert_party(reference_type, reference_name)
    Message = DocType("LF Message")
    result = (
        frappe.qb.from_(Message)
        .select(frappe.query_builder.functions.Count("*").as_("cnt"))
        .where(
            (Message.reference_type == reference_type)
            & (Message.reference_name == reference_name)
            & (Message.is_read == 0)
            & (Message.sender != frappe.session.user)
        )
    ).run(as_dict=True)
    return result[0].cnt if result else 0
