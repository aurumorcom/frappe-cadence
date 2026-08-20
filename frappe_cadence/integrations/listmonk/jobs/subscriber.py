from typing import Any, Optional

import frappe

from frappe_cadence.integrations.listmonk.client import (
	ListmonkClient,
	ensure_listmonk_authorized,
)
from frappe_cadence.integrations.listmonk.schemas.subscriber import (
	SubscriberCreateRequest,
	SubscriberUpdateRequest,
)


def upsert_subscriber(lead_name: str) -> int | None:
	ensure_listmonk_authorized()

	if not frappe.db.exists("CRM Lead", lead_name):
		return None

	lead = frappe.get_doc("CRM Lead", lead_name)
	lead_dict = frappe.parse_json(frappe.as_json(lead.as_dict()))

	email = lead.get("email_id") or lead.get("email") or ""
	name = lead.get("lead_name") or lead.get("first_name") or lead.name

	listmonk_id = lead.get("listmonk_id")
	client = ListmonkClient()

	if listmonk_id:
		req = SubscriberUpdateRequest(
			email=email or None,
			name=name or None,
			status="enabled",
			attribs={"contact": lead_dict},
		)
		resp = client.update_subscriber(int(listmonk_id), req)
		subscriber_id = resp.id
	else:
		req = SubscriberCreateRequest(
			email=email,
			name=name,
			status="enabled",
			attribs={"contact": lead_dict},
		)
		resp = client.create_subscriber(req)
		subscriber_id = resp.id
		lead.db_set("listmonk_id", subscriber_id)

	return subscriber_id


def delete_subscriber(listmonk_id: int) -> None:
	ensure_listmonk_authorized()
	client = ListmonkClient()
	client.delete_subscriber(int(listmonk_id))


def sync_all_crm_leads() -> None:
	leads = frappe.get_all("CRM Lead", fields=["name"])
	for lead in leads:
		frappe.enqueue(
			"frappe_cadence.integrations.listmonk.jobs.subscriber.upsert_subscriber",
			queue="medium",
			lead_name=lead["name"],
		)
