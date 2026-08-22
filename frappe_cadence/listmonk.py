import hashlib
import hmac
import json

import frappe
from frappe import _
from frappe.utils import now_datetime

from frappe_cadence.integrations.listmonk.client import ListmonkClient


@frappe.whitelist(allow_guest=True)
def webhook() -> dict:
	client = ListmonkClient()
	secret = client.get_webhook_secret()

	signature = (
		frappe.get_request_header("Listmonk-Signature")
		or frappe.get_request_header("X-Listmonk-Signature")
		or ""
	)

	raw_data = frappe.request.get_data() if frappe.request else b""

	if secret:
		expected_sig = hmac.new(secret.encode("utf-8"), raw_data, hashlib.sha256).hexdigest()
		if not hmac.compare_digest(signature, expected_sig):
			frappe.throw(_("Invalid Listmonk webhook signature"), frappe.PermissionError)

	try:
		payload = json.loads(raw_data.decode("utf-8")) if raw_data else frappe.local.form_dict
	except Exception:
		payload = frappe.local.form_dict

	event_type = payload.get("event") or payload.get("event_type") or ""
	data = payload.get("data") or {}

	mcc_status_map = {
		"scheduled": "Scheduled",
		"sent": "In Progress",
		"step_executed": "In Progress",
		"campaign.step_executed": "In Progress",
		"in_progress": "In Progress",
		"replied": "Replied",
		"completed": "Finished",
		"finished": "Finished",
		"unsubscribed": "Opted Out",
		"opted_out": "Opted Out",
	}

	raw_status = data.get("status") or event_type
	target_status = mcc_status_map.get(raw_status) or mcc_status_map.get(event_type)

	subscriber_id = (
		data.get("subscriber_id")
		or data.get("contact_id")
		or data.get("id")
		or payload.get("subscriber_id")
		or payload.get("contact_id")
	)
	campaign_id = data.get("campaign_id") or payload.get("campaign_id")

	filters = {}
	if subscriber_id:
		filters["listmonk_subscriber_id"] = subscriber_id
	if campaign_id:
		filters["listmonk_campaign_id"] = campaign_id

	if filters:
		mcc_list = frappe.get_all("Multi Channel Cadence", filters=filters, fields=["name", "status"])
		for mcc_item in mcc_list:
			mcc_doc = frappe.get_doc("Multi Channel Cadence", mcc_item["name"])
			if target_status and mcc_doc.status != target_status:
				mcc_doc.db_set("status", target_status)

			recipient_email = data.get("email") or payload.get("email")
			if not recipient_email and mcc_doc.recipient:
				cadence_for = getattr(mcc_doc, "cadence_for", None)
				if isinstance(cadence_for, str) and cadence_for:
					recipient_email = (
						frappe.db.get_value(
							cadence_for,
							mcc_doc.recipient,
							"email_id",
						)
						or "subscriber@system.local"
					)
				else:
					recipient_email = "subscriber@system.local"

			if target_status in ["In Progress", "Replied", "Finished"]:
				frappe.get_doc(
					{
						"doctype": "Communication",
						"communication_type": "Communication",
						"communication_medium": "Email",
						"subject": data.get("subject") or f"Listmonk Event: {event_type}",
						"content": data.get("body")
						or data.get("content")
						or f"Executed step for Listmonk event {event_type}",
						"reference_doctype": "Multi Channel Cadence",
						"reference_name": mcc_doc.name,
						"sender": data.get("sender_email")
						or payload.get("sender_email")
						or "listmonk@system.local",
						"recipients": recipient_email,
					}
				).insert(ignore_permissions=True)

	return {"status": "ok", "message": "Webhook processed successfully"}
