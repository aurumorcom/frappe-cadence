from unittest.mock import MagicMock, patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.playbook_execution.playbook_execution import on_update


class TestPlaybookExecutionUnit(FrappeTestCase):
	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_playbook_execution_on_update_running_updates_mcc_enriching(self, mock_exists, mock_get_doc) -> None:
		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-001"
		mock_get_doc.return_value = mcc_mock

		pe = frappe._dict({
			"multi_channel_cadence": "MCC-001",
			"status": "Running",
		})
		on_update(pe)

		mcc_mock.db_set.assert_called_once_with("status", "Enriching")

	@patch("frappe.enqueue")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_playbook_execution_on_update_completed_updates_mcc_provisioning_and_enqueues_enrollment(self, mock_exists, mock_get_doc, mock_enqueue) -> None:
		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-001"
		mock_get_doc.return_value = mcc_mock

		pe = frappe._dict({
			"multi_channel_cadence": "MCC-001",
			"status": "Completed",
		})
		on_update(pe)

		mcc_mock.db_set.assert_called_once_with("status", "Provisioning")
		mock_enqueue.assert_called_once_with(
			"frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence.add_contact_to_sequence",
			queue="high",
			mcc_name="MCC-001",
		)

	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_playbook_execution_on_update_failed_updates_mcc_failed(self, mock_exists, mock_get_doc) -> None:
		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-001"
		mock_get_doc.return_value = mcc_mock

		pe = frappe._dict({
			"multi_channel_cadence": "MCC-001",
			"status": "Failed",
		})
		on_update(pe)

		mcc_mock.db_set.assert_called_once_with("status", "Failed")
