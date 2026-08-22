import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.integrations.listmonk.schemas.list import ListResponse
from frappe_cadence.jobs.cadence import (
	add_lead_batch_to_cadence,
	delete_campaign,
	determine_sender,
	evaluate_cadences_for_lead,
	evaluate_leads_for_cadence,
	update_campaign_status,
	upsert_campaign,
)


class TestCadenceJobs(unittest.TestCase):
	@patch("frappe_cadence.jobs.cadence.ensure_listmonk_authorized")
	@patch("frappe_cadence.jobs.cadence.ListmonkClient")
	@patch("frappe.db.exists")
	@patch("frappe.get_doc")
	def test_upsert_campaign(
		self,
		mock_get_doc: MagicMock,
		mock_exists: MagicMock,
		mock_client_cls: MagicMock,
		mock_auth: MagicMock,
	) -> None:
		mock_exists.return_value = True
		cadence_mock = MagicMock()
		cadence_mock.cadence_name = "Cadence 1"
		cadence_mock.name = "CAD-001"
		cadence_mock.enabled = 1
		cadence_mock.get.return_value = None
		mock_get_doc.return_value = cadence_mock

		client_inst = MagicMock()
		client_inst.create_list.return_value = ListResponse(
			id=20, name="Cadence 1", type="public", optin="single"
		)
		mock_client_cls.return_value = client_inst

		list_id = upsert_campaign("CAD-001")
		self.assertEqual(list_id, 20)
		cadence_mock.db_set.assert_called_once_with("listmonk_id", 20)
		client_inst.update_list_status.assert_called_once_with(20, "active")

	@patch("frappe_cadence.jobs.cadence.ensure_listmonk_authorized")
	@patch("frappe_cadence.jobs.cadence.ListmonkClient")
	def test_delete_campaign(self, mock_client_cls: MagicMock, mock_auth: MagicMock) -> None:
		client_inst = MagicMock()
		mock_client_cls.return_value = client_inst

		delete_campaign(20)
		client_inst.delete_list.assert_called_once_with(20)

	@patch("frappe_cadence.jobs.cadence.ensure_listmonk_authorized")
	@patch("frappe_cadence.jobs.cadence.ListmonkClient")
	def test_update_campaign_status(self, mock_client_cls: MagicMock, mock_auth: MagicMock) -> None:
		client_inst = MagicMock()
		mock_client_cls.return_value = client_inst

		update_campaign_status(20, "paused")
		client_inst.update_list_status.assert_called_once_with(20, "paused")

	@patch("frappe.enqueue")
	@patch("frappe.get_all")
	def test_evaluate_cadences_for_lead(self, mock_get_all: MagicMock, mock_enqueue: MagicMock) -> None:
		mock_get_all.return_value = [{"name": "CAD-01", "assign_condition_json": '[["status","=","Lead"]]'}]
		evaluate_cadences_for_lead("LEAD-001")
		mock_enqueue.assert_called_once()

	@patch("frappe.get_doc")
	@patch("frappe.db.exists")
	def test_add_lead_batch_to_cadence(
		self,
		mock_exists: MagicMock,
		mock_get_doc: MagicMock,
	) -> None:
		mock_exists.side_effect = lambda dt, name: True if dt == "Cadence" else False
		cadence_mock = MagicMock()
		cadence_mock.users = []
		cadence_mock.owner = "admin@example.com"
		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-001"
		mcc_mock.insert.return_value = mcc_mock
		mock_get_doc.side_effect = lambda *args, **kwargs: (
			cadence_mock if args and args[0] == "Cadence" else mcc_mock
		)

		res = add_lead_batch_to_cadence("CAD-001", ["LEAD-1"])
		self.assertEqual(res, ["MCC-001"])

	def test_determine_sender(self) -> None:
		cadence_mock = MagicMock()
		user_1 = MagicMock()
		user_1.user = "user1@example.com"
		user_2 = MagicMock()
		user_2.user = "user2@example.com"
		cadence_mock.users = [user_1, user_2]
		cadence_mock.rule = "Round Robin"
		cadence_mock.last_user = "user1@example.com"

		sender = determine_sender(cadence_mock)
		self.assertEqual(sender, "user2@example.com")
