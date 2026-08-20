from typing import Any, Optional

import frappe
import requests
from frappe import _

from frappe_cadence.integrations.listmonk.schemas.campaign import (
	CampaignCreateRequest,
	CampaignResponse,
	TransactionalEmailRequest,
)
from frappe_cadence.integrations.listmonk.schemas.list import (
	ListCreateRequest,
	ListResponse,
	ListUpdateRequest,
)
from frappe_cadence.integrations.listmonk.schemas.subscriber import (
	SubscriberCreateRequest,
	SubscriberListModifyRequest,
	SubscriberResponse,
	SubscriberUpdateRequest,
)
from frappe_cadence.integrations.listmonk.schemas.webhook import (
	WebhookCreateRequest,
	WebhookResponse,
	WebhookUpdateRequest,
)


def ensure_listmonk_authorized() -> None:
	settings = frappe.get_doc("Listmonk Settings")
	if not settings.enabled or settings.status != "Authorized":
		if getattr(frappe.flags, "current_job_id", None):
			frappe.wait_for(
				"on_update",
				filters={"doctype": "Listmonk Settings", "enabled": 1, "status": "Authorized"},
			)
		else:
			frappe.wait_for(
				event_key="Listmonk Settings:on_update:Listmonk Settings",
				condition="argument.get('enabled') == 1 and argument.get('status') == 'Authorized'",
			)


def _dump_model(model: Any, exclude_unset: bool = False) -> dict[str, Any]:
	if not hasattr(model, "model_dump"):
		return model if isinstance(model, dict) else {}
	try:
		return model.model_dump(exclude_unset=exclude_unset)
	except Exception:
		if exclude_unset and hasattr(model, "model_fields_set"):
			return {k: getattr(model, k) for k in model.model_fields_set}
		if hasattr(model, "model_fields"):
			return {k: getattr(model, k) for k in model.model_fields}
		return dict(model)


def _validate_model(cls: Any, data: Any) -> Any:
	if not hasattr(cls, "model_validate"):
		return data
	try:
		return cls.model_validate(data)
	except Exception:
		if isinstance(data, dict):
			return cls(**data)
		return data


