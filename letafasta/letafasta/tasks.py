"""
Scheduled tasks for LetaFasta.

Registered in hooks.py:
  - flush_sms_queue: runs every minute (cron * * * * *)
  - run_scheduled_jobs: runs every 15 minutes (Frappe "all" interval)
"""

import frappe
from frappe.query_builder import DocType
from frappe.utils import now_datetime


def flush_sms_queue():
	"""Send pending SMS notifications from the LF Notification queue."""
	if not frappe.db.get_single_value("LF Platform Settings", "sms_enabled"):
		return
	# Phase 6: implemented in letafasta.letafasta.utils.sms


def run_scheduled_jobs():
	"""Business-logic scheduler — runs every Frappe 'all' tick (≈15 min)."""
	expire_orders()
	expire_rfqs()
	# escalate_issues()     # Phase 5
	# send_arrival_reminders()  # Phase 6


def expire_orders():
	"""Cancel confirmed orders older than 24h with no booked loads."""
	Order = DocType("LF Order")
	Load = DocType("LF Load")

	booked_orders = (
		frappe.qb.from_(Load)
		.select(Load.order)
		.where(Load.status.isin(["booked", "departed", "arrived", "collected"]))
	)

	expired = (
		frappe.qb.from_(Order)
		.select(Order.name)
		.where(
			(Order.status == "confirmed")
			& (Order.expires_at < now_datetime())
			& Order.name.notin(booked_orders)
		)
	).run(as_dict=True)

	for row in expired:
		frappe.db.set_value("LF Order", row.name, {
			"status": "cancelled",
			"cancel_reason": "Auto-cancelled: no load booked within 24 hours",
			"cancelled_at": now_datetime(),
		})
		_restore_stock_for_order(row.name)
	if expired:
		frappe.db.commit()


def expire_rfqs():
	"""Expire open/quoted RFQs past their expires_at."""
	Rfq = DocType("LF RFQ")
	(
		frappe.qb.update(Rfq)
		.set(Rfq.status, "expired")
		.where(
			Rfq.status.isin(["open", "quoted"])
			& (Rfq.expires_at < now_datetime())
		)
	).run()
	frappe.db.commit()


def _restore_stock_for_order(order_name):
	Product = DocType("LF Product")
	items = frappe.get_all(
		"LF Order Item",
		filters={"parent": order_name},
		fields=["product", "quantity"],
	)
	for item in items:
		if item.product:
			(
				frappe.qb.update(Product)
				.set(Product.stock_quantity, Product.stock_quantity + item.quantity)
				.where(Product.name == item.product)
			).run()
