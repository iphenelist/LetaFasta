import frappe
from frappe.query_builder import DocType


def get_supplier_org(user=None):
	"""Return the LF Organization name for a user (defaults to session user)."""
	Member = DocType("LF Organization Member")
	rows = (
		frappe.qb.from_(Member)
		.select(Member.parent)
		.where(
			(Member.user == (user or frappe.session.user))
			& (Member.parenttype == "LF Organization")
		)
		.limit(1)
	).run(as_dict=True)
	return rows[0].parent if rows else None
