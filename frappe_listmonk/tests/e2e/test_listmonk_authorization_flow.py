from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_listmonk.client import ensure_listmonk_authorized


class TestListmonkAuthorizationE2E(FrappeTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.db.sql(
			"UPDATE `tabDocType` SET module='Listmonk' WHERE name IN ('Listmonk Settings', 'Deep Research', 'Deep Research Rule', 'List', 'CRM Lead List', 'CRM Organization List')"
		)
		frappe.db.commit()
		frappe.clear_cache()

	@patch("frappe.wait_for")
	def test_unauthorized_settings_defers_and_authorization_resumes(self, mock_wait_for) -> None:
		settings = frappe.get_doc("Listmonk Settings")
		settings.enabled = 0
		settings.status = "Disabled"
		settings.save()

		ensure_listmonk_authorized()
		mock_wait_for.assert_called_once_with(
			event_key="Listmonk Settings:on_update:Listmonk Settings",
			condition="argument.get('enabled') == 1 and argument.get('status') == 'Authorized'",
		)

		mock_wait_for.reset_mock()
		with patch("requests.get") as mock_get:
			res_mock = MagicMock()
			res_mock.status_code = 200
			mock_get.return_value = res_mock

			settings.enabled = 1
			settings.base_url = "http://localhost:9000"
			settings.access_token = "token"
			settings.webhook_secret = "secret"
			settings.save()

			self.assertEqual(settings.status, "Authorized")

		ensure_listmonk_authorized()
		mock_wait_for.assert_not_called()
