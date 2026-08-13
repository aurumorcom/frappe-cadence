import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.cadence.doctype.crm_lead.crm_lead import on_trash, on_update


class TestCrmLeadUnit(unittest.TestCase):
	@patch("frappe.enqueue")
	def test_on_update_enqueues(self, mock_enqueue: MagicMock) -> None:
		doc = MagicMock()
		doc.name = "LEAD-001"

		on_update(doc)
		self.assertEqual(mock_enqueue.call_count, 2)

	@patch("frappe.enqueue")
	def test_on_trash_enqueues_delete(self, mock_enqueue: MagicMock) -> None:
		doc = MagicMock()
		doc.get.return_value = 101

		on_trash(doc)
		mock_enqueue.assert_called_once()
