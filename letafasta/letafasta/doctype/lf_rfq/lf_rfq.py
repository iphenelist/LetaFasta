import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, now_datetime


class LFRFQ(Document):
    def before_insert(self):
        if not self.rfq_title:
            self.rfq_title = self.name or "New RFQ"
        if not self.expires_at:
            self.expires_at = add_to_date(now_datetime(), hours=24)
        if not self.buyer:
            self.buyer = frappe.session.user

    def after_insert(self):
        # update title now that name is assigned
        if self.rfq_title == "New RFQ":
            frappe.db.set_value("LF RFQ", self.name, "rfq_title", self.name)

    def validate(self):
        if not self.product and not self.product_description:
            frappe.throw("Please select a product or provide a product description.")
