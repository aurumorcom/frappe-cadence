import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.client import ListmonkClient
from frappe_cadence.integrations.listmonk.jobs.user import get_users
from frappe_cadence.tests.integration.external.conftest import (
	cadence_vcr,
	get_test_listmonk_config,
	is_listmonk_live,
)


class TestUserJobExternal(FrappeTestCase):
	def setUp(self) -> None:
		if not is_listmonk_live():
			self.skipTest(
				"LISTMONK service is not live or test configuration environment variables not provided"
			)

		cfg = get_test_listmonk_config()
		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = cfg["base_url"]
		settings.access_token = cfg["token"]
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

		self.user = frappe.get_doc(
			{
				"doctype": "User",
				"email": "alice@company.com",
				"first_name": "Alice Sales Rep",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True, ignore_links=True)

	def tearDown(self) -> None:
		frappe.db.delete("User", {"email": "alice@company.com"})

	@cadence_vcr.use_cassette("get_listmonk_users.yaml")
	def test_get_users_external_cassette(self) -> None:
		# Run get_users job against recorded Listmonk API cassette
		res = get_users()
		self.assertEqual(res["status"], "success")

		self.user.reload()
		self.assertEqual(int(self.user.listmonk_id), 10)
