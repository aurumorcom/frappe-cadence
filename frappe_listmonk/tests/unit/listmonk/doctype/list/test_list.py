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
				"filter_condition": "doc.status == 'Qualified'",
			}
		).insert()

		self.assertEqual(doc.name, "Test Target List")
		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertIn("doc.status == 'Qualified'", doc.filter_condition_json)

		frappe.delete_doc("List", doc.name, force=True)

	def test_invalid_ast_condition_raises_validation_error(self) -> None:
		if frappe.db.exists("List", "Invalid AST List"):
			frappe.delete_doc("List", "Invalid AST List", force=True)

		doc = frappe.get_doc(
			{
				"doctype": "List",
				"list_name": "Invalid AST List",
				"reference_doctype": "CRM Lead",
				"enabled": 1,
				"filter_condition": "doc.status ==",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()
