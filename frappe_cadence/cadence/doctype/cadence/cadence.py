import ast
import json
from typing import Optional

import frappe
from frappe import _
from frappe.model.document import Document


class Cadence(Document):
	def autoname(self) -> None:
		if not self.cadence_code:
			from frappe.model.naming import set_name_by_naming_series

			set_name_by_naming_series(self)
			self.cadence_code = self.name
		self.name = self.cadence_code

	def after_insert(self) -> None:
		self.ensure_playbook()
		if frappe.db.exists("DocType", "UTM Campaign"):
			if frappe.db.exists("UTM Campaign", self.name):
				mc = frappe.get_doc("UTM Campaign", self.name)
			else:
				mc = frappe.new_doc("UTM Campaign")
				mc.name = self.name
			mc.cadence_description = self.description
			mc.crm_cadence = self.name
			mc.save(ignore_permissions=True)

	def before_save(self) -> None:
		if not self.assign_condition:
			self.assign_condition_json = ""
			return

		try:
			tree = ast.parse(self.assign_condition, mode="eval")
			filters = self._ast_to_filters(tree.body)
			self.assign_condition_json = json.dumps(filters)
		except Exception as e:
			frappe.throw(f"Invalid condition syntax: {e!s}", frappe.ValidationError)

	def _ast_to_filters(self, node: ast.AST) -> list:
		operators = {
			ast.Eq: "=",
			ast.NotEq: "!=",
			ast.Gt: ">",
			ast.Lt: "<",
			ast.GtE: ">=",
			ast.LtE: "<=",
			ast.In: "in",
			ast.NotIn: "not in",
			ast.Is: "is",
		}

		if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
			filters = []
			for val in node.values:
				filters.extend(self._ast_to_filters(val))
			return filters

		elif isinstance(node, ast.Compare):
			if len(node.ops) != 1 or len(node.comparators) != 1:
				raise ValueError("Only simple comparisons are supported")

			op = type(node.ops[0])
			if op not in operators:
				raise ValueError(f"Unsupported operator: {op.__name__}")

			left = node.left
			if not (
				isinstance(left, ast.Attribute)
				and isinstance(left.value, ast.Name)
				and left.value.id == "doc"
			):
				raise ValueError("Left side of comparison must be a doc attribute (e.g., doc.status)")

			fieldname = left.attr

			right = node.comparators[0]
			if isinstance(right, ast.Constant):
				value = right.value
			elif isinstance(right, (ast.List, ast.Tuple)):
				value = [el.value for el in right.elts if isinstance(el, ast.Constant)]
			else:
				raise ValueError("Right side of comparison must be a constant or a list of constants")

			if (
				op == ast.Eq
				and isinstance(value, list)
				and len(value) == 2
				and isinstance(value[0], str)
				and value[0].lower() in ("like", "not like")
			):
				return [[fieldname, value[0].lower(), value[1]]]

			return [[fieldname, operators[op], value]]

		else:
			raise ValueError("Unsupported expression structure")

	def on_change(self) -> None:
		if frappe.db.exists("DocType", "UTM Campaign"):
			if frappe.db.exists("UTM Campaign", self.name):
				mc = frappe.get_doc("UTM Campaign", self.name)
			else:
				mc = frappe.new_doc("UTM Campaign")
				mc.name = self.name
			mc.cadence_description = self.description
			mc.crm_cadence = self.name
			mc.save(ignore_permissions=True)

	def on_update(self) -> None:
		self.ensure_playbook()
		frappe.enqueue(
			"frappe_cadence.jobs.cadence.upsert_sequence",
			queue="high",
			cadence_name=self.name,
		)
		frappe.enqueue(
			"frappe_cadence.jobs.cadence.evaluate_leads_for_cadence",
			queue="medium",
			cadence_name=self.name,
		)

	def on_trash(self) -> None:
		if self.listmonk_id:
			frappe.enqueue(
				"frappe_cadence.jobs.cadence.delete_sequence",
				queue="high",
				listmonk_id=int(self.listmonk_id),
			)

	def ensure_playbook(self) -> None:
		if not self.get("reference_playbook") and frappe.db.exists("DocType", "Playbook"):
			try:
				if frappe.db.exists("Playbook", self.name):
					self.db_set("reference_playbook", self.name)
					self.reference_playbook = self.name
				else:
					playbook = frappe.get_doc(
						{
							"doctype": "Playbook",
							"playbook_name": f"{self.name}",
							"document_type": "Multi Channel Cadence",
							"doc_event": "on_update",
							"condition_type": "Filters",
							"is_active": 0,
							"filters": [
								{"fieldname": "cadence_name", "operator": "=", "value": self.name},
								{"fieldname": "status", "operator": "=", "value": "Provisioning"},
							],
						}
					).insert(ignore_permissions=True)
					self.db_set("reference_playbook", playbook.name)
					self.reference_playbook = playbook.name
			except Exception as e:
				frappe.log_error(title="Failed to create/link playbook for Cadence", message=str(e))


def on_update(doc, method: str | None = None) -> None:
	if hasattr(doc, "on_update"):
		doc.on_update()


def on_trash(doc, method: str | None = None) -> None:
	if hasattr(doc, "on_trash"):
		doc.on_trash()
