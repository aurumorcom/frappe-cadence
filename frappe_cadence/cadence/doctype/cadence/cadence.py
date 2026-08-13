import ast
import json
from typing import Optional
import frappe
from frappe import _
from frappe.model.document import Document
from frappe_cadence.integrations.listmonk import (
	create_sequence,
	delete_sequence as api_delete_sequence,
	ensure_listmonk_authorized,
	update_sequence,
	update_sequence_status,
)


class Cadence(Document):
	def autoname(self) -> None:
		if not self.cadence_code:
			from frappe.model.naming import set_name_by_naming_series
			set_name_by_naming_series(self)
			self.cadence_code = self.name
		self.name = self.cadence_code

	def after_insert(self) -> None:
		self.ensure_playbook()
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
			frappe.throw(f"Invalid condition syntax: {str(e)}", frappe.ValidationError)

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
			if not (isinstance(left, ast.Attribute) and isinstance(left.value, ast.Name) and left.value.id == "doc"):
				raise ValueError("Left side of comparison must be a doc attribute (e.g., doc.status)")

			fieldname = left.attr

			right = node.comparators[0]
			if isinstance(right, ast.Constant):
				value = right.value
			elif isinstance(right, (ast.List, ast.Tuple)):
				value = [el.value for el in right.elts if isinstance(el, ast.Constant)]
			else:
				raise ValueError("Right side of comparison must be a constant or a list of constants")

			if op == ast.Eq and isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and value[0].lower() in ("like", "not like"):
				return [[fieldname, value[0].lower(), value[1]]]

			return [[fieldname, operators[op], value]]

		else:
			raise ValueError("Unsupported expression structure")

	def on_change(self) -> None:
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
			"frappe_cadence.cadence.doctype.cadence.cadence.upsert_sequence",
			queue="high",
			cadence_name=self.name,
		)
		frappe.enqueue(
			"frappe_cadence.cadence.doctype.cadence.cadence.evaluate_leads_for_cadence",
			queue="medium",
			cadence_name=self.name,
		)

	def on_trash(self) -> None:
		if self.listmonk_id:
			frappe.enqueue(
				"frappe_cadence.cadence.doctype.cadence.cadence.delete_sequence",
				queue="high",
				listmonk_id=self.listmonk_id,
			)

	def ensure_playbook(self) -> None:
		if not self.get("reference_playbook"):
			try:
				if frappe.db.exists("Playbook", self.name):
					self.db_set("reference_playbook", self.name)
					self.reference_playbook = self.name
				else:
					playbook = frappe.get_doc({
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
					}).insert(ignore_permissions=True)
					self.db_set("reference_playbook", playbook.name)
					self.reference_playbook = playbook.name
			except Exception as e:
				frappe.log_error(title="Failed to create/link playbook for Cadence", message=str(e))


def on_update(doc, method=None) -> None:
	if hasattr(doc, "on_update"):
		doc.on_update()


def on_trash(doc, method=None) -> None:
	if hasattr(doc, "on_trash"):
		doc.on_trash()


def upsert_sequence(cadence_name: str) -> None:
	ensure_listmonk_authorized()

	if not frappe.db.exists("Cadence", cadence_name):
		return

	cadence = frappe.get_doc("Cadence", cadence_name)
	payload = {
		"name": cadence.cadence_name or cadence.name,
		"description": cadence.description or "",
	}

	listmonk_id = cadence.get("listmonk_id")
	if listmonk_id:
		update_sequence(int(listmonk_id), payload)
	else:
		res = create_sequence(payload)
		if isinstance(res, dict) and res.get("id"):
			listmonk_id = res["id"]
			cadence.db_set("listmonk_id", listmonk_id)

	if listmonk_id:
		status_str = "active" if cadence.enabled else "paused"
		update_sequence_status(int(listmonk_id), status_str)


def delete_sequence(listmonk_id: int) -> None:
	ensure_listmonk_authorized()
	api_delete_sequence(int(listmonk_id))


def evaluate_leads_for_cadence(cadence_name: str) -> None:
	if not frappe.db.exists("Cadence", cadence_name):
		return

	cadence = frappe.get_doc("Cadence", cadence_name)
	if not cadence.assign_condition_json or not cadence.enabled:
		return

	enrolled_leads = frappe.get_all(
		"Multi Channel Cadence",
		filters={"cadence_name": cadence_name},
		pluck="recipient",
	)

	try:
		filters = json.loads(cadence.assign_condition_json)
		if not isinstance(filters, list):
			return

		if enrolled_leads:
			filters.append(["name", "not in", enrolled_leads])

		matching_leads = frappe.get_all("CRM Lead", filters=filters, pluck="name")
		if not matching_leads:
			return

		chunk_size = 100
		for i in range(0, len(matching_leads), chunk_size):
			chunk = matching_leads[i : i + chunk_size]
			frappe.enqueue(
				"frappe_cadence.cadence.doctype.cadence.cadence.add_lead_batch_to_cadence",
				queue="medium",
				cadence_name=cadence_name,
				lead_names=chunk,
				as_child=True,
			)
	except Exception as exc:
		frappe.logger("cadence").error(f"Error evaluating leads for cadence {cadence_name}: {exc}")


def add_lead_batch_to_cadence(cadence_name: str, lead_names: list[str]) -> list[str]:
	if not frappe.db.exists("Cadence", cadence_name):
		return []

	cadence = frappe.get_doc("Cadence", cadence_name)
	created_mccs = []

	for lead_name in lead_names:
		if frappe.db.exists("Multi Channel Cadence", {"cadence_name": cadence_name, "recipient": lead_name}):
			continue

		try:
			sender = determine_sender(cadence)
			mcc = frappe.get_doc({
				"doctype": "Multi Channel Cadence",
				"cadence_name": cadence_name,
				"cadence_for": "CRM Lead",
				"recipient": lead_name,
				"sender": sender,
				"status": "Draft",
			}).insert(ignore_permissions=True)
			created_mccs.append(mcc.name)
		except Exception as exc:
			frappe.logger("cadence").error(f"Failed to add lead {lead_name} to cadence {cadence_name}: {exc}")

	return created_mccs


def determine_sender(cadence: Cadence) -> str:
	if not cadence.users:
		return cadence.owner or frappe.session.user

	user_ids = [u.user for u in cadence.users if getattr(u, "user", None)]
	if not user_ids:
		return cadence.owner or frappe.session.user

	if cadence.rule == "Round Robin":
		if not cadence.last_user or cadence.last_user not in user_ids:
			sender = user_ids[0]
		else:
			idx = user_ids.index(cadence.last_user)
			next_idx = (idx + 1) % len(user_ids)
			sender = user_ids[next_idx]

		cadence.db_set("last_user", sender)
		return sender

	elif cadence.rule == "Load Balancing":
		counts = frappe.db.sql(
			"""
			SELECT sender, COUNT(name) as cnt
			FROM `tabMulti Channel Cadence`
			WHERE sender IN %s AND docstatus != 2
			GROUP BY sender
			""",
			(tuple(user_ids),),
			as_dict=True,
		)

		user_counts = {u: 0 for u in user_ids}
		for c in counts:
			user_counts[c["sender"]] = c["cnt"]

		sender = min(user_counts, key=user_counts.get)
		return sender

	return cadence.owner or frappe.session.user
