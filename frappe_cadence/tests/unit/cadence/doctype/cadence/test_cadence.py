import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.cadence.doctype.cadence.cadence import (
	Cadence,
	on_trash,
	on_update,
)


class TestCadenceUnit(unittest.TestCase):
	def test_ast_to_filters_simple(self) -> None:
		doc = Cadence.__new__(Cadence)
		import ast

		tree = ast.parse("doc.status == 'Open'", mode="eval")
		filters = doc._ast_to_filters(tree.body)
		self.assertEqual(filters, [["status", "=", "Open"]])

	def test_ast_to_filters_and(self) -> None:
		doc = Cadence.__new__(Cadence)
		import ast

		tree = ast.parse("doc.status == 'Open' and doc.country == 'US'", mode="eval")
		filters = doc._ast_to_filters(tree.body)
		self.assertEqual(filters, [["status", "=", "Open"], ["country", "=", "US"]])

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
