from unittest.mock import patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.crm_lead.crm_lead import upsert_contact


class TestCRMLeadInternal(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": "Internal Test Lead",
			"lead_name": "Internal Test Lead",
			"email": f"test_lead_{frappe.generate_hash(length=6)}@example.com",
		}).insert(ignore_permissions=True, ignore_links=True)

	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.create_contact")
	@patch("frappe_cadence.cadence.doctype.crm_lead.crm_lead.ensure_listmonk_authorized")
	def test_upsert_contact_saves_listmonk_id_to_db(self, mock_ensure_auth, mock_create_contact) -> None:
		mock_create_contact.return_value = {"id": 888}

		upsert_contact(self.lead.name)

		self.lead.reload()
		self.assertEqual(self.lead.listmonk_id, 888)
