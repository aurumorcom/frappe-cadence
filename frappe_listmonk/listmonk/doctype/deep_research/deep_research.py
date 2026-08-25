import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class DeepResearch(Document):
	def before_save(self) -> None:
		if not self.is_new() and self.has_value_changed("content"):
			old_doc = self.get_doc_before_save()
			old_content = old_doc.content if old_doc else ""
			if old_content:
				self.append(
					"history",
					{
						"timestamp": now_datetime(),
						"user": frappe.session.user if frappe.session else "Administrator",
						"content_snapshot": old_content,
					},
				)
