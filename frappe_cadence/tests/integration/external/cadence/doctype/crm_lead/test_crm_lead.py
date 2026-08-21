import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.cadence.doctype.crm_lead.crm_lead import delete_subscriber, upsert_subscriber
from frappe_cadence.tests.integration.external.conftest import (
	cadence_vcr,
	get_test_listmonk_config,
	is_listmonk_live,
)


class TestCRMLeadExternal(FrappeTestCase):
	def setUp(self) -> None:
		if not is_listmonk_live():
			self.skipTest(
				"LISTMONK service is not live or test configuration environment variables not provided"
			)

		self.cfg = get_test_listmonk_config()
		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = self.cfg["base_url"]
		settings.access_token = self.cfg["token"]
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	@cadence_vcr.use_cassette("crm_lead_sync.yaml")
	def test_crm_lead_external_sync(self) -> None:
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "External CRM Lead Sync Test",
				"lead_name": "External CRM Lead Sync Test",
				"email": f"crm_lead_{frappe.generate_hash(length=6)}@example.com",
				"email_id": f"crm_lead_{frappe.generate_hash(length=6)}@example.com",
			}
		).insert(ignore_permissions=True, ignore_links=True)

		upsert_subscriber(lead.name)
		lead.reload()

		listmonk_id = lead.listmonk_id
		self.assertIsNotNone(listmonk_id)

		delete_subscriber(listmonk_id)
