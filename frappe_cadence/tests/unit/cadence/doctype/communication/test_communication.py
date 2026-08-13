from unittest.mock import MagicMock, patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.communication.communication import on_update


class TestCommunicationEvents(FrappeTestCase):
	def test_module_load(self):
		import frappe_cadence.cadence.doctype.communication.communication as comm_module
		self.assertIsNotNone(comm_module)

	def test_on_update_ignores_non_mcc_communication(self):
		comm = MagicMock()
		comm.reference_doctype = "Customer"
		comm.reference_name = "CUST-001"

		with patch("frappe.db.exists") as mock_exists:
			on_update(comm)
			mock_exists.assert_not_called()

	@patch("frappe.get_doc")
	@patch("frappe.db.exists", return_value=True)
	def test_on_update_updates_mcc_status_if_scheduled(self, mock_exists, mock_get_doc):
		comm = MagicMock()
		comm.reference_doctype = "Multi Channel Cadence"
		comm.reference_name = "MCC-001"

		mcc_mock = MagicMock()
		mcc_mock.status = "Scheduled"
		mock_get_doc.return_value = mcc_mock

		on_update(comm)

		mcc_mock.db_set.assert_called_once_with("status", "In Progress")
