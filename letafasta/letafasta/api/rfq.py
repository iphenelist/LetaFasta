"""
RFQ lifecycle APIs: post_rfq, submit_quote, accept_quote, cancel_rfq.
All methods are whitelisted for portal/mobile calls.
"""
import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime, cint, flt


@frappe.whitelist()
def post_rfq(product=None, product_description=None, quantity=0, unit_label="",
             hub=None, preferred_date=None, budget_per_unit=0, notes=""):
    """Buyer posts a new RFQ. Returns the new RFQ name."""
    frappe.has_permission("LF RFQ", "create", throw=True)

    quantity = cint(quantity)
    if quantity <= 0:
        frappe.throw(_("Quantity must be greater than zero."))
    if not hub:
        frappe.throw(_("Please select a delivery hub."))
    if not product and not product_description:
        frappe.throw(_("Please select a product or describe what you need."))

    rfq = frappe.new_doc("LF RFQ")
    rfq.buyer = frappe.session.user
    rfq.product = product
    rfq.product_description = product_description
    rfq.quantity = quantity
    rfq.unit_label = unit_label or _get_unit_label(product)
    rfq.hub = hub
    rfq.preferred_date = preferred_date
    rfq.budget_per_unit = flt(budget_per_unit)
    rfq.notes = notes
    rfq.status = "open"
    rfq.expires_at = add_to_date(now_datetime(), hours=24)
    rfq.insert(ignore_permissions=False)
    frappe.db.set_value("LF RFQ", rfq.name, "rfq_title", rfq.name)
    return rfq.name


@frappe.whitelist()
def submit_quote(rfq, price_per_unit, delivery_lead_days=3, terms="", valid_hours=48):
    """Supplier submits a quote on an open RFQ."""
    frappe.has_permission("LF RFQ Quote", "create", throw=True)

    rfq_doc = frappe.get_doc("LF RFQ", rfq)
    if rfq_doc.status not in ("open", "quoted"):
        frappe.throw(_("Cannot quote on an RFQ that is {0}.").format(rfq_doc.status))

    supplier = _get_supplier_org()

    # prevent duplicate quote from same supplier
    existing = frappe.db.exists("LF RFQ Quote", {"rfq": rfq, "supplier": supplier,
                                                  "status": ["not in", ["rejected", "expired"]]})
    if existing:
        frappe.throw(_("You have already submitted a quote for this RFQ."))

    quote = frappe.new_doc("LF RFQ Quote")
    quote.rfq = rfq
    quote.supplier = supplier
    quote.price_per_unit = flt(price_per_unit)
    quote.delivery_lead_days = cint(delivery_lead_days)
    quote.terms = terms
    quote.status = "submitted"
    quote.valid_until = add_to_date(now_datetime(), hours=cint(valid_hours))
    quote.insert(ignore_permissions=False)

    # move RFQ status to quoted
    if rfq_doc.status == "open":
        frappe.db.set_value("LF RFQ", rfq, "status", "quoted")

    return quote.name


@frappe.whitelist()
def accept_quote(quote_name):
    """Buyer accepts a submitted quote — creates an LF Order stub and links it."""
    quote = frappe.get_doc("LF RFQ Quote", quote_name)
    rfq = frappe.get_doc("LF RFQ", quote.rfq)

    if rfq.buyer != frappe.session.user:
        frappe.throw(_("Only the buyer who posted this RFQ can accept a quote."))
    if rfq.status not in ("open", "quoted"):
        frappe.throw(_("This RFQ is no longer accepting quotes."))
    if quote.status != "submitted":
        frappe.throw(_("This quote is not in submitted status."))

    # mark all other quotes on this RFQ as rejected
    frappe.db.sql("""
        UPDATE `tabLF RFQ Quote`
        SET status = 'rejected'
        WHERE rfq = %s AND name != %s AND status = 'submitted'
    """, (rfq.name, quote_name))

    # accept this quote
    frappe.db.set_value("LF RFQ Quote", quote_name, "status", "accepted")

    # close the RFQ
    frappe.db.set_value("LF RFQ", rfq.name, {
        "status": "accepted",
        "accepted_quote": quote_name,
    })

    # create the order (Phase 3 will flesh this out further)
    order_name = _create_order_from_quote(rfq, quote)
    frappe.db.set_value("LF RFQ Quote", quote_name, "order", order_name)

    return {"rfq": rfq.name, "quote": quote_name, "order": order_name}