class ListmonkClient:
	def __init__(
		self,
		base_url: str | None = None,
		username: str | None = None,
		token: str | None = None,
		webhook_secret: str | None = None,
		timeout: int = 30,
	) -> None:
		conf_base = None
		conf_user = None
		conf_token = None
		conf_secret = None
		try:
			if getattr(frappe, "conf", None):
				conf_base = frappe.conf.get("listmonk_base_url")
				conf_user = frappe.conf.get("listmonk_username")
				conf_token = frappe.conf.get("listmonk_access_token")
				conf_secret = frappe.conf.get("listmonk_webhook_secret")
		except Exception:
			pass

		settings_base = None
		settings_user = None
		settings_token = None
		settings_secret = None
		try:
			if getattr(frappe, "db", None) and frappe.db.exists("DocType", "Listmonk Settings"):
				settings = frappe.get_doc("Listmonk Settings")
				settings_base = getattr(settings, "base_url", None)
				settings_user = getattr(settings, "username", None)
				settings_token = settings.get_password("access_token") if settings else None
				settings_secret = settings.get_webhook_secret() if settings else None
		except Exception:
			pass

		self.base_url = (base_url or conf_base or settings_base or "").rstrip("/")
		self.username = username or conf_user or settings_user or "crm"
		self.token = token or conf_token or settings_token or ""
		self.webhook_secret = webhook_secret or conf_secret or settings_secret or ""
		self.timeout = timeout

	def get_webhook_secret(self) -> str:
		return self.webhook_secret

	def _get_headers(self) -> dict[str, str]:
		if not self.token:
			frappe.throw(_("Listmonk access_token is missing"), frappe.ValidationError)

		if self.token.startswith("Bearer "):
			auth_header = self.token
		elif self.token.startswith("token "):
			if ":" in self.token:
				auth_header = self.token
			else:
				token_val = self.token[6:].strip()
				auth_header = f"token {self.username}:{token_val}"
		elif ":" in self.token:
			auth_header = f"token {self.token}"
		else:
			auth_header = f"token {self.username}:{self.token}"

		return {
			"Authorization": auth_header,
			"Content-Type": "application/json",
		}

	def _request(
		self,
		method: str,
		endpoint: str,
		payload: dict[str, Any] | None = None,
		params: dict[str, Any] | None = None,
	) -> Any:
		if not self.base_url:
			frappe.throw(_("Listmonk base_url is missing"), frappe.ValidationError)

		url = f"{self.base_url}{endpoint}"
		headers = self._get_headers()

		response = requests.request(
			method=method,
			url=url,
			json=payload,
			params=params,
			headers=headers,
			timeout=self.timeout,
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

	def test_connection(self) -> bool:
		try:
			res = requests.get(
				f"{self.base_url}/api/sequences",
				headers=self._get_headers(),
				timeout=10,
			)
			return res.status_code == 200
		except Exception:
			return False

	# Subscriber methods
	def create_subscriber(self, req: SubscriberCreateRequest | dict[str, Any]) -> SubscriberResponse:
		data = _dump_model(req)
		res = self._request("POST", "/api/subscribers", payload=data)
		return _validate_model(SubscriberResponse, res)

	def update_subscriber(
		self, subscriber_id: int, req: SubscriberUpdateRequest | dict[str, Any]
	) -> SubscriberResponse:
		data = _dump_model(req, exclude_unset=True)
		res = self._request("PUT", f"/api/subscribers/{subscriber_id}", payload=data)
		return _validate_model(SubscriberResponse, res)

	def upsert_subscriber(
		self,
		req: SubscriberCreateRequest | SubscriberUpdateRequest | dict[str, Any],
		subscriber_id: int | None = None,
	) -> SubscriberResponse:
		if subscriber_id:
			return self.update_subscriber(subscriber_id, req)
		if isinstance(req, dict) and "id" in req:
			sub_id = req.pop("id")
			return self.update_subscriber(sub_id, req)
		return self.create_subscriber(req)

	def delete_subscriber(self, subscriber_id: int) -> bool:
		res = self._request("DELETE", f"/api/subscribers/{subscriber_id}")
		return bool(res)

	def modify_subscriber_lists(self, req: SubscriberListModifyRequest | dict[str, Any]) -> bool:
		data = _dump_model(req)
		payload = {
			"action": data.get("action", "add"),
			"ids": data.get("ids", []),
			"target_list_ids": data.get("target_list_ids", []),
			"status": data.get("status", "confirmed"),
		}
		res = self._request("PUT", "/api/subscribers/lists", payload=payload)
		return bool(res)

	# List / Sequence methods
	def create_list(self, req: ListCreateRequest | dict[str, Any]) -> ListResponse:
		data = _dump_model(req)
		payload = {
			"type": "public",
			"optin": "single",
			**data,
		}
		res = self._request("POST", "/api/lists", payload=payload)
		return _validate_model(ListResponse, res)

	def update_list(self, list_id: int, req: ListUpdateRequest | dict[str, Any]) -> ListResponse:
		data = _dump_model(req, exclude_unset=True)
		payload = {
			"type": "public",
			"optin": "single",
			**data,
		}
		res = self._request("PUT", f"/api/lists/{list_id}", payload=payload)
		return _validate_model(ListResponse, res)

	def update_list_status(self, list_id: int, status: str) -> dict[str, Any]:
		payload = {
			"name": f"Sequence {list_id}",
			"type": "public",
			"optin": "single",
			"status": status,
		}
		return self._request("PUT", f"/api/lists/{list_id}", payload=payload)

	def delete_list(self, list_id: int) -> bool:
		res = self._request("DELETE", f"/api/lists/{list_id}")
		return bool(res)

	# Webhook methods
	def get_webhooks(self) -> list[dict[str, Any]]:
		try:
			res = self._request("GET", "/api/webhooks")
			if isinstance(res, list):
				return res
		except Exception as exc:
			frappe.logger("listmonk").warning(f"Failed to fetch Listmonk webhooks: {exc}")
		return []

	def create_webhook(self, req: WebhookCreateRequest | dict[str, Any]) -> WebhookResponse:
		data = _dump_model(req)
		if not data.get("secret") and self.webhook_secret:
			data["secret"] = self.webhook_secret
		res = self._request("POST", "/api/webhooks", payload=data)
		return _validate_model(WebhookResponse, res)

	def update_webhook(self, webhook_id: int, req: WebhookUpdateRequest | dict[str, Any]) -> WebhookResponse:
		data = _dump_model(req, exclude_unset=True)
		if not data.get("secret") and self.webhook_secret:
			data["secret"] = self.webhook_secret
		res = self._request("PUT", f"/api/webhooks/{webhook_id}", payload=data)
		return _validate_model(WebhookResponse, res)

	def delete_webhook(self, webhook_id: int) -> bool:
		res = self._request("DELETE", f"/api/webhooks/{webhook_id}")
		return bool(res)

	# Campaign & Transactional methods
	def create_campaign(self, req: CampaignCreateRequest | dict[str, Any]) -> CampaignResponse:
		data = _dump_model(req)
		res = self._request("POST", "/api/campaigns", payload=data)
		return _validate_model(CampaignResponse, res)

	def send_transactional_email(self, req: TransactionalEmailRequest | dict[str, Any]) -> dict[str, Any]:
		data = _dump_model(req)
		return self._request("POST", "/api/tx", payload=data)
