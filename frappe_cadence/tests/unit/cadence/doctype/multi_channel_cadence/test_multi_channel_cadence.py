import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.cadence.doctype.multi_channel_cadence.multi_channel_cadence import (
	MultiChannelCadence,
	on_trash,
	on_update,
)


class TestMultiChannelCadenceUnit(unittest.TestCase):
	def test_before_insert_default_status(self) -> None:
		doc = MultiChannelCadence.__new__(MultiChannelCadence)
		doc.status = None
		doc.before_insert()
		self.assertEqual(doc.status, "Draft")

	@patch("frappe.enqueue")
	def test_on_trash_enqueues_remove(self, mock_enqueue: MagicMock) -> None:
		doc = MultiChannelCadence.__new__(MultiChannelCadence)
		doc.name = "MCC-001"
		doc.listmonk_contact_id = 10
		doc.listmonk_sequence_id = 5

		on_trash(doc)
		mock_enqueue.assert_called_once()
