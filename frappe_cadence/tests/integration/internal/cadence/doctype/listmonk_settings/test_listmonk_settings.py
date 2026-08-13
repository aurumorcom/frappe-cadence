from unittest.mock import MagicMock, patch
import frappe
from frappe.tests.utils import FrappeTestCase


class TestListmonkSettingsIntegration(FrappeTestCase):
	def setUp(self) -> None:
		self.settings = frappe.get_doc("Listmonk Settings")
		self.settings.enabled = 1
		self.settings.base_url = "http://localhost:9000"
		self.settings.access_token = "test_token"
		self.settings.webhook_secret = "test_secret"

	@patch("requests.get")
	def test_settings_save_updates_status_authorized(self, mock_get) -> None:
		res_mock = MagicMock()
		res_mock.status_code = 200
		mock_get.return_value = res_mock

		self.settings.save()
		self.assertEqual(self.settings.status, "Authorized")

	@patch("requests.get")
	def test_settings_save_updates_status_unauthorized_on_failure(self, mock_get) -> None:
		res_mock = MagicMock()
		res_mock.status_code = 401
		mock_get.return_value = res_mock

		self.settings.save()
		self.assertEqual(self.settings.status, "Unauthorized")
