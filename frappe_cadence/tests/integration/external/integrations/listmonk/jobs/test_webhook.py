from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import set_encrypted_password

from frappe_cadence.integrations.listmonk.client import ListmonkClient
from frappe_cadence.integrations.listmonk.jobs.webhook import setup_webhook
from frappe_cadence.tests.integration.external.conftest import (
	cadence_vcr,
	get_test_listmonk_config,
)


class TestListmonkWebhookJobExternal(FrappeTestCase):
	def setUp(self) -> None:
		self.config = get_test_listmonk_config()
		self.client = ListmonkClient(
			base_url=self.config["base_url"],
			username=self.config["username"],
			token=self.config["token"],
		)

	@cadence_vcr.use_cassette("integrations_webhook_provisioning.yaml")
	@patch.object(ListmonkClient, "test_connection", return_value=True)
	def test_external_setup_webhook_provisioning(self, mock_test_conn) -> None:
		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = self.config["base_url"]
		settings.username = self.config["username"]
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		set_encrypted_password("Listmonk Settings", "Listmonk Settings", self.config["token"], "access_token")
		frappe.db.commit()

		# Run setup_webhook which provisions or updates the webhook on Listmonk
		setup_webhook()

		# Verify webhook exists in Listmonk
		webhooks = self.client.get_webhooks()
		self.assertIsInstance(webhooks, list)
		matched = any(
			isinstance(wh, dict) and "frappe_cadence.listmonk.webhook" in wh.get("url", "") for wh in webhooks
		)
		self.assertTrue(matched)
