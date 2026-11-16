import frappe
from frappe.model.document import Document


class LFRFQQuote(Document):
    def validate(self):
        rfq = frappe.get_doc("LF RFQ", self.rfq)
        self.total_price = self.price_per_unit * (rfq.quantity or 0)
        if not self.valid_until:
            from frappe.utils import add_to_date, now_datetime
            self.valid_until = add_to_date(now_datetime(), hours=48)
