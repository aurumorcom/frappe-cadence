from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestListJobExternal(FrappeTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.db.sql(
			"UPDATE `tabDocType` SET module='Listmonk' WHERE name IN ('Listmonk Settings', 'Deep Research', 'Deep Research Rule', 'List', 'CRM Lead List', 'CRM Organization List')"
		)
		frappe.db.commit()
		frappe.clear_cache()

	def setUp(self) -> None:
		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 1
		settings.status = "Authorized"
		settings.base_url = "http://localhost:9000"
		settings.access_token = "test_token"
		settings.save(ignore_permissions=True)
		frappe.db.set_single_value("Listmonk Settings", "status", "Authorized")

	@patch("frappe_listmonk.client.ListmonkClient.create_list")
	def test_polymorphic_list_creation(self, mock_create_list) -> None:
		from frappe_listmonk.jobs.list import upsert_list

		mock_create_list.return_value = frappe._dict({"id": 10})

		if frappe.db.exists("List", "External Test List"):
			frappe.delete_doc("List", "External Test List", force=True)

		doc = frappe.get_doc(
			{
				"doctype": "List",
				"list_name": "External Test List",
				"reference_doctype": "CRM Lead",
				"enabled": 1,
			}
		).insert()

		upsert_list(doc.name)

		mock_create_list.assert_called_once()
		args = mock_create_list.call_args[0][0]
		self.assertEqual(args["crm_id"], doc.name)
		self.assertEqual(args["type"], "private")
		self.assertEqual(args["optin"], "single")

		doc.reload()
		self.assertEqual(doc.listmonk_id, 10)

		frappe.delete_doc("List", doc.name, force=True)
