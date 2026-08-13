import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.crm_lead.crm_lead import delete_contact, upsert_contact
from frappe_cadence.tests.integration.external.conftest import get_test_listmonk_config, is_listmonk_live


class TestCRMLeadExternal(FrappeTestCase):
	def setUp(self) -> None:
		if not is_listmonk_live():
			self.skipTest("LISTMONK service is not live or test configuration environment variables not provided")

		self.cfg = get_test_listmonk_config()
		frappe.db.set_value(
			"Listmonk Settings",
			"Listmonk Settings",
			{
				"base_url": self.cfg["base_url"],
				"status": "Authorized",
			},
		)

	def test_crm_lead_external_sync(self) -> None:
		lead = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": "External CRM Lead Sync Test",
			"lead_name": "External CRM Lead Sync Test",
			"email": f"crm_lead_{frappe.generate_hash(length=6)}@example.com",
			"email_id": f"crm_lead_{frappe.generate_hash(length=6)}@example.com",
		}).insert(ignore_permissions=True, ignore_links=True)

		upsert_contact(lead.name)
		lead.reload()

		listmonk_id = lead.listmonk_id
		self.assertIsNotNone(listmonk_id)

		delete_contact(listmonk_id)
