import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Sum


class LFRating(Document):
	def before_insert(self):
		if not self.buyer:
			self.buyer = frappe.session.user

	def validate(self):
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
		Rating = DocType("LF Rating")
		result = (
			frappe.qb.from_(Rating)
			.select(
				Sum(Rating.overall_rating).as_("sum_r"),
				Count("*").as_("cnt"),
			)
			.where(Rating.supplier == self.supplier)
		).run(as_dict=True)

		if result and result[0].cnt:
			avg = round((result[0].sum_r or 0) / result[0].cnt, 1)
			frappe.db.set_value("LF Organization", self.supplier, {
				"avg_rating": avg,
				"total_orders_completed": result[0].cnt,
			})