@frappe.whitelist()
def cancel_rfq(rfq):
    """Buyer cancels an open/quoted RFQ."""
    rfq_doc = frappe.get_doc("LF RFQ", rfq)
    if rfq_doc.buyer != frappe.session.user and not frappe.has_permission("LF RFQ", "delete"):
        frappe.throw(_("Not authorised."))
    if rfq_doc.status not in ("open", "quoted"):
        frappe.throw(_("Cannot cancel an RFQ that is already {0}.").format(rfq_doc.status))
    frappe.db.set_value("LF RFQ", rfq, "status", "cancelled")
    frappe.db.sql("""
        UPDATE `tabLF RFQ Quote` SET status = 'rejected'
        WHERE rfq = %s AND status = 'submitted'
    """, (rfq,))
    return {"cancelled": rfq}


@frappe.whitelist()
def get_rfq_quotes(rfq):
    """Return quotes for a given RFQ (buyer view)."""
    rfq_doc = frappe.get_doc("LF RFQ", rfq)
    if rfq_doc.buyer != frappe.session.user and not frappe.has_permission("LF RFQ", "read"):
        frappe.throw(_("Not authorised."))
    quotes = frappe.get_all(
        "LF RFQ Quote",
        filters={"rfq": rfq},
        fields=["name", "supplier", "price_per_unit", "total_price",
                "delivery_lead_days", "terms", "status", "valid_until"],
        order_by="price_per_unit asc",
    )
    return quotes


@frappe.whitelist()
def get_open_rfqs():
    """Return open RFQs visible to suppliers (for quoting)."""
    return frappe.get_all(
        "LF RFQ",
        filters={"status": ["in", ["open", "quoted"]]},
        fields=["name", "rfq_title", "buyer", "product", "product_description",
                "quantity", "unit_label", "hub", "preferred_date",
                "budget_per_unit", "expires_at", "creation"],
        order_by="creation desc",
        limit=50,
    )


# ── helpers ────────────────────────────────────────────────────────────────

def _get_unit_label(product):
    if product:
        return frappe.db.get_value("LF Product", product, "unit_label") or "unit"
    return "unit"


def _get_supplier_org():
    """Return the LF Organization name for the logged-in supplier user."""
    org = frappe.db.sql("""
        SELECT parent FROM `tabLF Organization Member`
        WHERE user = %s AND parenttype = 'LF Organization'
        LIMIT 1
    """, (frappe.session.user,), as_dict=True)
    if not org:
        frappe.throw(_("No supplier organisation found for your account."))
    return org[0].parent


def _create_order_from_quote(rfq, quote):
    """
    Create a minimal LF Order from an accepted quote.
    Full order logic lives in api/order.py (Phase 3).
    """
    from frappe.utils import add_to_date, now_datetime
    order = frappe.new_doc("LF Order")
    order.buyer = rfq.buyer
    order.supplier = quote.supplier
    order.hub = rfq.hub
    order.rfq = rfq.name
    order.agreed_price = quote.total_price
    order.status = "confirmed"
    order.expires_at = add_to_date(now_datetime(), hours=24)
    order.payment_recorded = 0

    if rfq.product:
        prod = frappe.get_doc("LF Product", rfq.product)
        order.append("items", {
            "product": rfq.product,
            "product_name": prod.product_name,
            "quantity": rfq.quantity,
            "unit_label": rfq.unit_label,
            "unit_price": quote.price_per_unit,
            "unit_weight_kg": prod.unit_weight_kg or 0,
            "line_total": quote.total_price,
        })

    order.insert(ignore_permissions=True)
    return order.name
