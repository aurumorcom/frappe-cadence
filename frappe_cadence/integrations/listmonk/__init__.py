from typing import Any

import frappe
from frappe import _

from frappe_cadence.integrations.listmonk.client import ListmonkClient, ensure_listmonk_authorized


def ensure_user_listmonk_id_provisioned(sender_user: str) -> int:
	if not frappe.db.exists("User", sender_user):
		frappe.throw(_("User {0} does not exist").format(sender_user), frappe.DoesNotExistError)

	user_doc = frappe.get_doc("User", sender_user)
	listmonk_id = user_doc.get("listmonk_id")

	if not listmonk_id or frappe.utils.cint(listmonk_id) <= 0:
		if getattr(frappe.flags, "current_job_id", None):
			frappe.wait_for(
				event_key=f"User:on_update:{sender_user}",
				condition="argument.get('listmonk_id') is not None and argument.get('listmonk_id') > 0",
			)
			user_doc.reload()
			listmonk_id = user_doc.get("listmonk_id")

	return frappe.utils.cint(listmonk_id)


def ensure_user_bio_provisioned(sender_user: str, cadence_name: str) -> str:
	bios = frappe.get_all(
		"User Bio",
		filters={"reference_user": sender_user, "enabled": 1},
		fields=["name", "reference_cadence", "is_default", "content"],
	)

	matched_bio = None
	for bio in bios:
		if bio.get("reference_cadence") == cadence_name:
			matched_bio = bio.get("content")
			break

	if matched_bio is None:
		for bio in bios:
			if bio.get("is_default") == 1:
				matched_bio = bio.get("content")
				break

	if matched_bio is None:
		condition = (
			f"argument.get('reference_user') == '{sender_user}' and argument.get('enabled') == 1 "
			f"and (argument.get('reference_cadence') == '{cadence_name}' or argument.get('is_default') == 1)"
		)
		frappe.wait_for(
			event_key=f"User Bio:on_update:{sender_user}",
			condition=condition,
		)
		return ensure_user_bio_provisioned(sender_user, cadence_name)

	return matched_bio or ""


def create_subscriber(subscriber_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	res = client.create_subscriber(subscriber_data)
	return res.model_dump() if hasattr(res, "model_dump") else res


def update_subscriber(subscriber_id: int, subscriber_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	res = client.update_subscriber(subscriber_id, subscriber_data)
	return res.model_dump() if hasattr(res, "model_dump") else res


def delete_subscriber(subscriber_id: int) -> bool:
	client = ListmonkClient()
	return client.delete_subscriber(subscriber_id)


def create_list(list_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	res = client.create_list(list_data)
	return res.model_dump() if hasattr(res, "model_dump") else res


def update_list(list_id: int, list_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	res = client.update_list(list_id, list_data)
	return res.model_dump() if hasattr(res, "model_dump") else res


def delete_list(list_id: int) -> bool:
	client = ListmonkClient()
	return client.delete_list(list_id)


def get_list(list_id: int) -> dict[str, Any]:
	client = ListmonkClient()
	res = client._request("GET", f"/api/lists/{list_id}")
	return res if isinstance(res, dict) else {}


def create_campaign(campaign_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	payload = {
		"type": "sequence",
		"status": "active",
		"description": "",
		"lists": [],
		"content_type": "richtext",
		"subject": campaign_data.get("subject") or campaign_data.get("name") or "Campaign",
		"body": campaign_data.get("body") or "",
		**campaign_data,
	}
	res = client.create_campaign(payload)
	return res.model_dump() if hasattr(res, "model_dump") else (res if isinstance(res, dict) else {})


def update_campaign(campaign_id: int, campaign_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	payload = {
		"type": "sequence",
		"status": "active",
		"description": "",
		"lists": [],
		**campaign_data,
	}
	res = client.update_campaign(campaign_id, payload)
	return res.model_dump() if hasattr(res, "model_dump") else (res if isinstance(res, dict) else {})


def update_campaign_status(campaign_id: int, status: str) -> dict[str, Any]:
	client = ListmonkClient()
	return client.update_campaign_status(campaign_id, status)


def delete_campaign(campaign_id: int) -> bool:
	client = ListmonkClient()
	return client.delete_campaign(campaign_id)


def get_campaign(campaign_id: int) -> dict[str, Any]:
	client = ListmonkClient()
	return client.get_campaign(campaign_id)


def get_webhooks() -> list[dict[str, Any]]:
	client = ListmonkClient()
	return client.get_webhooks()


def create_webhook(webhook_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	res = client.create_webhook(webhook_data)
	return res.model_dump() if hasattr(res, "model_dump") else res


def update_webhook(webhook_id: int, webhook_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	res = client.update_webhook(webhook_id, webhook_data)
	return res.model_dump() if hasattr(res, "model_dump") else res


def delete_webhook(webhook_id: int) -> bool:
	client = ListmonkClient()
	return client.delete_webhook(webhook_id)


def modify_subscriber_lists(
	action: str, subscriber_ids: list[int], list_ids: list[int], status: str = "confirmed"
) -> bool:
	client = ListmonkClient()
	return client.modify_subscriber_lists(
		{"action": action, "ids": subscriber_ids, "target_list_ids": list_ids, "status": status}
	)


def modify_subscriber_campaigns(
	action: str, subscriber_ids: list[int], list_ids: list[int], status: str = "confirmed"
) -> bool:
	return modify_subscriber_lists(action=action, subscriber_ids=subscriber_ids, list_ids=list_ids, status=status)


__all__ = [
	"ListmonkClient",
	"create_campaign",
	"create_list",
	"create_subscriber",
	"create_webhook",
	"delete_campaign",
	"delete_list",
	"delete_subscriber",
	"delete_webhook",
	"ensure_listmonk_authorized",
	"ensure_user_bio_provisioned",
	"ensure_user_listmonk_id_provisioned",
	"get_campaign",
	"get_list",
	"get_webhooks",
	"modify_subscriber_campaigns",
	"modify_subscriber_lists",
	"update_campaign",
	"update_campaign_status",
	"update_list",
	"update_subscriber",
	"update_webhook",
]
