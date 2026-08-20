import frappe
import requests
from frappe import _
from frappe.model.document import Document

from frappe_cadence.integrations.listmonk.client import ListmonkClient
from frappe_cadence.integrations.listmonk.jobs.webhook import setup_webhook


class ListmonkSettings(Document):
	def validate(self) -> None:
		if self.base_url:
			self.base_url = self.base_url.rstrip("/")

		access_token = getattr(self, "access_token", None)
		if access_token and set(access_token) == {"*"}:
			self.access_token = None
		webhook_secret = getattr(self, "webhook_secret", None)
		if webhook_secret and set(webhook_secret) == {"*"}:
			self.webhook_secret = None

	def get_username(self) -> str:
		conf_user = frappe.conf.get("listmonk_username")
		if conf_user:
			return conf_user
		return getattr(self, "username", None) or "crm"

	def get_access_token(self) -> str | None:
		conf_token = frappe.conf.get("listmonk_access_token")
		if conf_token:
			return conf_token

		pwd = self.get_password("access_token", raise_exception=False)
		if pwd:
			return pwd

		return None

	def get_webhook_secret(self) -> str | None:
		conf_secret = frappe.conf.get("listmonk_webhook_secret")
		if conf_secret:
			return conf_secret

		pwd = self.get_password("webhook_secret", raise_exception=False)
		if pwd:
			return pwd

		return None

	def on_update(self) -> None:
		if not self.enabled:
			self.db_set("status", "Disabled")
			return

		username = self.get_username()
		token = self.get_access_token()
		base_url = (self.base_url or frappe.conf.get("listmonk_base_url") or "").rstrip("/")

		if not base_url or not token:
			self.db_set("status", "Unauthorized")
			return

		client = ListmonkClient(base_url=base_url, username=username, token=token)

		try:
			if client.test_connection():
				self.db_set("status", "Authorized")
				frappe.enqueue(
					"frappe_cadence.integrations.listmonk.jobs.webhook.setup_webhook",
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
			"frappe_cadence.integrations.listmonk.jobs.subscriber.sync_all_crm_leads",
			queue="long",
		)
		return {"status": "success", "message": _("Bootstrap process enqueued successfully.")}
