import frappe
from frappe.tests.utils import FrappeTestCase


class TestDeepResearchSource(FrappeTestCase):
	"""Unit tests for the Deep Research Source child table DocType."""

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		if hasattr(frappe, "db") and frappe.db:
			try:
				frappe.reload_doc("listmonk", "doctype", "deep_research_source", force=True)
			except Exception:
				pass
			frappe.db.sql(
				"UPDATE `tabDocType` SET module='Listmonk' WHERE name IN ('Source', 'Deep Research Source', 'Deep Research')"
			)
			frappe.db.commit()
			frappe.clear_cache()

	def test_deep_research_source_child_row(self) -> None:
		child_row = frappe.get_doc(
			{
				"doctype": "Deep Research Source",
				"source": "SRC-00001",
				"reference_doctype": "CRM Lead",
				"reference_name": "LEAD-00001",
				"url": "https://example.com/source-link",
			}
		)
		self.assertEqual(child_row.doctype, "Deep Research Source")
		self.assertEqual(child_row.source, "SRC-00001")
		self.assertEqual(child_row.reference_doctype, "CRM Lead")
		self.assertEqual(child_row.reference_name, "LEAD-00001")
		self.assertEqual(child_row.url, "https://example.com/source-link")
