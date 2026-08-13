from unittest.mock import MagicMock, patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.cadence.cadence import (
	add_lead_batch_to_cadence,
	delete_sequence,
	evaluate_leads_for_cadence,
	upsert_sequence,
)


class TestCadenceUnit(FrappeTestCase):
	@patch("frappe.enqueue")
	def test_cadence_on_update_enqueues_upsert_and_evaluation(self, mock_enqueue) -> None:
		from frappe_cadence.cadence.doctype.cadence.cadence import Cadence
		c = Cadence.__new__(Cadence)
		c.name = "CAD-001"
		c.ensure_playbook = MagicMock()

		c.on_update()

		self.assertEqual(mock_enqueue.call_count, 2)

	@patch("frappe_cadence.cadence.doctype.cadence.cadence.update_sequence_status")
	@patch("frappe_cadence.cadence.doctype.cadence.cadence.create_sequence")
	@patch("frappe_cadence.cadence.doctype.cadence.cadence.ensure_listmonk_authorized")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_upsert_sequence_new(self, mock_exists, mock_get_doc, mock_ensure_auth, mock_create_seq, mock_update_status) -> None:
		cad_mock = MagicMock()
		cad_mock.get.return_value = None
		cad_mock.cadence_name = "My Sequence"
		cad_mock.description = "Desc"
		cad_mock.enabled = 1
		mock_get_doc.return_value = cad_mock
		mock_create_seq.return_value = {"id": 88}

		upsert_sequence("CAD-001")

		mock_ensure_auth.assert_called_once()
		mock_create_seq.assert_called_once_with({"name": "My Sequence", "description": "Desc"})
		cad_mock.db_set.assert_called_once_with("listmonk_id", 88)
		mock_update_status.assert_called_once_with(88, "active")

	@patch("frappe_cadence.cadence.doctype.cadence.cadence.api_delete_sequence")
	@patch("frappe_cadence.cadence.doctype.cadence.cadence.ensure_listmonk_authorized")
	def test_delete_sequence(self, mock_ensure_auth, mock_api_delete) -> None:
		delete_sequence(88)
		mock_ensure_auth.assert_called_once()
		mock_api_delete.assert_called_once_with(88)

	@patch("frappe.enqueue")
	@patch("frappe.get_all")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_evaluate_leads_for_cadence_chunks_leads(self, mock_exists, mock_get_doc, mock_get_all, mock_enqueue) -> None:
		cad_mock = MagicMock()
		cad_mock.assign_condition_json = '[["status", "=", "Open"]]'
		cad_mock.enabled = 1
		mock_get_doc.return_value = cad_mock

		# Mock 250 leads -> should chunk into 3 batches (100, 100, 50)
		mock_get_all.side_effect = [
			[],  # enrolled_leads
			[f"LEAD-{i:03d}" for i in range(250)],  # matching_leads
		]

		evaluate_leads_for_cadence("CAD-001")

		self.assertEqual(mock_enqueue.call_count, 3)

	@patch("frappe.get_doc")
	@patch("frappe.db.exists", side_effect=[True, False])
	@patch("frappe_cadence.cadence.doctype.cadence.cadence.determine_sender", return_value="Administrator")
	def test_add_lead_batch_to_cadence(self, mock_sender, mock_exists, mock_get_doc) -> None:
		cad_mock = MagicMock()
		cad_mock.name = "CAD-001"

		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-00001"

		with patch("frappe.get_doc", side_effect=[cad_mock, MagicMock(insert=MagicMock(return_value=mcc_mock))]):
			res = add_lead_batch_to_cadence("CAD-001", ["LEAD-001"])
			self.assertIn("MCC-00001", res)
