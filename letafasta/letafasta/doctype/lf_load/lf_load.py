import frappe
from frappe.model.document import Document


class LFLoad(Document):
    def before_insert(self):
        if not self.label:
            # auto-label as Truck A, B, C…
            count = frappe.db.count("LF Load", {"order": self.order})
            self.label = "Truck " + chr(65 + count)  # A, B, C…

    def validate(self):
        booked_statuses = ("booked", "departed", "arrived", "collected")
        if self.status in booked_statuses:
            if not self.plate_number:
                frappe.throw("Plate number is required once a load is booked.")
            if not self.driver_name:
                frappe.throw("Driver name is required once a load is booked.")
