import frappe
from frappe.tests.utils import FrappeTestCase


class TestDeepResearch(FrappeTestCase):
	"""Unit tests for the Deep Research DocType."""

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		if hasattr(frappe, "db") and frappe.db:
			frappe.db.sql(
				"UPDATE `tabDocType` SET module='Listmonk' WHERE name IN ('Source', 'Deep Research Source', 'Deep Research')"
			)
			frappe.db.commit()
			frappe.clear_cache()

	def test_deep_research_summary_and_sources(self) -> None:
		doc = frappe.get_doc(
			{
				"doctype": "Deep Research",
				"reference_doctype": "CRM Lead",
				"reference_doc": "LEAD-00001",
				"rule": "CTO Research Rule",
				"summary": "AI summary of lead background.",
				"sources": [
					{
						"reference_doctype": "CRM Lead",
						"reference_name": "LEAD-00001",
						"url": "https://example.com/source1",
					}
				],
			}
		)
		self.assertEqual(doc.doctype, "Deep Research")
		self.assertEqual(doc.summary, "AI summary of lead background.")
		self.assertEqual(len(doc.sources), 1)
		source_row = doc.sources[0]
		url_val = getattr(source_row, "url", None) or (source_row.get("url") if isinstance(source_row, dict) else None)
		self.assertEqual(url_val, "https://example.com/source1")
