import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_cadence.listmonk import webhook


class TestWebhookEndpointUnit(FrappeTestCase):
	def setUp(self) -> None:
		req = MagicMock()
		req.get_data.return_value = b""
		frappe.local.request = req
		frappe.local.form_dict = frappe._dict()

	@patch("frappe.get_doc")
	@patch("frappe_cadence.listmonk.frappe.get_request_header")
	def test_webhook_invalid_signature_throws_error(self, mock_header, mock_get_doc) -> None:
		settings_mock = MagicMock()
		settings_mock.get_password.return_value = "my_secret"
		mock_get_doc.return_value = settings_mock

		mock_header.return_value = "invalid_signature"
		frappe.local.request.get_data.return_value = b'{"event": "contact.created"}'

		with self.assertRaises(frappe.PermissionError):
			webhook()

	@patch("frappe.get_doc")
	@patch("frappe.get_all")
	@patch("frappe_cadence.listmonk.frappe.get_request_header")
	def test_webhook_valid_signature_updates_mcc(self, mock_header, mock_get_all, mock_get_doc) -> None:
		secret = frappe.conf.get("listmonk_webhook_secret") or "whsec_123"
		body_bytes = json.dumps(
			{
				"event": "sequence.step_executed",
				"data": {"subscriber_id": 10, "sequence_id": 20, "subject": "Hi", "body": "Hello"},
			}
		).encode("utf-8")
		sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

		mock_header.return_value = sig
		frappe.local.request.get_data.return_value = body_bytes

		mock_get_all.return_value = [{"name": "MCC-001"}]

		settings_mock = MagicMock()
		settings_mock.get_password.return_value = secret

		mcc_doc = MagicMock()
		mcc_doc.status = "Scheduled"
		mcc_doc.name = "MCC-001"
		mcc_doc.recipient = "test@example.com"

		comm_doc = MagicMock()

		def side_effect(dt, *args, **kwargs):
			if dt == "Listmonk Settings":
				return settings_mock
			if dt == "Multi Channel Cadence":
				return mcc_doc
			return comm_doc

		mock_get_doc.side_effect = side_effect

		res = webhook()

		self.assertEqual(res["status"], "ok")
		mcc_doc.db_set.assert_called_with("status", "In Progress")
