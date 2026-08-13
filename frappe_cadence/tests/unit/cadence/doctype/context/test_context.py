from unittest.mock import MagicMock, patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.context.context import Context


class TestContextUnit(FrappeTestCase):
	@patch("frappe.session", frappe._dict({"user": "test@example.com"}))
	def test_context_before_save_populates_history_table(self) -> None:
		ctx = Context.__new__(Context)
		ctx.history = []
		ctx.append = lambda table, row: ctx.history.append(frappe._dict(row))
		ctx.is_new = MagicMock(return_value=False)
		ctx.has_value_changed = MagicMock(return_value=True)

		old_doc = MagicMock()
		old_doc.content = "Original Content"
		ctx.get_doc_before_save = MagicMock(return_value=old_doc)

		ctx.before_save()

		self.assertEqual(len(ctx.history), 1)
		self.assertEqual(ctx.history[0].content_snapshot, "Original Content")
		self.assertEqual(ctx.history[0].user, "test@example.com")
