from unittest.mock import patch
import frappe
from frappe.tests.utils import FrappeTestCase


class TestMultiChannelCadenceIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.lead = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": "Integration",
			"lead_name": "Integration Lead MCC",
			"email_id": "mcc.lead@example.com",
		}).insert(ignore_permissions=True, ignore_links=True)

		self.cadence = frappe.get_doc({
			"doctype": "Cadence",
			"cadence_name": "Integration Cadence MCC",
			"enabled": 1,
			"listmonk_id": 901,
		}).insert(ignore_permissions=True, ignore_links=True)

		self.mcc = frappe.get_doc({
			"doctype": "Multi Channel Cadence",
			"cadence_name": self.cadence.name,
			"cadence_for": "CRM Lead",
			"recipient": self.lead.name,
			"sender": "Administrator",
			"status": "Draft",
		}).insert(ignore_permissions=True, ignore_links=True)

	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.update_contact")
	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.ensure_user_bio_provisioned", return_value="Bio Markdown")
	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.ensure_listmonk_authorized")
	def test_mcc_full_database_lifecycle(self, mock_ensure_auth, mock_ensure_bio, mock_update_contact) -> None:
		from frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence import add_contact_to_sequence

		self.lead.db_set("listmonk_id", 333)

		add_contact_to_sequence(self.mcc.name)

		self.mcc.reload()
		self.assertEqual(self.mcc.status, "Scheduled")
		self.assertEqual(self.mcc.listmonk_contact_id, 333)
		self.assertEqual(self.mcc.listmonk_sequence_id, 901)
		mock_update_contact.assert_called_once()
