import frappe
from frappe.model.document import Document


class LFPaymentRecord(Document):
    def before_insert(self):
        if not self.recorded_by:
            self.recorded_by = frappe.session.user
