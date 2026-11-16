import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class LFOrganization(Document):
	def before_save(self):
		if self.has_value_changed("status"):
			if self.status == "approved" and not self.approved_at:
				self.approved_at = now_datetime()
				self.approved_by = frappe.session.user
			elif self.status != "approved":
				# Clear approval stamp when un-approving
				self.approved_at = None
				self.approved_by = None

	def sync_member_roles(self):
		"""Grant or revoke Frappe roles for all members based on their org role and status."""
		if self.type != "supplier":
			return
		for member in self.members:
			user = frappe.get_doc("User", member.user)
			if self.status == "approved":
				frappe_role = "LF Supplier Owner" if member.role == "owner" else "LF Supplier Staff"
				user.add_roles(frappe_role)
			else:
				user.remove_roles("LF Supplier Owner", "LF Supplier Staff")

	def after_save(self):
		if self.has_value_changed("status"):
			self.sync_member_roles()
