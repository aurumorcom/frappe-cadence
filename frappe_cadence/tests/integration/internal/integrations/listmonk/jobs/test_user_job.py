from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.integrations.listmonk.jobs.user import get_users


class TestUserJobInternalIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.user_email = f"int_user_{frappe.generate_hash(length=6)}@example.com"
		self.test_user = frappe.get_doc(
			{
				"doctype": "User",
				"email": self.user_email,
				"first_name": "Integration",
				"last_name": "User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True, ignore_links=True)

	def tearDown(self) -> None:
		frappe.db.delete("User", {"email": self.user_email})

	@patch("frappe_cadence.integrations.listmonk.jobs.user.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.jobs.user.ListmonkClient")
	def test_get_users_updates_user_listmonk_id_in_db(
		self,
		mock_client_cls: MagicMock,
		mock_auth: MagicMock,
	) -> None:
		client_inst = MagicMock()
		client_inst.get_listmonk_users.return_value = [
			{"id": 404, "email": self.user_email, "username": "int_user"}
		]
		mock_client_cls.return_value = client_inst

		res = get_users()
		self.assertEqual(res["status"], "success")

		updated_id = frappe.db.get_value("User", self.test_user.name, "listmonk_id")
		self.assertEqual(int(updated_id), 404)
