import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.jobs.multi_channel_cadence import (
	add_subscriber_to_sequence,
	remove_subscriber_from_sequence,
	stop_mcc,
)


class TestMultiChannelCadenceJobs(unittest.TestCase):
	@patch("frappe_cadence.jobs.multi_channel_cadence.ensure_listmonk_authorized")
	@patch("frappe_cadence.jobs.multi_channel_cadence.resolve_user_bio")
	@patch("frappe_cadence.jobs.multi_channel_cadence.ListmonkClient")
	@patch("frappe.db.exists")
	@patch("frappe.get_doc")
	def test_add_subscriber_to_sequence(
		self,
		mock_get_doc: MagicMock,
		mock_exists: MagicMock,
		mock_client_cls: MagicMock,
		mock_bio: MagicMock,
		mock_auth: MagicMock,
	) -> None:
		mock_exists.return_value = True
		mock_bio.return_value = "Sales Bio"

		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-001"
		mcc_mock.recipient = "LEAD-001"
		mcc_mock.cadence_name = "CAD-001"
		mcc_mock.sender = "sales@test.local"

		lead_mock = MagicMock()
		lead_mock.name = "LEAD-001"
		lead_mock.listmonk_id = 10
		lead_mock.get.side_effect = lambda k: {"email_id": "lead@test.local", "lead_name": "Lead One"}.get(k)

		cadence_mock = MagicMock()
		cadence_mock.name = "CAD-001"
		cadence_mock.listmonk_id = 5

		def get_doc_side_effect(dt, name=None):
			if dt == "Multi Channel Cadence":
				return mcc_mock
			if dt == "CRM Lead":
				return lead_mock
			if dt == "Cadence":
				return cadence_mock
			return MagicMock()

		mock_get_doc.side_effect = get_doc_side_effect
		client_inst = MagicMock()
		mock_client_cls.return_value = client_inst

		add_subscriber_to_sequence("MCC-001")
		client_inst.update_subscriber.assert_called_once()
		mcc_mock.db_set.assert_any_call("status", "Scheduled")

	@patch("frappe_cadence.jobs.multi_channel_cadence.ensure_listmonk_authorized")
	@patch("frappe_cadence.jobs.multi_channel_cadence.ListmonkClient")
	def test_remove_subscriber_from_sequence(self, mock_client_cls: MagicMock, mock_auth: MagicMock) -> None:
		client_inst = MagicMock()
		mock_client_cls.return_value = client_inst

		remove_subscriber_from_sequence("MCC-001", listmonk_subscriber_id=10, listmonk_sequence_id=5)
		client_inst.modify_subscriber_lists.assert_called_once()

	@patch("frappe.get_doc")
	@patch("frappe.db.exists")
	def test_stop_mcc(
		self,
		mock_exists: MagicMock,
		mock_get_doc: MagicMock,
	) -> None:
		mock_exists.return_value = True
		mcc_mock = MagicMock()
		mock_get_doc.return_value = mcc_mock

		stop_mcc("MCC-001", reason="Replied")
		mcc_mock.db_set.assert_called_once_with("status", "Replied")
