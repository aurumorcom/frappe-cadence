import unittest

import frappe
from frappe.tests.utils import FrappeTestCase


class TestList(FrappeTestCase):
	def test_list_doc_creation(self) -> None:
		if frappe.db.exists("List", "Test Target List"):
			frappe.delete_doc("List", "Test Target List", force=True)

		doc = frappe.get_doc(
			{
				"doctype": "List",
				"list_name": "Test Target List",
				"reference_doctype": "CRM Lead",
				"enabled": 1,
				"type": "public",
				"optin": "single",
				"tags": "outreach, sales",
			}
		).insert()

		self.assertEqual(doc.name, "Test Target List")
		self.assertEqual(doc.reference_doctype, "CRM Lead")

		frappe.delete_doc("List", doc.name, force=True)
