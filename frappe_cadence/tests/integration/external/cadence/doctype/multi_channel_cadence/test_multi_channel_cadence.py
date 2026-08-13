from unittest.mock import patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence import (
	add_contact_to_sequence,
	remove_contact_from_sequence,
)
from frappe_cadence.tests.integration.external.conftest import get_test_listmonk_config


class TestMultiChannelCadence(FrappeTestCase):
	def setUp(self) -> None:
		cfg = get_test_listmonk_config()
		self.base_url = cfg["base_url"]
		self.token = cfg["token"]

		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.base_url = self.base_url
		settings.status = "Authorized"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

		self.cadence = frappe.get_doc({
			"doctype": "Cadence",
			"cadence_name": "MCC External Test Cadence",
			"enabled": 1,
			"listmonk_id": 901,
		}).insert(ignore_permissions=True, ignore_links=True)

		self.lead = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": "MCC",
			"lead_name": "MCC External Lead",
			"email": "mcc_external_lead@example.com",
			"email_id": "mcc_external_lead@example.com",
			"listmonk_id": 801,
		}).insert(ignore_permissions=True, ignore_links=True)

		self.mcc = frappe.get_doc({
			"doctype": "Multi Channel Cadence",
			"cadence_name": self.cadence.name,
			"recipient": self.lead.name,
			"status": "Provisioning",
			"sender_user": "Administrator",
		}).insert(ignore_permissions=True, ignore_links=True)

	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.update_contact")
	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.ensure_user_bio_provisioned", return_value="Test Bio Content")
	def test_add_and_remove_contact_sequence(self, mock_bio, mock_update_contact) -> None:
		add_contact_to_sequence(self.mcc.name)

		self.mcc.reload()
		self.assertEqual(self.mcc.status, "Scheduled")
		self.assertEqual(self.mcc.listmonk_contact_id, 801)
		self.assertEqual(self.mcc.listmonk_sequence_id, 901)
		mock_update_contact.assert_called_once()

		# Test unenrollment
		with patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.modify_contact_sequences") as mock_modify:
			remove_contact_from_sequence(self.mcc.name, listmonk_contact_id=801, listmonk_sequence_id=901)
			mock_modify.assert_called_once_with(
				action="remove",
				contact_ids=[801],
				sequence_ids=[901],
			)
