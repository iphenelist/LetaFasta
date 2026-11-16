import frappe
from frappe.model.document import Document


class LFProduct(Document):
    def validate(self):
        if self.stock_quantity < 0:
            frappe.throw("Stock quantity cannot be negative.")
