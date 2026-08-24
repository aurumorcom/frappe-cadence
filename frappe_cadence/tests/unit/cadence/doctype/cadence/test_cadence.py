import ast
import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.cadence.doctype.cadence.cadence import (
	Cadence,
	on_trash,
	on_update,
	upsert_campaign,
)


class TestCadenceUnit(unittest.TestCase):
	def test_ast_to_filters_simple(self) -> None:
		doc = Cadence.__new__(Cadence)
		tree = ast.parse("doc.status == 'Open'", mode="eval")
		filters = doc._ast_to_filters(tree.body)
		self.assertEqual(filters, [["status", "=", "Open"]])

	def test_ast_to_filters_and(self) -> None:
		doc = Cadence.__new__(Cadence)
		tree = ast.parse("doc.status == 'Open' and doc.country == 'US'", mode="eval")
		filters = doc._ast_to_filters(tree.body)
		self.assertEqual(filters, [["status", "=", "Open"], ["country", "=", "US"]])

	@patch("frappe_cadence.cadence.doctype.cadence.cadence.update_campaign_status")
	@patch("frappe_cadence.cadence.doctype.cadence.cadence.create_campaign")
	def test_upsert_campaign_uses_running_status_when_enabled(
		self, mock_create: MagicMock, mock_update_status: MagicMock
	) -> None:
		doc = Cadence.__new__(Cadence)
		doc.name = "CAD-001"
		doc.cadence_name = "Outreach Cadence"
		doc.description = "Test Description"
		doc.enabled = 1
		doc.listmonk_id = None
		doc.get = MagicMock(return_value=None)
		doc.db_set = MagicMock()

		mock_create.return_value = {"id": 88}

		campaign_id = upsert_campaign(doc, list_id=10)
		self.assertEqual(campaign_id, 88)
		mock_create.assert_called_once_with(
			{
				"name": "Outreach Cadence",
				"description": "Test Description",
				"status": "running",
				"lists": [10],
				"type": "sequence",
			}
		)

	@patch("frappe.enqueue")
	def test_on_update_enqueues(self, mock_enqueue: MagicMock) -> None:
		doc = Cadence.__new__(Cadence)
		doc.name = "CAD-001"
		doc.ensure_playbook = MagicMock()

		on_update(doc)
		self.assertEqual(mock_enqueue.call_count, 2)

	@patch("frappe.enqueue")
	def test_on_trash_enqueues_delete(self, mock_enqueue: MagicMock) -> None:
		doc = Cadence.__new__(Cadence)
		doc.name = "CAD-001"
		doc.listmonk_id = 42

		on_trash(doc)
		mock_enqueue.assert_called_once()
