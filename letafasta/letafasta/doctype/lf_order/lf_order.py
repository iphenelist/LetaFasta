import frappe
from frappe.model.document import Document


class LFOrder(Document):
    def before_insert(self):
        if not self.reference:
            self.reference = self.name or "New Order"

    def after_insert(self):
        if self.reference == "New Order":
            frappe.db.set_value("LF Order", self.name, "reference", self.name)
