from typing import Any, Optional

import frappe
import requests
from frappe import _


def ensure_listmonk_authorized() -> None:
	settings = frappe.get_doc("Listmonk Settings")
	if not settings.enabled or settings.status != "Authorized":
		frappe.wait_for(
			event_key="Listmonk Settings:on_update:Listmonk Settings",
			condition="argument.get('enabled') == 1 and argument.get('status') == 'Authorized'",
		)


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


def _make_request(
	method: str,
	endpoint: str,
	payload: dict[str, Any] | None = None,
	params: dict[str, Any] | None = None,
) -> Any:
	settings = frappe.get_doc("Listmonk Settings")
	base_url = (frappe.conf.get("listmonk_base_url") or settings.base_url or "").rstrip("/")
	username = getattr(settings, "username", None) or frappe.conf.get("listmonk_username") or "crm"
	token = (
		frappe.conf.get("listmonk_access_token")
		or settings.get_password("access_token", raise_exception=False)
		or ""
	)

	if not base_url or not token:
		frappe.throw(_("Listmonk Settings base_url or access_token is missing"), frappe.ValidationError)

	url = f"{base_url}{endpoint}"
	headers = {
		"Content-Type": "application/json",
	}
	auth = None
	if token.startswith("token ") or token.startswith("Bearer ") or token.startswith("Basic "):
		headers["Authorization"] = token
	else:
		auth = (username, token)

	response = requests.request(
		method=method,
		url=url,
		json=payload,
		params=params,
		headers=headers,
		auth=auth,
		timeout=30,
	)
	response.raise_for_status()

	if response.content:
		try:
			data = response.json()
			if isinstance(data, dict) and "data" in data:
				return data["data"]
			return data
		except Exception:
			return response.text
	return True


def create_subscriber(subscriber_data: dict[str, Any]) -> dict[str, Any]:
	return _make_request("POST", "/api/subscribers", payload=subscriber_data)


def update_subscriber(subscriber_id: int, subscriber_data: dict[str, Any]) -> dict[str, Any]:
	return _make_request("PUT", f"/api/subscribers/{subscriber_id}", payload=subscriber_data)


def delete_subscriber(subscriber_id: int) -> bool:
	res = _make_request("DELETE", f"/api/subscribers/{subscriber_id}")
	return bool(res)


def create_list(list_data: dict[str, Any]) -> dict[str, Any]:
	payload = {
		"type": "public",
		"optin": "single",
		"status": "active",
		**list_data,
	}
	return _make_request("POST", "/api/lists", payload=payload)


def update_list(list_id: int, list_data: dict[str, Any]) -> dict[str, Any]:
	payload = {
		"type": "public",
		"optin": "single",
		"status": "active",
		**list_data,
	}
	return _make_request("PUT", f"/api/lists/{list_id}", payload=payload)


def delete_list(list_id: int) -> bool:
	res = _make_request("DELETE", f"/api/lists/{list_id}")
	return bool(res)


def get_list(list_id: int) -> dict[str, Any]:
	res = _make_request("GET", f"/api/lists/{list_id}")
	if isinstance(res, dict):
		return res
	return {}


def create_campaign(campaign_data: dict[str, Any]) -> dict[str, Any]:
	payload = {
		"type": "sequence",
		"status": "active",
		"description": "",
		"lists": [],
		**campaign_data,
	}
	return _make_request("POST", "/api/campaigns", payload=payload)


def update_campaign(campaign_id: int, campaign_data: dict[str, Any]) -> dict[str, Any]:
	payload = {
		"type": "sequence",
		"status": "active",
		"description": "",
		"lists": [],
		**campaign_data,
	}
	return _make_request("PUT", f"/api/campaigns/{campaign_id}", payload=payload)


def update_campaign_status(campaign_id: int, status: str) -> dict[str, Any]:
	payload = {
		"status": status,
	}
	return _make_request("PUT", f"/api/campaigns/{campaign_id}/status", payload=payload)


def delete_campaign(campaign_id: int) -> bool:
	res = _make_request("DELETE", f"/api/campaigns/{campaign_id}")
	return bool(res)


def get_campaign(campaign_id: int) -> dict[str, Any]:
	res = _make_request("GET", f"/api/campaigns/{campaign_id}")
	if isinstance(res, dict):
		return res
	return {}


def get_webhooks() -> list[dict[str, Any]]:
	res = _make_request("GET", "/api/webhooks")
	if isinstance(res, list):
		return res
	return []


def create_webhook(webhook_data: dict[str, Any]) -> dict[str, Any]:
	return _make_request("POST", "/api/webhooks", payload=webhook_data)


def update_webhook(webhook_id: int, webhook_data: dict[str, Any]) -> dict[str, Any]:
	return _make_request("PUT", f"/api/webhooks/{webhook_id}", payload=webhook_data)


def delete_webhook(webhook_id: int) -> bool:
	res = _make_request("DELETE", f"/api/webhooks/{webhook_id}")
	return bool(res)


def modify_subscriber_lists(
	action: str,
	subscriber_ids: list[int],
	list_ids: list[int],
	status: str = "confirmed",
) -> bool:
	payload = {
		"action": action,
		"ids": subscriber_ids,
		"target_list_ids": list_ids,
		"status": status,
	}
	res = _make_request("PUT", "/api/subscribers/lists", payload=payload)
	return bool(res)


def modify_subscriber_campaigns(
	action: str,
	subscriber_ids: list[int],
	list_ids: list[int],
	status: str = "confirmed",
) -> bool:
	return modify_subscriber_lists(
		action=action,
		subscriber_ids=subscriber_ids,
		list_ids=list_ids,
		status=status,
	)
