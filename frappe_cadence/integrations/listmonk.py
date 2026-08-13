from typing import Any, Optional
import requests
import frappe
from frappe import _


def ensure_listmonk_authorized() -> None:
	settings = frappe.get_doc("Listmonk Settings")
	if not settings.enabled or settings.status != "Authorized":
		frappe.wait_for(
			"listmonk_authorized",
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
		frappe.wait_for("user_bio_provisioned", condition=condition)
		return ensure_user_bio_provisioned(sender_user, cadence_name)

	return matched_bio or ""


def _make_request(
	method: str,
	endpoint: str,
	payload: Optional[dict[str, Any]] = None,
	params: Optional[dict[str, Any]] = None,
) -> Any:
	settings = frappe.get_doc("Listmonk Settings")
	base_url = (frappe.conf.get("listmonk_base_url") or settings.base_url or "").rstrip("/")
	token = frappe.conf.get("listmonk_access_token") or settings.get_password("access_token")

	if not base_url or not token:
		frappe.throw(_("Listmonk Settings base_url or access_token is missing"), frappe.ValidationError)

	url = f"{base_url}{endpoint}"
	if token.startswith("token ") or token.startswith("Bearer "):
		auth_header = token
	else:
		auth_header = f"token {token}"

	headers = {
		"Authorization": auth_header,
		"Content-Type": "application/json",
	}

	response = requests.request(
		method=method,
		url=url,
		json=payload,
		params=params,
		headers=headers,
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


def create_contact(contact_data: dict[str, Any]) -> dict[str, Any]:
	return _make_request("POST", "/api/contacts", payload=contact_data)


def update_contact(contact_id: int, contact_data: dict[str, Any]) -> dict[str, Any]:
	return _make_request("PUT", f"/api/contacts/{contact_id}", payload=contact_data)


def delete_contact(contact_id: int) -> bool:
	res = _make_request("DELETE", f"/api/contacts/{contact_id}")
	return bool(res)


def create_sequence(sequence_data: dict[str, Any]) -> dict[str, Any]:
	payload = {
		"type": "public",
		"optin": "single",
		**sequence_data,
	}
	return _make_request("POST", "/api/lists", payload=payload)


def update_sequence(sequence_id: int, sequence_data: dict[str, Any]) -> dict[str, Any]:
	payload = {
		"type": "public",
		"optin": "single",
		**sequence_data,
	}
	return _make_request("PUT", f"/api/lists/{sequence_id}", payload=payload)


def update_sequence_status(sequence_id: int, status: str) -> dict[str, Any]:
	payload = {
		"name": f"Sequence {sequence_id}",
		"type": "public",
		"optin": "single",
		"status": status,
	}
	return _make_request("PUT", f"/api/lists/{sequence_id}", payload=payload)


def delete_sequence(sequence_id: int) -> bool:
	res = _make_request("DELETE", f"/api/lists/{sequence_id}")
	return bool(res)


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


def modify_contact_sequences(
	action: str,
	contact_ids: list[int],
	sequence_ids: list[int],
	status: str = "confirmed",
) -> bool:
	payload = {
		"action": action,
		"ids": contact_ids,
		"target_list_ids": sequence_ids,
		"status": status,
	}
	res = _make_request("PUT", "/api/subscribers/lists", payload=payload)
	return bool(res)
