import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.integrations.listmonk.jobs.subscriber import (
	delete_subscriber,
	sync_all_crm_leads,
	upsert_subscriber,
)
from frappe_cadence.integrations.listmonk.schemas.subscriber import SubscriberResponse


class TestListmonkSubscriberJobs(unittest.TestCase):
	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ListmonkClient")
	@patch("frappe.db.exists")
	@patch("frappe.get_doc")
	def test_upsert_subscriber_new(
		self,
		mock_get_doc: MagicMock,
		mock_exists: MagicMock,
		mock_client_cls: MagicMock,
		mock_auth: MagicMock,
	) -> None:
		mock_exists.return_value = True
		lead_mock = MagicMock()
		lead_mock.get.side_effect = lambda k: {
			"email_id": "test@lead.local",
			"lead_name": "Test Lead",
			"listmonk_id": None,
		}.get(k)
		lead_mock.name = "LEAD-001"
		lead_mock.as_dict.return_value = {"name": "LEAD-001"}
		mock_get_doc.return_value = lead_mock

		client_inst = MagicMock()
		client_inst.create_subscriber.return_value = SubscriberResponse(
			id=55,
			email="test@lead.local",
			name="Test Lead",
			status="enabled",
		)
		mock_client_cls.return_value = client_inst

		sub_id = upsert_subscriber("LEAD-001")
		self.assertEqual(sub_id, 55)
		lead_mock.db_set.assert_called_once_with("listmonk_id", 55)

	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.jobs.subscriber.ListmonkClient")
	def test_delete_subscriber(self, mock_client_cls: MagicMock, mock_auth: MagicMock) -> None:
		client_inst = MagicMock()
		mock_client_cls.return_value = client_inst

		delete_subscriber(123)
		client_inst.delete_subscriber.assert_called_once_with(123)

	@patch("frappe.enqueue")
	@patch("frappe.get_all")
	def test_sync_all_crm_leads(self, mock_get_all: MagicMock, mock_enqueue: MagicMock) -> None:
		mock_get_all.return_value = [{"name": "L-1"}, {"name": "L-2"}]
		sync_all_crm_leads()
		self.assertEqual(mock_enqueue.call_count, 2)
