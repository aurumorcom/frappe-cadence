from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_listmonk.jobs.list import delete_list, upsert_list


class TestListJobUnit(FrappeTestCase):
	@patch("frappe_listmonk.jobs.list.ensure_listmonk_authorized")
	@patch("frappe_listmonk.client.ListmonkClient.create_list")
	def test_upsert_list_hardcoded_payload(self, mock_create, mock_auth) -> None:
		mock_create.return_value = frappe._dict({"id": 101})

		list_name = "Unit Test Private List"
		if frappe.db.exists("List", list_name):
			frappe.delete_doc("List", list_name, force=True)

		doc = frappe.get_doc(
			{
				"doctype": "List",
				"list_name": list_name,
				"reference_doctype": "CRM Lead",
				"enabled": 1,
			}
		).insert()

		upsert_list(doc.name)

		mock_create.assert_called_once()
		payload = mock_create.call_args[0][0]
		self.assertEqual(payload["type"], "private")
		self.assertEqual(payload["optin"], "single")
		self.assertNotIn("tags", payload)

		doc.reload()
		self.assertEqual(doc.listmonk_id, 101)

		frappe.delete_doc("List", doc.name, force=True)

	@patch("frappe_listmonk.jobs.list.ensure_listmonk_authorized")
	@patch("frappe_listmonk.client.ListmonkClient.delete_list")
	def test_delete_list_invokes_client(self, mock_delete, mock_auth) -> None:
		delete_list("Some List", listmonk_id=202)
		mock_delete.assert_called_once_with(202)
