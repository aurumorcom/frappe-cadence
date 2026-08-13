from unittest.mock import MagicMock, patch
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence import (
	MultiChannelCadence,
	add_contact_to_sequence,
	remove_contact_from_sequence,
)


class TestMultiChannelCadenceUnit(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_mcc_on_trash_enqueues_remove_contact_from_sequence(self, mock_enqueue) -> None:
		mcc = MultiChannelCadence.__new__(MultiChannelCadence)
		mcc.name = "MCC-001"
		mcc.listmonk_contact_id = 10
		mcc.listmonk_sequence_id = 20

		mcc.on_trash()

		mock_enqueue.assert_called_once_with(
			"frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.remove_contact_from_sequence",
			queue="high",
			mcc_name="MCC-001",
			listmonk_contact_id=10,
			listmonk_sequence_id=20,
		)

	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.update_contact")
	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.ensure_user_bio_provisioned", return_value="User Bio Content")
	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.ensure_listmonk_authorized")
	@patch("frappe.db.get_value", return_value="Context Content")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_add_contact_to_sequence(self, mock_exists, mock_get_doc, mock_db_get_value, mock_ensure_auth, mock_ensure_bio, mock_update_contact) -> None:
		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-001"
		mcc_mock.recipient = "LEAD-001"
		mcc_mock.cadence_name = "CAD-001"
		mcc_mock.sender = "sales_rep@example.com"
		mcc_mock.owner = "sales_rep@example.com"

		lead_mock = MagicMock()
		lead_mock.name = "LEAD-001"
		lead_mock.listmonk_id = 55
		lead_mock.get.side_effect = lambda k, default=None: {"email_id": "lead@example.com", "lead_name": "Jane Doe", "company_name": "Acme", "status": "Open"}.get(k, default)

		cadence_mock = MagicMock()
		cadence_mock.listmonk_id = 99

		user_mock = MagicMock()
		user_mock.name = "sales_rep@example.com"
		user_mock.full_name = "Sales Rep"
		user_mock.email = "sales_rep@example.com"

		mock_get_doc.side_effect = [mcc_mock, lead_mock, cadence_mock, user_mock]

		add_contact_to_sequence("MCC-001")

		mock_ensure_auth.assert_called_once()
		mock_ensure_bio.assert_called_once_with("sales_rep@example.com", "CAD-001")
		mock_update_contact.assert_called_once()

		args, kwargs = mock_update_contact.call_args
		self.assertEqual(args[0], 55)
		payload = args[1]
		self.assertEqual(payload["email"], "lead@example.com")
		self.assertEqual(payload["sequences"], [99])
		self.assertEqual(payload["attribs"]["user"]["bio"], "User Bio Content")
		self.assertEqual(payload["attribs"]["context"]["content"], "Context Content")

		mcc_mock.db_set.assert_any_call("status", "Scheduled")

	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.modify_contact_sequences")
	@patch("frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.ensure_listmonk_authorized")
	def test_remove_contact_from_sequence(self, mock_ensure_auth, mock_modify_seq) -> None:
		remove_contact_from_sequence("MCC-001", listmonk_contact_id=10, listmonk_sequence_id=20)
		mock_ensure_auth.assert_called_once()
		mock_modify_seq.assert_called_once_with(action="remove", contact_ids=[10], sequence_ids=[20])
