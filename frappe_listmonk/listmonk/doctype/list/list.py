import ast
import json

import frappe
from frappe import _
from frappe.model.document import Document


class List(Document):
	def validate(self) -> None:
		filter_condition = self.get("filter_condition")
		if filter_condition and filter_condition.strip():
			try:
				ast.parse(filter_condition)
				self.filter_condition_json = json.dumps({"condition": filter_condition})
			except Exception as exc:
				frappe.throw(_("Invalid filter condition: {0}").format(exc), frappe.ValidationError)
		else:
			self.filter_condition_json = None

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
			listmonk_id=self.listmonk_id,
			enqueue_after_commit=True,
		)
