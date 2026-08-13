from typing import Optional
import frappe
from frappe_cadence.integrations.listmonk import (
	create_contact,
	delete_contact as api_delete_contact,
	ensure_listmonk_authorized,
	update_contact,
)


def on_update(doc, method: Optional[str] = None) -> None:
	if not doc.name:
		return
	frappe.enqueue(
		"frappe_cadence.cadence.doctype.crm_lead.crm_lead.upsert_contact",
		queue="high",
		lead_name=doc.name,
	)
	frappe.enqueue(
		"frappe_cadence.cadence.doctype.crm_lead.crm_lead.evaluate_cadences_for_lead",
		queue="high",
		lead_name=doc.name,
	)


def on_trash(doc, method: Optional[str] = None) -> None:
	listmonk_id = doc.get("listmonk_id")
	if listmonk_id:
		frappe.enqueue(
			"frappe_cadence.cadence.doctype.crm_lead.crm_lead.delete_contact",
			queue="high",
			listmonk_id=listmonk_id,
		)


def upsert_contact(lead_name: str) -> None:
	ensure_listmonk_authorized()

	if not frappe.db.exists("CRM Lead", lead_name):
		return

	lead = frappe.get_doc("CRM Lead", lead_name)
	lead_dict = frappe.parse_json(frappe.as_json(lead.as_dict()))

	email = lead.get("email_id") or lead.get("email") or ""
	name = lead.get("lead_name") or lead.get("first_name") or lead.name

	payload = {
		"email": email,
		"name": name,
		"status": "enabled",
		"attribs": {"contact": lead_dict},
	}

	listmonk_id = lead.get("listmonk_id")
	if listmonk_id:
		update_contact(int(listmonk_id), payload)
	else:
		res = create_contact(payload)
		if isinstance(res, dict) and res.get("id"):
			lead.db_set("listmonk_id", res["id"])


def delete_contact(listmonk_id: int) -> None:
	ensure_listmonk_authorized()
	api_delete_contact(int(listmonk_id))


def evaluate_cadences_for_lead(lead_name: str) -> None:
	cadences = frappe.get_all(
		"Cadence",
		filters={"enabled": 1},
		fields=["name", "assign_condition_json"],
	)

	for cadence in cadences:
		if cadence.get("assign_condition_json"):
			frappe.enqueue(
				"frappe_cadence.cadence.doctype.cadence.cadence.add_lead_batch_to_cadence",
				queue="high",
				cadence_name=cadence["name"],
				lead_names=[lead_name],
				as_child=True,
			)
