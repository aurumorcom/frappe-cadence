import unittest
from unittest.mock import MagicMock, patch

import frappe

from frappe_cadence.integrations.listmonk import ensure_user_listmonk_id_provisioned
from frappe_cadence.integrations.listmonk.jobs.user import get_users


class TestUserJobUnit(unittest.TestCase):
	@patch("frappe_cadence.integrations.listmonk.jobs.user.ListmonkClient")
	@patch("frappe_cadence.integrations.listmonk.jobs.user.ensure_listmonk_authorized")
	@patch("frappe.db.set_value")
	@patch("frappe.get_all")
	def test_get_users_matches_existing_user(
		self,
		mock_get_all: MagicMock,
		mock_set_value: MagicMock,
		mock_auth: MagicMock,
		mock_client_cls: MagicMock,
	) -> None:
		mock_get_all.return_value = [
			{"name": "sales1@test.local", "email": "sales1@test.local", "listmonk_id": None}
		]
		client_inst = MagicMock()
		client_inst.get_listmonk_users.return_value = [
			{"id": 105, "email": "sales1@test.local", "username": "sales1"}
		]
		mock_client_cls.return_value = client_inst

		res = get_users()
		self.assertEqual(res["status"], "success")
		self.assertEqual(res["updated"], 1)
		mock_set_value.assert_called_once_with("User", "sales1@test.local", "listmonk_id", 105)

	@patch("frappe_cadence.integrations.listmonk.jobs.user.ListmonkClient")
	@patch("frappe_cadence.integrations.listmonk.jobs.user.ensure_listmonk_authorized")
	@patch("frappe.db.set_value")
	@patch("frappe.get_all")
	def test_get_users_skips_unmatched_user(
		self,
		mock_get_all: MagicMock,
		mock_set_value: MagicMock,
		mock_auth: MagicMock,
		mock_client_cls: MagicMock,
	) -> None:
		mock_get_all.return_value = [
			{"name": "sales2@test.local", "email": "sales2@test.local", "listmonk_id": None}
		]
		client_inst = MagicMock()
		client_inst.get_listmonk_users.return_value = []
		mock_client_cls.return_value = client_inst

		res = get_users()
		self.assertEqual(res["status"], "success")
		self.assertEqual(res["updated"], 0)
		mock_set_value.assert_not_called()

	@patch("frappe.get_doc")
	@patch("frappe.db.exists")
	def test_ensure_user_listmonk_id_provisioned_returns_id(
		self,
		mock_exists: MagicMock,
		mock_get_doc: MagicMock,
	) -> None:
		mock_exists.return_value = True
		user_mock = MagicMock()
		user_mock.get.return_value = 88
		mock_get_doc.return_value = user_mock

		res = ensure_user_listmonk_id_provisioned("sales1@test.local")
		self.assertEqual(res, 88)

	@patch("frappe.wait_for")
	@patch("frappe.get_doc")
	@patch("frappe.db.exists")
	def test_ensure_user_listmonk_id_provisioned_defers_when_missing(
		self,
		mock_exists: MagicMock,
		mock_get_doc: MagicMock,
		mock_wait_for: MagicMock,
	) -> None:
		mock_exists.return_value = True
		user_mock = MagicMock()
		user_mock.get.side_effect = [None, 99]
		mock_get_doc.return_value = user_mock

		frappe.flags.current_job_id = "job_test_123"
		try:
			res = ensure_user_listmonk_id_provisioned("sales1@test.local")
		finally:
			frappe.flags.current_job_id = None

		mock_wait_for.assert_called_once_with(
			event_key="User:on_update:sales1@test.local",
			condition="argument.get('listmonk_id') is not None and argument.get('listmonk_id') > 0",
		)
		self.assertEqual(res, 99)
