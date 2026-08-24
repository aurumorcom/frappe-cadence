import json
from typing import Any, Optional

import frappe

from frappe_cadence.cadence.doctype.user_bio.user_bio import get_user_bio
from frappe_cadence.integrations.listmonk import ensure_user_listmonk_id_provisioned
from frappe_cadence.integrations.listmonk.client import (
	ListmonkClient,
	ensure_listmonk_authorized,
)
from frappe_cadence.integrations.listmonk.schemas.subscriber import (
	SubscriberListModifyRequest,
	SubscriberUpdateRequest,
)


def resolve_user_bio(sender_user: str, cadence_name: str | None = None) -> str:
	bio = get_user_bio(sender_user, reference_cadence=cadence_name)
	if bio:
		return bio
	user_doc = frappe.get_doc("User", sender_user) if frappe.db.exists("User", sender_user) else None
	user_name = user_doc.full_name if user_doc else sender_user
	return f"Sales Representative ({user_name})"


def add_subscriber_to_campaign(mcc_name: str) -> None:
	ensure_listmonk_authorized()

	if not frappe.db.exists("Multi Channel Cadence", mcc_name):
		return

	mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
	if not frappe.db.exists("CRM Lead", mcc.recipient):
		return

	lead = frappe.get_doc("CRM Lead", mcc.recipient)
	if not frappe.db.exists("Cadence", mcc.cadence_name):
		return

	cadence = frappe.get_doc("Cadence", mcc.cadence_name)
	listmonk_campaign_id = cadence.listmonk_id
	if not listmonk_campaign_id:
		from frappe_cadence.jobs.cadence import upsert_campaign

		listmonk_campaign_id = upsert_campaign(cadence.name)
		cadence.reload()

	sender_user = mcc.sender or mcc.owner or frappe.session.user
	user_listmonk_id = ensure_user_listmonk_id_provisioned(sender_user)
	bio_content = resolve_user_bio(sender_user, mcc.cadence_name)

	user_doc = frappe.get_doc("User", sender_user) if frappe.db.exists("User", sender_user) else None
	if user_doc:
		doc_dict = user_doc.as_dict()
		if isinstance(doc_dict, dict):
			user_dict = json.loads(frappe.as_json(doc_dict))
			if not isinstance(user_dict, dict):
				user_dict = {"name": sender_user, "email": getattr(user_doc, "email", sender_user)}
		else:
			user_dict = {"name": sender_user, "email": getattr(user_doc, "email", sender_user)}
	else:
		user_dict = {"name": sender_user}

	user_dict["id"] = user_listmonk_id
	user_dict["bio"] = bio_content

	deep_research_text = frappe.db.get_value("Deep Research", {"reference_doc": mcc.name}, "content")
	if not deep_research_text:
		deep_research_text = (
			frappe.db.get_value("Deep Research", {"reference_doc": mcc.recipient}, "content") or ""
		)

	deep_research_dict = {"content": deep_research_text}

	listmonk_subscriber_id = lead.listmonk_id
	if not listmonk_subscriber_id:
		from frappe_cadence.integrations.listmonk.jobs.subscriber import upsert_subscriber

		listmonk_subscriber_id = upsert_subscriber(lead.name)
		lead.reload()

	if not listmonk_subscriber_id:
		frappe.logger("cadence").error(f"Failed to resolve listmonk_subscriber_id for lead {lead.name}")
		return

	client = ListmonkClient()
	list_id = cadence.listmonk_list_id or listmonk_campaign_id
	payload = {
		"email": lead.get("email_id") or lead.get("email") or "",
		"name": lead.get("lead_name") or lead.get("first_name") or lead.name,
		"status": "enabled",
		"lists": [int(list_id)] if list_id else [],
		"attribs": {
			"user": user_dict,
			"deep_research": deep_research_dict,
			"lead_id": lead.name,
			"company_name": lead.get("company_name") or "",
			"lead_status": lead.get("status") or "",
		},
	}

	req = SubscriberUpdateRequest.model_validate(payload)
	client.update_subscriber(int(listmonk_subscriber_id), req)

	mcc.db_set("listmonk_subscriber_id", int(listmonk_subscriber_id))
	if listmonk_campaign_id:
		mcc.db_set("listmonk_campaign_id", int(listmonk_campaign_id))
	if cadence.listmonk_list_id:
		mcc.db_set("listmonk_list_id", int(cadence.listmonk_list_id))
	mcc.db_set("status", "Scheduled")


def remove_subscriber_from_campaign(
	mcc_name: str,
	listmonk_subscriber_id: int | None = None,
	listmonk_campaign_id: int | None = None,
) -> None:
	ensure_listmonk_authorized()
	subscriber_id = listmonk_subscriber_id

	target_list_id = None
	if frappe.db.exists("Multi Channel Cadence", mcc_name):
		mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
		subscriber_id = subscriber_id or getattr(mcc, "listmonk_subscriber_id", None)
		listmonk_campaign_id = listmonk_campaign_id or getattr(mcc, "listmonk_campaign_id", None)
		target_list_id = getattr(mcc, "listmonk_list_id", None)

	target_list_ids = (
		[int(target_list_id)]
		if target_list_id
		else ([int(listmonk_campaign_id)] if listmonk_campaign_id else [])
	)

	if subscriber_id and target_list_ids:
		client = ListmonkClient()
		req = SubscriberListModifyRequest(
			action="remove",
			ids=[int(subscriber_id)],
			target_list_ids=target_list_ids,
		)
		client.modify_subscriber_lists(req)


def stop_mcc(mcc_name: str, reason: str = "Replied") -> None:
	if not frappe.db.exists("Multi Channel Cadence", mcc_name):
		return

	mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
	target_status = "Replied" if reason == "Replied" else "Completed"
	mcc.db_set("status", target_status)
