import hashlib
import hmac
import json
from typing import Any, Optional

import frappe
from frappe import _
from frappe.utils import get_url

from frappe_cadence.integrations.listmonk.client import (
	ListmonkClient,
	ensure_listmonk_authorized,
)
from frappe_cadence.integrations.listmonk.schemas.webhook import (
	WebhookCreateRequest,
	WebhookEventPayload,
	WebhookUpdateRequest,
)


def setup_webhook() -> None:
	ensure_listmonk_authorized()

	settings = frappe.get_doc("Listmonk Settings")
	secret = settings.get_password("webhook_secret") if settings else None
	site_url = get_url()
	target_url = f"{site_url}/api/method/frappe_cadence.integrations.listmonk.jobs.webhook.webhook"

	client = ListmonkClient()
	existing_webhooks = client.get_webhooks()
	matched_webhook = None
	if isinstance(existing_webhooks, list):
		for wh in existing_webhooks:
			if isinstance(wh, dict) and wh.get("url") == target_url:
				matched_webhook = wh
				break

	events = [
		"campaign.started",
		"campaign.sent",
		"subscriber.bounced",
		"contact.created",
		"contact.updated",
		"sequence.step_executed",
	]

	if matched_webhook:
		req = WebhookUpdateRequest(
			name="Frappe Cadence Webhook",
			url=target_url,
			secret=secret,
			events=events,
			enabled=True,
		)
		client.update_webhook(matched_webhook["id"], req)
	else:
		create_req = WebhookCreateRequest(
			name="Frappe Cadence Webhook",
			url=target_url,
			headers={},
			events=events,
			secret=secret,
			enabled=True,
		)
		client.create_webhook(create_req)


@frappe.whitelist(allow_guest=True)
def webhook() -> dict[str, Any]:
	settings = (
		frappe.get_doc("Listmonk Settings") if frappe.db.exists("DocType", "Listmonk Settings") else None
	)
	secret = frappe.conf.get("listmonk_webhook_secret") or (
		settings.get_password("webhook_secret") if settings else ""
	)

	signature = (
		frappe.get_request_header("Listmonk-Signature")
		or frappe.get_request_header("X-Listmonk-Signature")
		or ""
	)

	raw_data = frappe.request.get_data() if frappe.request else b""

	if secret and raw_data:
		expected_sig = hmac.new(secret.encode("utf-8"), raw_data, hashlib.sha256).hexdigest()
		if not hmac.compare_digest(signature, expected_sig):
			frappe.throw(_("Invalid Listmonk webhook signature"), frappe.PermissionError)

	try:
		payload = json.loads(raw_data.decode("utf-8")) if raw_data else frappe.local.form_dict
	except Exception:
		payload = frappe.local.form_dict

	return process_webhook_payload(payload)


def process_webhook_payload(payload: dict[str, Any]) -> dict[str, Any]:
	event_payload = WebhookEventPayload(
		event=payload.get("event") or payload.get("event_type") or "",
		data=payload.get("data") or payload,
	)

	event_type = event_payload.event
	data = event_payload.data

	mcc_status_map = {
		"scheduled": "Scheduled",
		"sent": "In Progress",
		"step_executed": "In Progress",
		"sequence.step_executed": "In Progress",
		"in_progress": "In Progress",
		"replied": "Replied",
		"completed": "Finished",
		"finished": "Finished",
		"unsubscribed": "Opted Out",
		"opted_out": "Opted Out",
	}

	raw_status = data.get("status") or event_type
	target_status = mcc_status_map.get(raw_status) or mcc_status_map.get(event_type)

	contact_id = (
		data.get("subscriber_id")
		or data.get("contact_id")
		or data.get("id")
		or payload.get("contact_id")
		or payload.get("subscriber_id")
	)
	sequence_id = data.get("sequence_id") or payload.get("sequence_id")

	filters = {}
	if contact_id:
		filters["listmonk_contact_id"] = contact_id
	if sequence_id:
		filters["listmonk_sequence_id"] = sequence_id

	if filters:
		mcc_list = frappe.get_all("Multi Channel Cadence", filters=filters, fields=["name", "status"])
		for mcc_item in mcc_list:
			mcc_doc = frappe.get_doc("Multi Channel Cadence", mcc_item["name"])
			if target_status and mcc_doc.status != target_status:
				mcc_doc.db_set("status", target_status)

	return {"status": "ok", "message": "Webhook processed successfully"}
