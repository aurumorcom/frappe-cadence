import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.cadence.doctype.playbook_execution.playbook_execution import on_update


class TestPlaybookExecutionUnit(unittest.TestCase):
	@patch("frappe.enqueue")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists")
	def test_on_update_completed(
		self,
		mock_exists: MagicMock,
		mock_get_doc: MagicMock,
		mock_enqueue: MagicMock,
	) -> None:
		mock_exists.return_value = True
		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-001"
		mock_get_doc.return_value = mcc_mock

		doc = MagicMock()
		doc.get.side_effect = lambda k: "MCC-001" if k == "multi_channel_cadence" else None
		doc.status = "Completed"

		on_update(doc)
		mcc_mock.db_set.assert_called_once_with("status", "Provisioning")
		mock_enqueue.assert_called_once()
