import frappe
from frappe.model.document import Document


class LFIssue(Document):
    def before_insert(self):
        if not self.raised_by:
            self.raised_by = frappe.session.user
        if not self.due_at:
            from frappe.utils import add_to_date, now_datetime
            self.due_at = add_to_date(now_datetime(), hours=24)
