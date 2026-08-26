import frappe
from frappe.tests.utils import FrappeTestCase


class TestSource(FrappeTestCase):
	"""Unit tests for the Source DocType."""

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		if hasattr(frappe, "db") and frappe.db:
			try:
				frappe.reload_doc("listmonk", "doctype", "source", force=True)
			except Exception:
				pass
			frappe.db.sql(
				"UPDATE `tabDocType` SET module='Listmonk' WHERE name IN ('Source', 'Deep Research Source', 'Deep Research')"
			)
			frappe.db.commit()
			frappe.clear_cache()

	def test_source_creation_and_attributes(self) -> None:
		source = frappe.get_doc(
			{
				"doctype": "Source",
				"reference_doctype": "CRM Lead",
				"reference_name": "LEAD-00001",
				"url": "https://example.com/company-profile",
			}
		)
		self.assertEqual(source.doctype, "Source")
		self.assertEqual(source.reference_doctype, "CRM Lead")
		self.assertEqual(source.reference_name, "LEAD-00001")
		self.assertEqual(source.url, "https://example.com/company-profile")
