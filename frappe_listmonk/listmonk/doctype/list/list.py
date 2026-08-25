import frappe
from frappe.model.document import Document


class List(Document):
	def on_update(self) -> None:
		frappe.enqueue(
			"frappe_listmonk.jobs.list.upsert_list",
			queue="short",
			list_name=self.name,
			enqueue_after_commit=True,
		)

	def on_trash(self) -> None:
		frappe.enqueue(
			"frappe_listmonk.jobs.list.delete_list",
			queue="short",
			list_name=self.name,
			listmonk_list_id=self.listmonk_list_id,
			enqueue_after_commit=True,
		)
