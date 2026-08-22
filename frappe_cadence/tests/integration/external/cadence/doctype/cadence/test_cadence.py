import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.cadence.doctype.cadence.cadence import delete_list_campaign, upsert_list_campaign
from frappe_cadence.tests.integration.external.conftest import (
	cadence_vcr,
	get_test_listmonk_config,
	is_listmonk_live,
)


class TestCadence(FrappeTestCase):
	def setUp(self) -> None:
		if not is_listmonk_live():
			self.skipTest(
				"LISTMONK service is not live or test configuration environment variables not provided"
			)

		cfg = get_test_listmonk_config()
		self.base_url = cfg["base_url"]
		self.token = cfg["token"]

		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = self.base_url
		settings.username = cfg.get("username", "crm")
		settings.access_token = self.token
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

		self.cadence = frappe.get_doc(
			{
				"doctype": "Cadence",
				"cadence_name": "External Integration Test Cadence",
				"enabled": 1,
				"description": "Campaign description for external test",
			}
		).insert(ignore_permissions=True, ignore_links=True)

	@cadence_vcr.use_cassette("cadence_upsert_delete.yaml")
	def test_upsert_and_delete_campaign_live_sync(self) -> None:
		# Upsert list & campaign against live Listmonk API
		upsert_list_campaign(self.cadence.name)
		self.cadence.reload()
		self.assertIsNotNone(self.cadence.listmonk_list_id)
		self.assertIsNotNone(self.cadence.listmonk_id)

		campaign_id = self.cadence.listmonk_id
		list_id = self.cadence.listmonk_list_id

		# Delete campaign & list against live Listmonk API
		delete_list_campaign(listmonk_id=int(campaign_id), listmonk_list_id=int(list_id))
