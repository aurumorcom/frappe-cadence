from typing import Any, Optional

import frappe

from frappe_cadence.cadence.doctype.user_bio.user_bio import get_user_bio
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


def add_subscriber_to_sequence(mcc_name: str) -> None:
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
	listmonk_sequence_id = cadence.listmonk_id
	if not listmonk_sequence_id:
		from frappe_cadence.jobs.cadence import upsert_sequence

		listmonk_sequence_id = upsert_sequence(cadence.name)
		cadence.reload()

	sender_user = mcc.sender or mcc.owner or frappe.session.user
	bio_content = resolve_user_bio(sender_user, mcc.cadence_name)

	user_doc = frappe.get_doc("User", sender_user) if frappe.db.exists("User", sender_user) else None
	user_dict = {
		"id": user_doc.name if user_doc else sender_user,
		"name": user_doc.full_name if user_doc else sender_user,
		"email_id": user_doc.email if user_doc else "",
		"bio": bio_content,
	}

	ctx_text = frappe.db.get_value("Context", {"reference_doc": mcc.name}, "content")
	if not ctx_text:
		ctx_text = frappe.db.get_value("Context", {"reference_doc": mcc.recipient}, "content") or ""

	context_dict = {"content": ctx_text}

	listmonk_subscriber_id = lead.listmonk_id
	if not listmonk_subscriber_id:
		from frappe_cadence.integrations.listmonk.jobs.subscriber import upsert_subscriber

		listmonk_subscriber_id = upsert_subscriber(lead.name)
		lead.reload()

	if not listmonk_subscriber_id:
		frappe.logger("cadence").error(f"Failed to resolve listmonk_subscriber_id for lead {lead.name}")
		return

	client = ListmonkClient()
	payload = {
		"email": lead.get("email_id") or lead.get("email") or "",
		"name": lead.get("lead_name") or lead.get("first_name") or lead.name,
		"status": "enabled",
		"lists": [int(listmonk_sequence_id)] if listmonk_sequence_id else [],
		"attribs": {
			"user": user_dict,
			"context": context_dict,
			"lead_id": lead.name,
			"company_name": lead.get("company_name") or "",
			"lead_status": lead.get("status") or "",
		},
	}

	req = SubscriberUpdateRequest.model_validate(payload)
	client.update_subscriber(int(listmonk_subscriber_id), req)

	mcc.db_set("listmonk_subscriber_id", int(listmonk_subscriber_id))
	if listmonk_sequence_id:
		mcc.db_set("listmonk_sequence_id", int(listmonk_sequence_id))
	mcc.db_set("status", "Scheduled")


def remove_subscriber_from_sequence(
	mcc_name: str,
	listmonk_subscriber_id: int | None = None,
	listmonk_sequence_id: int | None = None,
) -> None:
	ensure_listmonk_authorized()
	subscriber_id = listmonk_subscriber_id

	if not subscriber_id or not listmonk_sequence_id:
		if frappe.db.exists("Multi Channel Cadence", mcc_name):
			mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
			subscriber_id = subscriber_id or getattr(mcc, "listmonk_subscriber_id", None)
			listmonk_sequence_id = listmonk_sequence_id or mcc.listmonk_sequence_id

	if subscriber_id and listmonk_sequence_id:
		client = ListmonkClient()
		req = SubscriberListModifyRequest(
			action="remove",
			ids=[int(subscriber_id)],
			target_list_ids=[int(listmonk_sequence_id)],
		)
		client.modify_subscriber_lists(req)


def stop_mcc(mcc_name: str, reason: str = "Replied") -> None:
	if not frappe.db.exists("Multi Channel Cadence", mcc_name):
		return

	mcc = frappe.get_doc("Multi Channel Cadence", mcc_name)
	target_status = "Replied" if reason == "Replied" else "Completed"
	mcc.db_set("status", target_status)
