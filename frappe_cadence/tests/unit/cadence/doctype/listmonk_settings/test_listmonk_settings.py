from unittest.mock import MagicMock, patch
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe_cadence.cadence.doctype.listmonk_settings.listmonk_settings import (
	ListmonkSettings,
	setup_webhook,
	sync_all_crm_leads,
)


class TestListmonkSettingsUnit(FrappeTestCase):
	def test_listmonk_settings_validate_strips_trailing_slash(self) -> None:
		settings = ListmonkSettings.__new__(ListmonkSettings)
		settings.base_url = "http://localhost:9000///"
		settings.validate()
		self.assertEqual(settings.base_url, "http://localhost:9000")

	@patch("frappe.enqueue")
	@patch("frappe.publish_event")
	@patch("requests.get")
	def test_listmonk_settings_on_update_authorized(self, mock_requests_get, mock_publish, mock_enqueue) -> None:
		settings = ListmonkSettings.__new__(ListmonkSettings)
		settings.enabled = 1
		settings.base_url = "http://localhost:9000"
		settings.get_password = MagicMock(return_value="test_token")
		settings.db_set = MagicMock()

		res_mock = MagicMock()
		res_mock.status_code = 200
		mock_requests_get.return_value = res_mock

		settings.on_update()

		settings.db_set.assert_called_with("status", "Authorized")
		mock_publish.assert_called_once_with("listmonk_authorized", {"enabled": 1, "status": "Authorized"})
		mock_enqueue.assert_called_once_with(
			"frappe_cadence.cadence.doctype.listmonk_settings.listmonk_settings.setup_webhook",
			queue="high",
		)

	@patch("frappe_cadence.integrations.listmonk.create_webhook")
	@patch("frappe_cadence.integrations.listmonk.get_webhooks", return_value=[])
	@patch("frappe_cadence.integrations.listmonk.ensure_listmonk_authorized")
	@patch("frappe.get_doc")
	def test_setup_webhook_creates_new(self, mock_get_doc, mock_ensure_auth, mock_get_webhooks, mock_create_webhook) -> None:
		settings_mock = MagicMock()
		settings_mock.get_password.return_value = "wh_secret"
		mock_get_doc.return_value = settings_mock

		setup_webhook()

		mock_ensure_auth.assert_called_once()
		mock_create_webhook.assert_called_once()

	@patch("frappe.enqueue")
	@patch("frappe.get_all", return_value=[{"name": "LEAD-001"}, {"name": "LEAD-002"}])
	def test_sync_all_crm_leads(self, mock_get_all, mock_enqueue) -> None:
		sync_all_crm_leads()
		self.assertEqual(mock_enqueue.call_count, 2)
