import frappe
from frappe.tests.utils import FrappeTestCase


class TestContextIntegration(FrappeTestCase):
	def test_context_creation_and_history_tracking(self) -> None:
		ctx = frappe.get_doc({
			"doctype": "Context",
			"content": "Initial Context Text",
		}).insert(ignore_permissions=True, ignore_links=True)

		self.assertEqual(ctx.content, "Initial Context Text")

		ctx.content = "Updated Context Text"
		ctx.save(ignore_permissions=True)

		ctx.reload()
		self.assertEqual(len(ctx.history), 1)
		self.assertEqual(ctx.history[0].content_snapshot, "Initial Context Text")
