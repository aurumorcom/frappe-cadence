from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_listmonk.jobs.user import sync_all_crm_users, update_user


class TestUserJobUnit(FrappeTestCase):
	@patch("frappe_listmonk.jobs.user.ensure_listmonk_authorized")
	@patch("frappe_listmonk.client.ListmonkClient.get_listmonk_users")
	def test_sync_all_crm_users_updates_listmonk_id(self, mock_get_users, mock_auth) -> None:
		test_email = "test_user_listmonk_sync@example.com"
		if not frappe.db.exists("User", test_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": test_email,
					"first_name": "SyncTest",
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", test_email)

		mock_get_users.return_value = [{"id": 55, "email": test_email}]

		sync_all_crm_users()

		lm_id = frappe.db.get_value("User", user.name, "listmonk_id")
		self.assertEqual(lm_id, 55)

		frappe.delete_doc("User", user.name, force=True)

	@patch("frappe_listmonk.jobs.user.ensure_listmonk_authorized")
	@patch("frappe_listmonk.client.ListmonkClient.get_listmonk_users")
	def test_update_user_sets_listmonk_id(self, mock_get_users, mock_auth) -> None:
		test_email = "single_user_listmonk@example.com"
		if not frappe.db.exists("User", test_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": test_email,
					"first_name": "SingleTest",
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", test_email)

		mock_get_users.return_value = [{"id": 88, "email": test_email}]

		update_user(user.name)

		user.reload()
		self.assertEqual(user.listmonk_id, 88)

		frappe.delete_doc("User", user.name, force=True)
