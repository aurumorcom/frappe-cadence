import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.listmonk_settings.listmonk_settings import setup_webhook
from frappe_cadence.tests.integration.external.conftest import get_test_listmonk_config


class TestListmonkSettings(FrappeTestCase):
	def setUp(self) -> None:
		cfg = get_test_listmonk_config()
		self.base_url = cfg["base_url"]
		self.token = cfg["token"]

		self.settings = frappe.get_doc("Listmonk Settings")
		self.settings.enabled = 1
		self.settings.base_url = self.base_url
		self.settings.save(ignore_permissions=True)
		frappe.db.commit()

	def test_listmonk_settings_on_update_authorized_and_webhook_setup(self) -> None:
		# Save triggers on_update authorization test
		self.settings.reload()
		self.assertEqual(self.settings.status, "Authorized")

		# Test setup_webhook against live Listmonk API
		setup_webhook()
