from typing import Any

import frappe

from frappe_cadence.integrations.listmonk.client import ListmonkClient, ensure_listmonk_authorized


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


def create_sequence(sequence_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	payload = {
		"status": "active",
		"description": "",
		"lists": [],
		"email_ids": [],
		"waha_sessions": [],
		**sequence_data,
	}
	res = client._request("POST", "/api/sequences", payload=payload)
	return res if isinstance(res, dict) else {}


def update_sequence(sequence_id: int, sequence_data: dict[str, Any]) -> dict[str, Any]:
	client = ListmonkClient()
	payload = {
		"status": "active",
		"description": "",
		"lists": [],
		"email_ids": [],
		"waha_sessions": [],
		**sequence_data,
	}
	res = client._request("PUT", f"/api/sequences/{sequence_id}", payload=payload)
	return res if isinstance(res, dict) else {}


def update_sequence_status(sequence_id: int, status: str) -> dict[str, Any]:
	client = ListmonkClient()
	return client.update_list_status(sequence_id, status)


def delete_sequence(sequence_id: int) -> bool:
	client = ListmonkClient()
	return client.delete_list(sequence_id)


def get_sequence(sequence_id: int) -> dict[str, Any]:
	client = ListmonkClient()
	res = client._request("GET", f"/api/sequences/{sequence_id}")
	return res if isinstance(res, dict) else {}


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


def modify_subscriber_sequences(
	action: str, subscriber_ids: list[int], sequence_ids: list[int], status: str = "confirmed"
) -> bool:
	return modify_subscriber_lists(action=action, subscriber_ids=subscriber_ids, list_ids=sequence_ids, status=status)


__all__ = [
	"ListmonkClient",
	"create_list",
	"create_sequence",
	"create_subscriber",
	"create_webhook",
	"delete_list",
	"delete_sequence",
	"delete_subscriber",
	"delete_webhook",
	"ensure_listmonk_authorized",
	"ensure_user_bio_provisioned",
	"get_list",
	"get_sequence",
	"get_webhooks",
	"modify_subscriber_lists",
	"modify_subscriber_sequences",
	"update_list",
	"update_sequence",
	"update_sequence_status",
	"update_subscriber",
	"update_webhook",
]
