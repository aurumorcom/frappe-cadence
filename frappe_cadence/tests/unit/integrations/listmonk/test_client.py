import unittest
from unittest.mock import MagicMock, patch

from frappe_cadence.integrations.listmonk.client import ListmonkClient
from frappe_cadence.integrations.listmonk.schemas.campaign import (
	CampaignCreateRequest,
	CampaignResponse,
	TransactionalEmailRequest,
)
from frappe_cadence.integrations.listmonk.schemas.list import (
	ListCreateRequest,
	ListResponse,
	ListUpdateRequest,
)
from frappe_cadence.integrations.listmonk.schemas.subscriber import (
	SubscriberCreateRequest,
	SubscriberListModifyRequest,
	SubscriberResponse,
	SubscriberUpdateRequest,
)
from frappe_cadence.integrations.listmonk.schemas.webhook import (
	WebhookCreateRequest,
	WebhookResponse,
	WebhookUpdateRequest,
)


class TestListmonkClient(unittest.TestCase):
	def setUp(self) -> None:
		self.client = ListmonkClient(
			base_url="https://listmonk.test.local",
			username="crm",
			token="test_token_123",
		)

	def test_get_headers(self) -> None:
		headers = self.client._get_headers()
		self.assertEqual(headers["Authorization"], "token crm:test_token_123")
		self.assertEqual(headers["Content-Type"], "application/json")

	def test_get_headers_already_formatted(self) -> None:
		client = ListmonkClient(
			base_url="https://listmonk.test.local",
			token="token crm:test_token_123",
		)
		headers = client._get_headers()
		self.assertEqual(headers["Authorization"], "token crm:test_token_123")

	@patch("requests.request")
	def test_create_subscriber(self, mock_req: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.content = b'{"data": {"id": 101, "email": "test@example.com", "name": "John Doe", "status": "enabled", "lists": [], "attribs": {}}}'
		mock_resp.json.return_value = {
			"data": {
				"id": 101,
				"email": "test@example.com",
				"name": "John Doe",
				"status": "enabled",
				"lists": [],
				"attribs": {},
			}
		}
		mock_req.return_value = mock_resp

		req = SubscriberCreateRequest(email="test@example.com", name="John Doe")
		res = self.client.create_subscriber(req)
		self.assertIsInstance(res, SubscriberResponse)
		self.assertEqual(res.id, 101)
		self.assertEqual(res.email, "test@example.com")

	@patch("requests.request")
	def test_update_subscriber(self, mock_req: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.content = b'{"data": {"id": 101, "email": "updated@example.com", "name": "John Doe", "status": "enabled", "lists": [], "attribs": {}}}'
		mock_resp.json.return_value = {
			"data": {
				"id": 101,
				"email": "updated@example.com",
				"name": "John Doe",
				"status": "enabled",
				"lists": [],
				"attribs": {},
			}
		}
		mock_req.return_value = mock_resp

		req = SubscriberUpdateRequest(email="updated@example.com")
		res = self.client.update_subscriber(101, req)
		self.assertEqual(res.email, "updated@example.com")

	@patch("requests.request")
	def test_delete_subscriber(self, mock_req: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.content = b'{"data": true}'
		mock_resp.json.return_value = {"data": True}
		mock_req.return_value = mock_resp

		success = self.client.delete_subscriber(101)
		self.assertTrue(success)

	@patch("requests.request")
	def test_create_list(self, mock_req: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.content = (
			b'{"data": {"id": 5, "name": "Outreach List", "type": "public", "optin": "single"}}'
		)
		mock_resp.json.return_value = {
			"data": {
				"id": 5,
				"name": "Outreach List",
				"type": "public",
				"optin": "single",
			}
		}
		mock_req.return_value = mock_resp

		req = ListCreateRequest(name="Outreach List")
		res = self.client.create_list(req)
		self.assertIsInstance(res, ListResponse)
		self.assertEqual(res.id, 5)

	@patch("requests.request")
	def test_create_webhook(self, mock_req: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.content = b'{"data": {"id": 1, "name": "Cadence WH", "url": "https://site/api/wh", "events": ["campaign.sent"], "enabled": true}}'
		mock_resp.json.return_value = {
			"data": {
				"id": 1,
				"name": "Cadence WH",
				"url": "https://site/api/wh",
				"events": ["campaign.sent"],
				"enabled": True,
			}
		}
		mock_req.return_value = mock_resp

		req = WebhookCreateRequest(name="Cadence WH", url="https://site/api/wh")
		res = self.client.create_webhook(req)
		self.assertIsInstance(res, WebhookResponse)
		self.assertEqual(res.id, 1)

	@patch("requests.request")
	def test_send_transactional_email(self, mock_req: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.content = b'{"data": true}'
		mock_resp.json.return_value = {"data": True}
		mock_req.return_value = mock_resp

		req = TransactionalEmailRequest(subscriber_email="target@example.com", template_id=1)
		res = self.client.send_transactional_email(req)
		self.assertTrue(res)

	@patch("requests.request")
	def test_update_campaign_status_normalizes_active(self, mock_req: MagicMock) -> None:
		mock_resp = MagicMock()
		mock_resp.content = b'{"data": {"id": 5, "status": "running"}}'
		mock_resp.json.return_value = {"data": {"id": 5, "status": "running"}}
		mock_req.return_value = mock_resp

		res = self.client.update_campaign_status(5, "active")
		self.assertEqual(res, {"id": 5, "status": "running"})
		mock_req.assert_called_once_with(
			method="PUT",
			url="https://listmonk.test.local/api/campaigns/5/status",
			json={"status": "running"},
			params=None,
			headers={
				"Authorization": "token crm:test_token_123",
				"Content-Type": "application/json",
			},
			timeout=30,
		)
