"""
Scheduled tasks for LetaFasta.

Registered in hooks.py:
  - flush_sms_queue: runs every minute (cron * * * * *)
  - run_scheduled_jobs: runs every 15 minutes (Frappe "all" interval)
"""

import frappe


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
	from frappe.utils import now_datetime
	expired = frappe.db.sql("""
		SELECT o.name
		FROM `tabLF Order` o
		WHERE o.status = 'confirmed'
		  AND o.expires_at < %s
		  AND NOT EXISTS (
		      SELECT 1 FROM `tabLF Load` l
		      WHERE l.order = o.name
		        AND l.status IN ('booked','departed','arrived','collected')
		  )
	""", (now_datetime(),), as_dict=True)

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
	from frappe.utils import now_datetime
	frappe.db.sql("""
		UPDATE `tabLF RFQ`
		SET status = 'expired'
		WHERE status IN ('open','quoted')
		  AND expires_at < %s
	""", (now_datetime(),))
	frappe.db.commit()


def _restore_stock_for_order(order_name):
	items = frappe.get_all("LF Order Item",
	                       filters={"parent": order_name},
	                       fields=["product", "quantity"])
	for item in items:
		if item.product:
			frappe.db.sql(
				"UPDATE `tabLF Product` SET stock_quantity = stock_quantity + %s WHERE name = %s",
				(item.quantity, item.product),
			)
