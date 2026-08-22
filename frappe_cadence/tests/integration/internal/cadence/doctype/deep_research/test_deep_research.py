import frappe
from frappe.tests.utils import FrappeTestCase


class TestDeepResearchIntegration(FrappeTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		if not frappe.db.exists("DocType", "Deep Research"):
			frappe.reload_doc("Cadence", "doctype", "deep_research_history")
			frappe.reload_doc("Cadence", "doctype", "deep_research")

	def test_deep_research_creation_and_history_tracking(self) -> None:
		ctx = frappe.get_doc(
			{
				"doctype": "Deep Research",
				"content": "Initial Deep Research Text",
			}
		).insert(ignore_permissions=True, ignore_links=True)

		self.assertEqual(ctx.content, "Initial Deep Research Text")

		ctx.content = "Updated Deep Research Text"
		ctx.save(ignore_permissions=True)

		ctx.reload()
		self.assertEqual(len(ctx.history), 1)
		self.assertEqual(ctx.history[0].content_snapshot, "Initial Deep Research Text")
