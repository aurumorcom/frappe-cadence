import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.integrations.listmonk.jobs.webhook import (
	process_webhook_payload,
	setup_webhook,
)
from frappe_cadence.integrations.listmonk.schemas.webhook import WebhookResponse


class TestListmonkWebhookJobs(unittest.TestCase):
	@patch("frappe_cadence.integrations.listmonk.jobs.webhook.ensure_listmonk_authorized")
	@patch("frappe_cadence.integrations.listmonk.jobs.webhook.ListmonkClient")
	@patch("frappe.get_doc")
	@patch("frappe.utils.get_url")
	def test_setup_webhook_create_new(
		self,
		mock_get_url: MagicMock,
		mock_get_doc: MagicMock,
		mock_client_cls: MagicMock,
		mock_auth: MagicMock,
	) -> None:
		mock_get_url.return_value = "https://erp.test.local"
		settings_mock = MagicMock()
		settings_mock.get_password.return_value = "secret_123"
		mock_get_doc.return_value = settings_mock

		client_inst = MagicMock()
		client_inst.get_webhook_secret.return_value = "secret_123"
		client_inst.get_webhooks.return_value = []
		client_inst.create_webhook.return_value = WebhookResponse(
			id=1,
			name="Frappe Cadence Webhook",
			url="https://erp.test.local/api/method/frappe_cadence.integrations.listmonk.jobs.webhook.webhook",
		)
		mock_client_cls.return_value = client_inst

		setup_webhook()
		client_inst.create_webhook.assert_called_once()

	@patch("frappe.get_all")
	@patch("frappe.get_doc")
	def test_process_webhook_payload(
		self,
		mock_get_doc: MagicMock,
		mock_get_all: MagicMock,
	) -> None:
		mock_get_all.return_value = [{"name": "MCC-001", "status": "Scheduled"}]
		mcc_mock = MagicMock()
		mcc_mock.name = "MCC-001"
		mcc_mock.status = "Scheduled"
		mcc_mock.recipient = "LEAD-001"

		comm_mock = MagicMock()
		mock_get_doc.side_effect = lambda *args, **kwargs: (
			mcc_mock if args and args[0] == "Multi Channel Cadence" else comm_mock
		)

		payload = {
			"event": "campaign.step_executed",
			"data": {
				"subscriber_id": 10,
				"campaign_id": 2,
				"status": "step_executed",
				"email": "recipient@test.local",
			},
		}

		res = process_webhook_payload(payload)
		self.assertEqual(res["status"], "ok")
		mcc_mock.db_set.assert_called_with("status", "In Progress")
