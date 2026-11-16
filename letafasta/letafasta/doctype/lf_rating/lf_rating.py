import frappe
from frappe.model.document import Document


class LFRating(Document):
    def before_insert(self):
        if not self.buyer:
            self.buyer = frappe.session.user

    def validate(self):
        # compute overall as average of provided sub-ratings
        ratings = [r for r in [
            self.quality_rating,
            self.punctuality_rating,
            self.communication_rating,
        ] if r]
        self.overall_rating = sum(ratings) / len(ratings) if ratings else 0

    def after_insert(self):
        self._update_supplier_rating()

    def on_update(self):
        self._update_supplier_rating()

    def _update_supplier_rating(self):
        result = frappe.db.sql("""
            SELECT AVG(overall_rating) AS avg_r, COUNT(*) AS cnt
            FROM `tabLF Rating`
            WHERE supplier = %s
        """, (self.supplier,), as_dict=True)
        if result:
            frappe.db.set_value("LF Organization", self.supplier, {
                "avg_rating": round(result[0].avg_r or 0, 1),
                "total_orders_completed": result[0].cnt,
            })
