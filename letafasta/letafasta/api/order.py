"""
Order lifecycle APIs: create_order (direct), cancel_order, reorder, mark_payment_received.
"""
import json
import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import add_to_date, now_datetime, cint, flt


@frappe.whitelist()
def create_order(cart_json, hub, checkout_id=None):
	"""
	Direct-order path: buyer places order(s) at catalogue price without RFQ.
	cart_json: JSON list of {product, quantity, supplier} items (from localStorage).
	Returns list of created order names.
	"""
	frappe.has_permission("LF Order", "create", throw=True)

	cart = json.loads(cart_json) if isinstance(cart_json, str) else cart_json
	if not cart:
		frappe.throw(_("Cart is empty."))
	if not hub:
		frappe.throw(_("Please select a delivery hub."))

	groups = {}
	for item in cart:
		sup = item.get("supplier")
		if sup not in groups:
			groups[sup] = []
		groups[sup].append(item)

	orders = []
	for supplier, items in groups.items():
		order = _build_direct_order(supplier, items, hub, checkout_id)
		orders.append(order.name)

	return orders


@frappe.whitelist()
def cancel_order(order_name, reason=""):
	order = frappe.get_doc("LF Order", order_name)
	_assert_order_party(order)
	if order.status in ("completed", "cancelled"):
		frappe.throw(_("Cannot cancel an order that is {0}.").format(order.status))

	active_loads = frappe.db.count("LF Load", {
		"order": order_name,
		"status": ["in", ["departed", "arrived"]],
	})
	if active_loads:
		frappe.throw(_("Cannot cancel — {0} load(s) already in transit.").format(active_loads))

	frappe.db.set_value("LF Order", order_name, {
		"status": "cancelled",
		"cancel_reason": reason,
		"cancelled_at": now_datetime(),
	})
	_restore_stock(order)
	return {"cancelled": order_name}


@frappe.whitelist()
def reorder(order_name):
	"""Clone a completed order's items into a JSON cart payload."""
	order = frappe.get_doc("LF Order", order_name)
	if order.buyer != frappe.session.user:
		frappe.throw(_("Not authorised."))
	if order.status != "completed":
		frappe.throw(_("Can only reorder completed orders."))

	cart = []
	for item in order.items:
		prod = frappe.get_doc("LF Product", item.product) if item.product else None
		if prod and prod.is_active:
			cart.append({
				"product": item.product,
				"product_name": item.product_name,
				"supplier": order.supplier,
				"supplier_name": frappe.db.get_value("LF Organization", order.supplier, "org_name"),
				"unit_label": item.unit_label,
				"unit_price": prod.unit_price,
				"unit_weight_kg": item.unit_weight_kg,
				"quantity": item.quantity,
			})
	if not cart:
		frappe.throw(_("No active products found for reorder."))

	return {"cart": cart, "hub": order.hub}


@frappe.whitelist()
def mark_payment_received(order_name):
	order = frappe.get_doc("LF Order", order_name)
	_assert_order_party(order)
	frappe.db.set_value("LF Order", order_name, "payment_recorded", 1)
	return {"payment_recorded": True}


# ── helpers ────────────────────────────────────────────────────────────────

def _build_direct_order(supplier, items, hub, checkout_id):
	agreed_price = 0
	total_weight = 0

	order = frappe.new_doc("LF Order")
	order.buyer = frappe.session.user
	order.supplier = supplier
	order.hub = hub
	order.status = "confirmed"
	order.expires_at = add_to_date(now_datetime(), hours=24)
	order.checkout_id = checkout_id or ""
	order.payment_recorded = 0

	for item in items:
		prod = frappe.get_doc("LF Product", item["product"])
		qty = cint(item.get("quantity", 1))
		unit_price = flt(item.get("unit_price") or prod.unit_price)
		line_total = unit_price * qty
		weight = (prod.unit_weight_kg or 0) * qty

		order.append("items", {
			"product": prod.name,
			"product_name": prod.product_name,
			"quantity": qty,
			"unit_label": prod.unit_label,
			"unit_price": unit_price,
			"unit_weight_kg": prod.unit_weight_kg or 0,
			"line_total": line_total,
		})
		agreed_price += line_total
		total_weight += weight

		new_stock = (prod.stock_quantity or 0) - qty
		if new_stock < 0:
			frappe.throw(_("{0} only has {1} {2}s in stock.").format(
				prod.product_name, prod.stock_quantity, prod.unit_label))
		frappe.db.set_value("LF Product", prod.name, "stock_quantity", new_stock)

	order.agreed_price = agreed_price
	order.total_weight_kg = total_weight

	rate = frappe.db.get_value(
		"LF Freight Rate",
		{"parent": supplier, "hub": hub},
		"rate_per_tonne",
	)
	order.rate_per_tonne = flt(rate)

	order.insert(ignore_permissions=False)
	frappe.db.set_value("LF Order", order.name, "reference", order.name)
	return order


def _assert_order_party(order):
	roles = frappe.get_roles()
	is_buyer = order.buyer == frappe.session.user
	is_supplier = frappe.db.exists(
		"LF Organization Member",
		{"user": frappe.session.user, "parent": order.supplier},
	)
	if not (is_buyer or is_supplier or "LF Admin" in roles):
		frappe.throw(_("Not authorised."))


def _restore_stock(order):
	Product = DocType("LF Product")
	for item in frappe.get_doc("LF Order", order.name).items:
		if item.product:
			(
				frappe.qb.update(Product)
				.set(Product.stock_quantity, Product.stock_quantity + item.quantity)
				.where(Product.name == item.product)
			).run()
