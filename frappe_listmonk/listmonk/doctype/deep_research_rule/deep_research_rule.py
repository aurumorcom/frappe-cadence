import ast
import json

import frappe
from frappe import _
from frappe.model.document import Document


class DeepResearchRule(Document):
	def before_save(self) -> None:
		if self.filter_condition and self.filter_condition.strip():
			try:
				ast.parse(self.filter_condition)
				self.filter_condition_json = json.dumps({"condition": self.filter_condition})
			except Exception as exc:
				frappe.throw(_("Invalid filter condition: {0}").format(exc), frappe.ValidationError)
		else:
			self.filter_condition_json = None

	def on_update(self) -> None:
		self.ensure_playbook()

	def ensure_playbook(self) -> None:
		if not self.reference_playbook and self.rule_name:
			playbook_name = self.rule_name
			if not frappe.db.exists("Playbook", playbook_name):
				playbook = frappe.get_doc(
					{
						"doctype": "Playbook",
						"playbook_name": playbook_name,
						"document_type": self.reference_doctype or "CRM Lead",
						"enabled": 1,
					}
				)
				playbook.insert(ignore_permissions=True)
				self.db_set("reference_playbook", playbook.name)
			else:
				self.db_set("reference_playbook", playbook_name)
