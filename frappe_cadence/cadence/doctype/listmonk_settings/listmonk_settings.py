import requests
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_url


class ListmonkSettings(Document):
	def validate(self) -> None:
		if self.base_url:
			self.base_url = self.base_url.rstrip("/")

	def on_update(self) -> None:
		if not self.enabled:
			self.db_set("status", "Disabled")
			return

		token = frappe.conf.get("listmonk_access_token") or self.get_password("access_token")
		base_url = (self.base_url or frappe.conf.get("listmonk_base_url") or "").rstrip("/")

		if not base_url or not token:
			self.db_set("status", "Unauthorized")
			return

		if token.startswith("token ") or token.startswith("Bearer "):
			auth_header = token
		else:
			auth_header = f"token {token}"

		headers = {
			"Authorization": auth_header,
			"Content-Type": "application/json",
		}

		try:
			res = requests.get(f"{base_url}/api/sequences", headers=headers, timeout=10)
			if res.status_code == 200:
				self.db_set("status", "Authorized")
				frappe.publish_event("listmonk_authorized", {"enabled": 1, "status": "Authorized"})
				frappe.enqueue(
					"frappe_cadence.cadence.doctype.listmonk_settings.listmonk_settings.setup_webhook",
					queue="high",
				)
			else:
				self.db_set("status", "Unauthorized")
		except Exception as exc:
			frappe.logger("listmonk").error(f"Listmonk authorization check failed: {exc}")
			self.db_set("status", "Unauthorized")

	@frappe.whitelist()
	def bootstrap_listmonk(self) -> dict[str, str]:
		if not frappe.has_permission("Listmonk Settings", "write"):
			frappe.throw(_("Not permitted to execute bootstrap"), frappe.PermissionError)

		frappe.enqueue(
			"frappe_cadence.cadence.doctype.listmonk_settings.listmonk_settings.sync_all_crm_leads",
			queue="long",
		)
		return {"status": "success", "message": _("Bootstrap process enqueued successfully.")}


def setup_webhook() -> None:
	from frappe_cadence.integrations.listmonk import (
		create_webhook,
		ensure_listmonk_authorized,
		get_webhooks,
		update_webhook,
	)

	ensure_listmonk_authorized()

	settings = frappe.get_doc("Listmonk Settings")
	secret = settings.get_password("webhook_secret")
	site_url = get_url()
	target_url = f"{site_url}/api/method/frappe_cadence.listmonk.webhook"

	existing_webhooks = get_webhooks()
	matched_webhook = None
	if isinstance(existing_webhooks, list):
		for wh in existing_webhooks:
			if isinstance(wh, dict) and wh.get("url") == target_url:
				matched_webhook = wh
				break

	events = [
		"contact.created",
		"contact.updated",
		"sequence.step_executed"
	]

	webhook_payload = {
		"name": "Frappe Cadence Webhook",
		"url": target_url,
		"secret": secret,
		"events": events,
		"enabled": True,
	}

	if matched_webhook:
		update_webhook(matched_webhook["id"], webhook_payload)
	else:
		create_webhook(webhook_payload)


def sync_all_crm_leads() -> None:
	leads = frappe.get_all("CRM Lead", fields=["name"])
	for lead in leads:
		frappe.enqueue(
			"frappe_cadence.cadence.doctype.crm_lead.crm_lead.upsert_contact",
			queue="medium",
			lead_name=lead["name"],
		)
